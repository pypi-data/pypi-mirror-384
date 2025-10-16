"""队列发现模块

负责动态发现新队列，并为新队列创建消费者组。
使用队列注册表替代scan命令以提高性能。
"""

import asyncio
import logging
import traceback
from typing import Set

import redis.asyncio as redis
from redis.asyncio import Redis

logger = logging.getLogger(__name__)


class QueueDiscovery:
    """队列发现器

    职责：
    - 初始队列发现（启动时执行一次）
    - 定期发现新队列
    - 为新队列创建消费者组
    - 更新ConsumerManager的队列列表
    """

    def __init__(
        self,
        redis_client: Redis,
        redis_prefix: str,
        consumer_group: str,
        consumer_manager=None
    ):
        """初始化队列发现器

        Args:
            redis_client: Redis异步客户端
            redis_prefix: Redis键前缀
            consumer_group: 消费者组名称
            consumer_manager: ConsumerManager实例（可选）
        """
        self.redis_client = redis_client
        self.redis_prefix = redis_prefix
        self.consumer_group = consumer_group
        self.consumer_manager = consumer_manager

        # 队列注册表的Redis key
        self.queue_registry_key = f"{redis_prefix}:QUEUE_REGISTRY"

        # 已知队列集合
        self._known_queues = set()

        self._running = False
        self._discovery_task = None

    async def initial_queue_discovery(self) -> Set[str]:
        """初始队列发现，在启动时执行一次 - 使用队列注册表替代scan

        Returns:
            发现的队列集合
        """
        try:
            new_queues = set()
            logger.info(f"Starting initial queue discovery from queue registry: {self.queue_registry_key}")

            # 从队列注册表获取所有队列
            queue_members = await self.redis_client.smembers(self.queue_registry_key.encode())
            for queue_name_bytes in queue_members:
                queue_name = queue_name_bytes.decode('utf-8') if isinstance(queue_name_bytes, bytes) else str(queue_name_bytes)
                new_queues.add(queue_name)
                logger.info(f"Found registered queue: {queue_name}")

            # 如果注册表为空，使用 RegistryManager 初始化
            if not new_queues:
                logger.warning(f"Queue registry is empty, initializing from RegistryManager...")
                from jettask.messaging.registry import QueueRegistry
                registry = QueueRegistry(
                    redis_client=None,  # 同步客户端，这里不需要
                    async_redis_client=self.redis_client,
                    redis_prefix=self.redis_prefix
                )

                # 初始化注册表（仅在首次运行时需要）
                await registry.initialize_from_existing_data()

                # 从注册表获取队列
                new_queues = await registry.get_all_queues()
                logger.info(f"Got {len(new_queues)} queues from registry manager")

            if new_queues:
                logger.info(f"Initial queue discovery found {len(new_queues)} queues: {new_queues}")
                # 合并所有队列：TASK_CHANGES + 动态发现的队列
                # 转换 bytes 为字符串
                string_queues = []
                for q in new_queues:
                    if isinstance(q, bytes):
                        string_queues.append(q.decode('utf-8'))
                    else:
                        string_queues.append(str(q))
                all_queues = string_queues + ['TASK_CHANGES']

                # 更新ConsumerManager的配置
                if self.consumer_manager:
                    self.consumer_manager.config['queues'] = all_queues

                    # 更新worker的队列信息
                    await self._update_worker_queues(all_queues)

                self._known_queues = new_queues

            return new_queues

        except Exception as e:
            logger.error(f"Error in initial queue discovery: {e}")
            logger.error(traceback.format_exc())
            return set()

    async def start_discovery(self):
        """启动定期队列发现"""
        self._running = True
        self._discovery_task = asyncio.create_task(self._discover_queues_loop())
        logger.debug("QueueDiscovery started")

    async def stop_discovery(self):
        """停止队列发现"""
        self._running = False
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        logger.debug("QueueDiscovery stopped")

    async def _discover_queues_loop(self):
        """定期发现新队列 - 使用队列注册表替代scan"""
        while self._running:
            try:
                new_queues = set()

                # 从队列注册表获取所有队列
                queue_members = await self.redis_client.smembers(self.queue_registry_key)
                for queue_name_bytes in queue_members:
                    queue_name = queue_name_bytes.decode('utf-8') if isinstance(queue_name_bytes, bytes) else str(queue_name_bytes)
                    new_queues.add(queue_name)

                # 优化：添加日志，只在队列数量或内容发生变化时记录
                if len(new_queues) != len(self._known_queues) or new_queues != self._known_queues:
                    logger.debug(f"Queue registry contains {len(new_queues)} queues: {sorted(new_queues)}")

                # 为新发现的队列创建消费者组（注意：新队列应该通过生产者自动注册）
                new_discovered = new_queues - self._known_queues
                if new_discovered:
                    for queue in new_discovered:
                        # 正确构建stream_key，保留优先级部分
                        stream_key = f"{self.redis_prefix}:QUEUE:{queue}"
                        try:
                            await self.redis_client.xgroup_create(
                                stream_key, self.consumer_group, id='0', mkstream=True
                            )
                            logger.info(f"Created consumer group for new queue: {queue} with stream_key: {stream_key}")
                        except redis.ResponseError:
                            pass

                # 更新ConsumerManager的队列列表（同步操作）
                if new_queues != self._known_queues:
                    logger.info(f"Queue discovery: found {len(new_queues)} queues: {new_queues}")
                    # 合并所有队列：TASK_CHANGES + 动态发现的队列
                    all_queues = list(new_queues) + ['TASK_CHANGES']

                    # 更新ConsumerManager的配置
                    if self.consumer_manager:
                        self.consumer_manager.config['queues'] = all_queues

                        # 更新worker的队列信息
                        await self._update_worker_queues(all_queues)

                self._known_queues = new_queues
                await asyncio.sleep(10)  # 保持较短的检查间隔，确保新队列能及时发现

            except Exception as e:
                logger.error(f"Error discovering queues: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(10)

    async def _update_worker_queues(self, all_queues: list):
        """更新worker的队列信息到Redis"""
        try:
            # ConsumerStrategy 已移除，现在只使用 HEARTBEAT 策略

            # 获取实际的consumer_id（从心跳策略中）
            if hasattr(self.consumer_manager, '_heartbeat_strategy'):
                actual_consumer_id = self.consumer_manager._heartbeat_strategy.consumer_id
            else:
                # 从config中获取或使用默认值
                actual_consumer_id = self.consumer_manager.config.get('consumer_id', 'unknown')

            worker_key = f"{self.redis_prefix}:{self.consumer_manager.config.get('worker_prefix', 'PG_CONSUMER')}:{actual_consumer_id}"

            # 使用同步Redis客户端更新
            self.consumer_manager.redis_client.hset(
                worker_key,
                'queues',
                ','.join(all_queues)
            )
            logger.debug(f"Updated worker queues: {all_queues}")

        except Exception as e:
            logger.error(f"Error updating worker queues: {e}")
            logger.error(traceback.format_exc())

    def get_known_queues(self) -> Set[str]:
        """获取已知队列集合"""
        return self._known_queues.copy()
