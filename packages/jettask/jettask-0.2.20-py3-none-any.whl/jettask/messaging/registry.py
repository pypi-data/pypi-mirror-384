"""
队列注册管理模块
负责队列、延迟队列、消费者组的注册和查询功能
"""

import logging
from typing import Set, List

logger = logging.getLogger(__name__)


class QueueRegistry:
    """
    队列注册管理器
    维护队列的注册信息，提供队列发现功能
    """

    def __init__(self, redis_client, async_redis_client, redis_prefix: str = 'jettask'):
        self.redis = redis_client
        self.async_redis = async_redis_client
        self.redis_prefix = redis_prefix

        # 注册表键
        self.queues_registry_key = f"{redis_prefix}:REGISTRY:QUEUES"  # 存储所有队列（包括优先级队列）
        self.delayed_queues_registry_key = f"{redis_prefix}:REGISTRY:DELAYED_QUEUES"
        self.consumer_groups_registry_key = f"{redis_prefix}:REGISTRY:CONSUMER_GROUPS"

    # ========== 队列管理 ==========

    def register_queue_sync(self, queue_name: str):
        """注册队列（同步）"""
        self.redis.sadd(self.queues_registry_key, queue_name)
        logger.debug(f"Registered queue: {queue_name}")

    async def register_queue(self, queue_name: str):
        """注册队列（异步）"""
        await self.async_redis.sadd(self.queues_registry_key, queue_name)
        logger.debug(f"Registered queue: {queue_name}")

    async def unregister_queue(self, queue_name: str):
        """注销队列"""
        await self.async_redis.srem(self.queues_registry_key, queue_name)
        logger.debug(f"Unregistered queue: {queue_name}")

    async def get_all_queues(self) -> Set[str]:
        """获取所有队列（不使用 SCAN）"""
        return await self.async_redis.smembers(self.queues_registry_key)

    def get_all_queues_sync(self) -> Set[str]:
        """同步获取所有队列"""
        return self.redis.smembers(self.queues_registry_key)

    async def get_queue_count(self) -> int:
        """获取队列数量"""
        return await self.async_redis.scard(self.queues_registry_key)

    # ========== 延迟队列管理 ==========

    async def register_delayed_queue(self, queue_name: str):
        """注册延迟队列"""
        await self.async_redis.sadd(self.delayed_queues_registry_key, queue_name)
        logger.debug(f"Registered delayed queue: {queue_name}")

    async def unregister_delayed_queue(self, queue_name: str):
        """注销延迟队列"""
        await self.async_redis.srem(self.delayed_queues_registry_key, queue_name)
        logger.debug(f"Unregistered delayed queue: {queue_name}")

    async def get_all_delayed_queues(self) -> Set[str]:
        """获取所有延迟队列"""
        return await self.async_redis.smembers(self.delayed_queues_registry_key)

    def get_all_delayed_queues_sync(self) -> Set[str]:
        """同步获取所有延迟队列"""
        return self.redis.smembers(self.delayed_queues_registry_key)

    async def get_delayed_queue_count(self) -> int:
        """获取延迟队列数量"""
        return await self.async_redis.scard(self.delayed_queues_registry_key)

    # ========== Consumer Group 管理 ==========

    async def register_consumer_group(self, queue: str, group_name: str):
        """注册 Consumer Group"""
        key = f"{self.consumer_groups_registry_key}:{queue}"
        await self.async_redis.sadd(key, group_name)
        logger.debug(f"Registered consumer group: {group_name} for queue: {queue}")

    async def unregister_consumer_group(self, queue: str, group_name: str):
        """注销 Consumer Group"""
        key = f"{self.consumer_groups_registry_key}:{queue}"
        await self.async_redis.srem(key, group_name)
        logger.debug(f"Unregistered consumer group: {group_name} for queue: {queue}")

    async def get_consumer_groups_for_queue(self, queue: str) -> Set[str]:
        """获取队列的所有 Consumer Group"""
        key = f"{self.consumer_groups_registry_key}:{queue}"
        return await self.async_redis.smembers(key)

    # ========== 优先级队列管理 ==========

    def register_priority_queue_sync(self, base_queue: str, priority: int):
        """注册优先级队列（同步）

        直接添加到全局队列注册表
        """
        priority_queue = f"{base_queue}:{priority}"
        self.redis.sadd(self.queues_registry_key, priority_queue)
        logger.debug(f"Registered priority queue: {priority_queue}")

    async def register_priority_queue(self, base_queue: str, priority: int):
        """注册优先级队列（异步）

        直接添加到全局队列注册表
        """
        priority_queue = f"{base_queue}:{priority}"
        await self.async_redis.sadd(self.queues_registry_key, priority_queue)
        logger.debug(f"Registered priority queue: {priority_queue}")

    async def unregister_priority_queue(self, base_queue: str, priority: int):
        """注销优先级队列"""
        priority_queue = f"{base_queue}:{priority}"
        await self.async_redis.srem(self.queues_registry_key, priority_queue)
        logger.debug(f"Unregistered priority queue: {priority_queue}")

    async def get_priority_queues_for_base(self, base_queue: str) -> List[str]:
        """获取基础队列的所有优先级队列

        从全局队列注册表中过滤出该基础队列的所有优先级队列
        """
        # 获取所有队列
        all_queues = await self.async_redis.smembers(self.queues_registry_key)

        # 过滤出该基础队列的优先级队列
        result = []
        for queue in all_queues:
            if isinstance(queue, bytes):
                queue = queue.decode('utf-8')

            # 检查是否是该基础队列的优先级队列
            # 格式：base_queue:priority（priority 是数字）
            if queue.startswith(f"{base_queue}:"):
                # 提取最后部分，检查是否是数字
                parts = queue.split(':')
                if len(parts) >= 2 and parts[-1].isdigit():
                    result.append(queue)

        # 按优先级排序（数字越小优先级越高）
        result.sort(key=lambda x: int(x.split(':')[-1]))
        return result

    async def clear_priority_queues_for_base(self, base_queue: str):
        """清理基础队列的所有优先级队列注册信息"""
        # 获取该基础队列的所有优先级队列
        priority_queues = await self.get_priority_queues_for_base(base_queue)

        # 从全局队列注册表中删除
        if priority_queues:
            await self.async_redis.srem(self.queues_registry_key, *priority_queues)
            logger.debug(f"Cleared {len(priority_queues)} priority queues for base queue: {base_queue}")

    # ========== 任务名称查询 ==========

    def get_task_names_by_queue_sync(self, base_queue: str) -> Set[str]:
        """
        通过基础队列名获取所有关联的任务名称（同步）

        从 READ_OFFSETS 中提取，key 格式可能是：
        - robust_bench2:benchmark_task （基础队列）
        - robust_bench2:8:benchmark_task （优先级队列）

        Args:
            base_queue: 基础队列名（不含优先级）

        Returns:
            Set[str]: 任务名称集合（去重后）

        Examples:
            >>> registry.get_task_names_by_queue_sync("robust_bench2")
            {'benchmark_task', 'another_task'}
        """
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

        # 获取所有 keys
        all_keys = self.redis.hkeys(read_offsets_key)

        task_names = set()
        for key in all_keys:
            # 解码 key
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            # 检查是否以 base_queue 开头
            if not key.startswith(f"{base_queue}:"):
                continue

            # 去掉队列名前缀
            suffix = key[len(base_queue) + 1:]  # +1 for the ':'

            # suffix 可能是 "benchmark_task" 或 "8:benchmark_task"
            parts = suffix.split(':')

            # 如果第一部分是数字，说明是优先级，task_name 是后面的部分
            if parts[0].isdigit() and len(parts) > 1:
                # 支持 task_name 中可能包含 ':'
                task_name = ':'.join(parts[1:])
            else:
                # 没有优先级，整个 suffix 就是 task_name
                task_name = suffix

            if task_name:  # 过滤空字符串
                task_names.add(task_name)

        return task_names

    async def get_task_names_by_queue(self, base_queue: str) -> Set[str]:
        """
        通过基础队列名获取所有关联的任务名称（异步）

        从 READ_OFFSETS 中提取，key 格式可能是：
        - robust_bench2:benchmark_task （基础队列）
        - robust_bench2:8:benchmark_task （优先级队列）

        Args:
            base_queue: 基础队列名（不含优先级）

        Returns:
            Set[str]: 任务名称集合（去重后）

        Examples:
            >>> await registry.get_task_names_by_queue("robust_bench2")
            {'benchmark_task', 'another_task'}
        """
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

        # 获取所有 keys
        all_keys = await self.async_redis.hkeys(read_offsets_key)

        task_names = set()
        for key in all_keys:
            # 解码 key
            if isinstance(key, bytes):
                key = key.decode('utf-8')

            # 检查是否以 base_queue 开头
            if not key.startswith(f"{base_queue}:"):
                continue

            # 去掉队列名前缀
            suffix = key[len(base_queue) + 1:]  # +1 for the ':'

            # suffix 可能是 "benchmark_task" 或 "8:benchmark_task"
            parts = suffix.split(':')

            # 如果第一部分是数字，说明是优先级，task_name 是后面的部分
            if parts[0].isdigit() and len(parts) > 1:
                # 支持 task_name 中可能包含 ':'
                task_name = ':'.join(parts[1:])
            else:
                # 没有优先级，整个 suffix 就是 task_name
                task_name = suffix

            if task_name:  # 过滤空字符串
                task_names.add(task_name)

        return task_names
