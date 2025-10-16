"""
消息读取器 - 统一的消息读取和确认接口
从 EventPool 中提取的消息读取逻辑
"""

import logging
from typing import List, Dict, Optional, Tuple
from redis.asyncio import Redis as AsyncRedis

from ..utils.serializer import loads_str

logger = logging.getLogger('app')


class MessageReader:
    """
    统一的消息读取接口

    职责：
    1. 从 Redis Stream 读取消息（支持consumer group）
    2. 确认消息（ACK）
    3. 支持优先级队列
    4. 支持历史消息和新消息的读取
    5. 追踪读取进度（offset）
    """

    def __init__(
        self,
        async_redis_client: AsyncRedis,
        async_binary_redis_client: AsyncRedis,
        redis_prefix: str = 'jettask'
    ):
        """
        初始化消息读取器

        Args:
            async_redis_client: 异步Redis客户端（文本模式）
            async_binary_redis_client: 异步Redis客户端（二进制模式，用于Stream）
            redis_prefix: Redis键前缀
        """
        self.redis = async_redis_client
        self.binary_redis = async_binary_redis_client
        self.redis_prefix = redis_prefix

        logger.debug(f"MessageReader initialized with prefix: {redis_prefix}")

    def _get_prefixed_queue_name(self, queue: str) -> str:
        """获取带前缀的队列名"""
        return f"{self.redis_prefix}:QUEUE:{queue}"

    async def create_consumer_group(
        self,
        queue: str,
        group_name: str,
        start_id: str = "0"
    ) -> bool:
        """
        创建消费者组

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            start_id: 起始消息ID（"0"表示从最早的消息开始，"$"表示只读新消息）

        Returns:
            bool: 是否成功创建（如果已存在返回False）
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            await self.redis.xgroup_create(
                name=prefixed_queue,
                groupname=group_name,
                id=start_id,
                mkstream=True  # 如果stream不存在则创建
            )
            logger.info(f"Created consumer group {group_name} for queue {queue}")
            return True
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists for queue {queue}")
                return False
            else:
                logger.error(f"Error creating consumer group {group_name} for queue {queue}: {e}")
                raise

    async def read_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block: int = 1000,
        start_id: str = ">"
    ) -> List[Tuple[str, Dict]]:
        """
        从队列读取消息（使用consumer group）

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            consumer_name: 消费者名称
            count: 读取消息数量
            block: 阻塞时间（毫秒），0表示不阻塞
            start_id: 起始消息ID
                - ">" 表示只读取新消息（未被该组消费过的）
                - "0-0" 表示读取该消费者的待处理消息（PEL）

        Returns:
            List[Tuple[str, Dict]]: [(message_id, message_data), ...]

        示例:
            # 读取新消息
            messages = await reader.read_messages(
                "orders", "order_processor", "worker1", count=10
            )

            # 读取待处理消息（PEL）
            pending = await reader.read_messages(
                "orders", "order_processor", "worker1", start_id="0-0"
            )
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            # xreadgroup 返回格式: [(stream_name, [(id, {field: value})])]
            results = await self.binary_redis.xreadgroup(
                groupname=group_name,
                consumername=consumer_name,
                streams={prefixed_queue: start_id},
                count=count,
                block=block
            )

            if not results:
                return []

            # 解析结果
            messages = []
            for stream_name, stream_messages in results:
                for message_id, message_fields in stream_messages:
                    # 解码 message_id
                    if isinstance(message_id, bytes):
                        message_id = message_id.decode('utf-8')

                    # 解码 message_fields
                    # 注意：data字段是二进制的msgpack数据，不能用utf-8 decode
                    decoded_fields = {}
                    for key, value in message_fields.items():
                        key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                        # 对于data字段，保持二进制格式
                        if key_str == 'data':
                            decoded_fields[key_str] = value  # 保持bytes
                        else:
                            # 其他字段（如offset）可以解码为字符串
                            value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                            decoded_fields[key_str] = value_str

                    # 解析data字段（msgpack二进制数据）
                    if 'data' in decoded_fields:
                        try:
                            data = loads_str(decoded_fields['data'])
                        except Exception as e:
                            logger.warning(f"Failed to parse message data: {e}")
                            data = decoded_fields['data']
                    else:
                        data = decoded_fields

                    # 添加offset和其他元数据
                    if 'offset' in decoded_fields:
                        # 确保data是字典类型才添加offset
                        if isinstance(data, dict):
                            data['_offset'] = int(decoded_fields['offset'])

                    messages.append((message_id, data))

            logger.debug(f"Read {len(messages)} messages from queue {queue}")
            return messages

        except Exception as e:
            if "NOGROUP" in str(e):
                logger.warning(f"Consumer group {group_name} does not exist for queue {queue}")
                # 自动创建consumer group
                await self.create_consumer_group(queue, group_name, start_id="0")
                # 重试读取
                return await self.read_messages(
                    queue, group_name, consumer_name, count, block, start_id
                )
            else:
                logger.error(f"Error reading messages from queue {queue}: {e}")
                raise

    async def read_from_multiple_queues(
        self,
        queues: List[str],
        group_name: str,
        consumer_name: str,
        count: int = 1,
        block: int = 1000,
        priority_order: bool = True
    ) -> List[Tuple[str, str, Dict]]:
        """
        从多个队列读取消息（支持优先级）

        Args:
            queues: 队列名列表（按优先级排序，第一个优先级最高）
            group_name: 消费者组名
            consumer_name: 消费者名称
            count: 每个队列读取的消息数量
            block: 阻塞时间（毫秒）
            priority_order: 是否按优先级顺序读取（True: 高优先级队列有消息就不读低优先级）

        Returns:
            List[Tuple[str, str, Dict]]: [(queue, message_id, message_data), ...]
        """
        all_messages = []
        messages_needed = count

        for queue in queues:
            if messages_needed <= 0:
                break

            messages = await self.read_messages(
                queue, group_name, consumer_name,
                count=messages_needed, block=block
            )

            # 添加队列信息
            for message_id, message_data in messages:
                all_messages.append((queue, message_id, message_data))

            messages_needed -= len(messages)

            # 如果是优先级模式且高优先级队列有消息，就不再读取低优先级
            if priority_order and messages:
                break

        return all_messages

    async def acknowledge_message(
        self,
        queue: str,
        group_name: str,
        message_id: str
    ) -> bool:
        """
        确认消息（ACK）

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            message_id: 消息ID

        Returns:
            bool: 是否成功确认
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            result = await self.binary_redis.xack(
                prefixed_queue,
                group_name,
                message_id
            )
            logger.debug(f"ACK message {message_id} in queue {queue}")
            return result > 0
        except Exception as e:
            logger.error(f"Error acknowledging message {message_id} in queue {queue}: {e}")
            return False

    async def acknowledge_messages(
        self,
        queue: str,
        group_name: str,
        message_ids: List[str]
    ) -> int:
        """
        批量确认消息

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            message_ids: 消息ID列表

        Returns:
            int: 成功确认的消息数量
        """
        if not message_ids:
            return 0

        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            result = await self.binary_redis.xack(
                prefixed_queue,
                group_name,
                *message_ids
            )
            logger.debug(f"ACK {result} messages in queue {queue}")
            return result
        except Exception as e:
            logger.error(f"Error acknowledging {len(message_ids)} messages in queue {queue}: {e}")
            return 0

    async def get_pending_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: Optional[str] = None,
        count: int = 10
    ) -> List[Dict]:
        """
        获取待处理消息（PEL - Pending Entries List）

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            consumer_name: 消费者名称（可选，不指定则获取整个组的PEL）
            count: 返回的消息数量

        Returns:
            List[Dict]: 待处理消息信息列表
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            # XPENDING 命令
            if consumer_name:
                # 获取特定消费者的待处理消息
                result = await self.binary_redis.xpending_range(
                    prefixed_queue,
                    group_name,
                    min="-",
                    max="+",
                    count=count,
                    consumername=consumer_name
                )
            else:
                # 获取整个组的待处理消息
                result = await self.binary_redis.xpending_range(
                    prefixed_queue,
                    group_name,
                    min="-",
                    max="+",
                    count=count
                )

            # 解析结果
            pending = []
            for item in result:
                pending.append({
                    'message_id': item['message_id'].decode('utf-8') if isinstance(item['message_id'], bytes) else item['message_id'],
                    'consumer': item['consumer'].decode('utf-8') if isinstance(item['consumer'], bytes) else item['consumer'],
                    'time_since_delivered': item['time_since_delivered'],
                    'times_delivered': item['times_delivered']
                })

            return pending

        except Exception as e:
            logger.error(f"Error getting pending messages from queue {queue}: {e}")
            return []

    async def claim_messages(
        self,
        queue: str,
        group_name: str,
        consumer_name: str,
        message_ids: List[str],
        min_idle_time: int = 60000
    ) -> List[Tuple[str, Dict]]:
        """
        认领消息（从其他消费者转移到当前消费者）
        用于处理超时的待处理消息

        Args:
            queue: 队列名（不带前缀）
            group_name: 消费者组名
            consumer_name: 当前消费者名称
            message_ids: 要认领的消息ID列表
            min_idle_time: 最小空闲时间（毫秒），只认领超过此时间的消息

        Returns:
            List[Tuple[str, Dict]]: 成功认领的消息列表
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            # XCLAIM 命令
            results = await self.binary_redis.xclaim(
                prefixed_queue,
                group_name,
                consumer_name,
                min_idle_time,
                message_ids
            )

            # 解析结果
            messages = []
            for message_id, message_fields in results:
                # 解码
                if isinstance(message_id, bytes):
                    message_id = message_id.decode('utf-8')

                decoded_fields = {}
                for key, value in message_fields.items():
                    key_str = key.decode('utf-8') if isinstance(key, bytes) else key
                    # 对于data字段，保持二进制格式
                    if key_str == 'data':
                        decoded_fields[key_str] = value
                    else:
                        value_str = value.decode('utf-8') if isinstance(value, bytes) else value
                        decoded_fields[key_str] = value_str

                # 解析data字段（msgpack二进制数据）
                if 'data' in decoded_fields:
                    try:
                        data = loads_str(decoded_fields['data'])
                    except Exception:
                        data = decoded_fields['data']
                else:
                    data = decoded_fields

                # 添加offset（如果有）
                if 'offset' in decoded_fields and isinstance(data, dict):
                    data['_offset'] = int(decoded_fields['offset'])

                messages.append((message_id, data))

            logger.info(f"Claimed {len(messages)} messages from queue {queue}")
            return messages

        except Exception as e:
            logger.error(f"Error claiming messages from queue {queue}: {e}")
            return []

    async def update_read_offset(
        self,
        queue: str,
        group_name: str,
        offset: int
    ):
        """
        更新读取进度（offset）

        Args:
            queue: 队列名（不带前缀，可能包含优先级后缀，如 "robust_bench2:8"）
            group_name: 消费者组名（格式：{prefix}:QUEUE:{base_queue}:{task_name}）
            offset: 新的offset值
        """
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

        # 从 group_name 中提取 task_name（最后一段）
        task_name = group_name.split(':')[-1]

        # 构建 field：队列名（含优先级）+ 任务名
        # 例如：robust_bench2:8:benchmark_task
        field = f"{queue}:{task_name}"

        try:
            # 使用Lua脚本原子性地更新最大offset
            lua_script = """
            local hash_key = KEYS[1]
            local field = KEYS[2]
            local new_value = tonumber(ARGV[1])

            local current = redis.call('HGET', hash_key, field)
            if current == false or tonumber(current) < new_value then
                redis.call('HSET', hash_key, field, new_value)
                return 1
            else
                return 0
            end
            """

            await self.redis.eval(
                lua_script,
                2,
                read_offsets_key,
                field,
                str(offset)
            )

            logger.debug(f"Updated read offset for {field} to {offset}")

        except Exception as e:
            logger.error(f"Error updating read offset: {e}")

    async def get_queue_length(self, queue: str) -> int:
        """
        获取队列长度

        Args:
            queue: 队列名（不带前缀）

        Returns:
            int: 队列中的消息数量
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)
        return await self.binary_redis.xlen(prefixed_queue)

    async def get_consumer_group_info(self, queue: str) -> List[Dict]:
        """
        获取消费者组信息

        Args:
            queue: 队列名（不带前缀）

        Returns:
            List[Dict]: 消费者组信息列表
        """
        prefixed_queue = self._get_prefixed_queue_name(queue)

        try:
            groups = await self.binary_redis.xinfo_groups(prefixed_queue)
            return groups
        except Exception as e:
            logger.error(f"Error getting consumer group info for queue {queue}: {e}")
            return []
