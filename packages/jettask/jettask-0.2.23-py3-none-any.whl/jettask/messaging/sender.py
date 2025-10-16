"""
消息发送器 - 统一的消息发送接口
从 EventPool 中提取的消息发送逻辑
"""

import time
import logging
from typing import List, Dict, Optional, Tuple
from redis.asyncio import Redis as AsyncRedis

from ..utils.serializer import dumps_str

logger = logging.getLogger('app')


class MessageSender:
    """
    统一的消息发送接口

    职责：
    1. 发送普通消息到 Redis Stream
    2. 发送延迟消息到 Redis Sorted Set + Stream
    3. 发送优先级消息到优先级队列
    4. 批量发送优化
    """

    def __init__(
        self,
        async_redis_client: AsyncRedis,
        redis_prefix: str = 'jettask'
    ):
        """
        初始化消息发送器

        Args:
            async_redis_client: 异步Redis客户端（二进制模式，用于Stream操作）
            redis_prefix: Redis键前缀
        """
        self.redis = async_redis_client
        self.redis_prefix = redis_prefix

        # 缓存Lua脚本
        self._batch_send_script = None
        self._delayed_task_script = None

        logger.debug(f"MessageSender initialized with prefix: {redis_prefix}")

    def _get_prefixed_queue_name(self, queue: str) -> str:
        """获取带前缀的队列名"""
        return f"{self.redis_prefix}:QUEUE:{queue}"

    def _get_delayed_queue_name(self, queue: str) -> str:
        """获取延迟队列名（Sorted Set）"""
        return f"{self.redis_prefix}:DELAYED_QUEUE:{queue}"

    async def send_messages(
        self,
        queue: str,
        messages: List[Dict],
        priority: Optional[int] = None,
        delay: Optional[float] = None
    ) -> List[str]:
        """
        发送消息到队列（统一入口）

        Args:
            queue: 队列名（不带前缀）
            messages: 消息列表，每个消息是一个字典
            priority: 优先级（可选，如果指定则发送到优先级队列）
            delay: 延迟时间（秒，可选）

        Returns:
            List[str]: Stream ID 列表

        示例:
            # 发送普通消息
            ids = await sender.send_messages("orders", [{"order_id": 123}])

            # 发送延迟消息
            ids = await sender.send_messages("emails", [{"to": "user@example.com"}], delay=60)

            # 发送优先级消息
            ids = await sender.send_messages("tasks", [{"task": "urgent"}], priority=1)
        """
        if not messages:
            return []

        # 确定实际队列名（考虑优先级）
        actual_queue = queue
        if priority is not None:
            actual_queue = f"{queue}:{priority}"

        # 根据是否延迟选择发送方式
        if delay and delay > 0:
            return await self._send_delayed_messages(actual_queue, messages, delay)
        else:
            return await self._send_normal_messages(actual_queue, messages)

    async def _send_normal_messages(self, queue: str, messages: List[Dict]) -> List[str]:
        """
        发送普通消息到 Redis Stream
        使用 Lua 脚本实现批量发送 + 原子性offset分配

        Args:
            queue: 队列名（不带前缀）
            messages: 消息列表

        Returns:
            List[str]: Stream ID 列表
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        # Lua脚本：批量发送消息并添加自增offset
        lua_script = """
        local stream_key = KEYS[1]
        local prefix = ARGV[1]
        local results = {}

        -- 使用Hash存储所有队列的offset
        local offsets_hash = prefix .. ':QUEUE_OFFSETS'

        -- 从stream_key中提取队列名（去掉prefix:QUEUE:前缀）
        local queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

        -- 将队列添加到全局队列注册表
        local queues_registry_key = prefix .. ':REGISTRY:QUEUES'
        redis.call('SADD', queues_registry_key, queue_name)

        -- 从ARGV[2]开始，每个参数是一个消息的data
        for i = 2, #ARGV do
            local data = ARGV[i]

            -- 使用HINCRBY原子递增offset（如果不存在会自动创建并设为1）
            local current_offset = redis.call('HINCRBY', offsets_hash, queue_name, 1)

            -- 添加消息到Stream（包含offset字段）
            local stream_id = redis.call('XADD', stream_key, '*',
                'data', data,
                'offset', current_offset)

            table.insert(results, stream_id)
        end

        return results
        """

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            # 确保消息格式正确
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        # 注册并执行Lua脚本
        if not self._batch_send_script:
            self._batch_send_script = self.redis.register_script(lua_script)

        results = await self._batch_send_script(
            keys=[prefixed_queue],
            args=lua_args
        )

        # 解码所有返回的Stream ID
        decoded_results = [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]

        logger.debug(f"Sent {len(decoded_results)} messages to queue {queue}")
        return decoded_results

    async def _send_delayed_messages(
        self,
        queue: str,
        messages: List[Dict],
        delay: float
    ) -> List[str]:
        """
        发送延迟消息到 Stream + Sorted Set
        使用 Lua 脚本实现原子性操作

        Args:
            queue: 队列名（不带前缀）
            messages: 消息列表
            delay: 延迟时间（秒）

        Returns:
            List[str]: Stream ID 列表
        """
        # Lua脚本：原子性地发送延迟任务
        lua_script = """
        local prefix = ARGV[1]
        local results = {}

        -- 从ARGV[2]开始，每3个参数为一组任务信息
        -- [stream_key, stream_data, execute_at]
        for i = 2, #ARGV, 3 do
            local stream_key = ARGV[i]
            local stream_data = ARGV[i+1]
            local execute_at = tonumber(ARGV[i+2])

            -- 使用Hash存储所有队列的offset
            local offsets_hash = prefix .. ':QUEUE_OFFSETS'

            -- 从stream_key中提取队列名
            local queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

            -- 使用HINCRBY原子递增offset
            local current_offset = redis.call('HINCRBY', offsets_hash, queue_name, 1)

            -- 1. 添加消息到Stream（包含offset字段）
            local stream_id = redis.call('XADD', stream_key, '*',
                'data', stream_data,
                'offset', current_offset)

            -- 2. 添加到延迟队列ZSET（使用execute_at作为分数）
            local delayed_queue_key = prefix .. ':DELAYED_QUEUE:' .. queue_name
            redis.call('ZADD', delayed_queue_key, execute_at, stream_id)

            -- 3. 设置任务状态Hash（用于追踪任务状态）
            local task_key = prefix .. ':TASK:' .. stream_id
            redis.call('HSET', task_key, 'status', 'delayed')
            redis.call('EXPIRE', task_key, 3600)  -- 1小时过期

            -- 保存stream_id到结果
            table.insert(results, stream_id)
        end

        return results
        """

        prefixed_queue = self._get_prefixed_queue_name(queue)
        current_time = time.time()

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix]

        for message in messages:
            # 添加延迟执行标记到消息体
            msg_dict = message.copy()
            execute_at = current_time + delay
            msg_dict['execute_at'] = execute_at
            msg_dict['is_delayed'] = 1

            stream_data = dumps_str(msg_dict)

            lua_args.extend([
                prefixed_queue,
                stream_data,
                str(execute_at)
            ])

        # 注册并执行Lua脚本
        if not self._delayed_task_script:
            self._delayed_task_script = self.redis.register_script(lua_script)

        results = await self._delayed_task_script(keys=[], args=lua_args)

        # 解码结果
        decoded_results = [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]

        logger.debug(f"Sent {len(decoded_results)} delayed messages to queue {queue} (delay={delay}s)")
        return decoded_results

    async def send_single_message(
        self,
        queue: str,
        message: Dict,
        priority: Optional[int] = None,
        delay: Optional[float] = None
    ) -> str:
        """
        发送单个消息（便捷方法）

        Args:
            queue: 队列名
            message: 消息字典
            priority: 优先级（可选）
            delay: 延迟时间（可选）

        Returns:
            str: Stream ID
        """
        results = await self.send_messages(queue, [message], priority=priority, delay=delay)
        return results[0] if results else None

    async def get_queue_size(self, queue: str) -> int:
        """
        获取队列大小（Stream长度）

        Args:
            queue: 队列名

        Returns:
            int: 队列中的消息数量
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)
        return await self.redis.xlen(prefixed_queue)

    async def get_delayed_queue_size(self, queue: str) -> int:
        """
        获取延迟队列大小（Sorted Set大小）

        Args:
            queue: 队列名

        Returns:
            int: 延迟队列中的消息数量
        """
        delayed_queue = self._get_delayed_queue_name(queue)
        return await self.redis.zcard(delayed_queue)
