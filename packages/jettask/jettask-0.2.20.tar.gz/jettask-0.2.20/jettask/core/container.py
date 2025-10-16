"""
依赖注入容器 - 统一管理服务实例
"""

import logging
from typing import Optional, Dict, Any
import redis
import redis.asyncio as aioredis

from jettask.config.config import JetTaskConfig

logger = logging.getLogger('app')


class ServiceContainer:
    """
    服务容器 - 管理所有服务实例

    职责：
    1. 统一管理 Redis 客户端（避免重复创建）
    2. 统一管理消息处理组件（MessageSender, MessageReader, DelayedMessageScanner）
    3. 统一管理 Worker 相关组件（WorkerStateManager, WorkerScanner）
    4. 提供单例模式，确保全局唯一

    设计原则：
    - 延迟初始化：只在需要时创建实例
    - 单例模式：同一配置只创建一次实例
    - 依赖注入：组件之间的依赖由容器管理
    """

    def __init__(self, config: JetTaskConfig):
        """
        初始化服务容器

        Args:
            config: JetTask配置对象
        """
        self.config = config

        # Redis客户端缓存（从全局客户端获取，不再管理连接池）
        self._sync_text_redis: Optional[redis.Redis] = None
        self._sync_binary_redis: Optional[redis.Redis] = None
        self._async_text_redis: Optional[aioredis.Redis] = None
        self._async_binary_redis: Optional[aioredis.Redis] = None

        # 消息处理组件
        self._message_sender = None
        self._message_reader = None
        self._delayed_scanner = None

        # Worker管理组件
        self._worker_state_manager = None
        self._worker_scanner = None
        self._worker_registry = None

        # 队列和任务注册组件
        self._queue_registry = None
        self._task_registry_with_redis = None

        # 其他组件
        self._consumer_manager = None

        # 新架构组件
        self._queue_manager = None
        self._queue_router = None
        self._queue_monitor = None
        self._task_registry = None
        self._task_executor = None
        self._worker_manager = None

        logger.info(f"ServiceContainer initialized with redis_url={config.redis.url}, prefix={config.redis.prefix}")

    # ==================== Redis 客户端管理 ====================

    def _get_sync_text_client(self) -> redis.Redis:
        """获取同步文本模式客户端（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_sync_redis_client
        return get_sync_redis_client(
            redis_url=self.config.redis.url,
            decode_responses=True,
            max_connections=self.config.redis.max_connections
        )

    def _get_sync_binary_client(self) -> redis.Redis:
        """获取同步二进制模式客户端（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_sync_redis_client
        return get_sync_redis_client(
            redis_url=self.config.redis.url,
            decode_responses=False,
            max_connections=self.config.redis.max_connections
        )

    def _get_async_text_client(self) -> aioredis.Redis:
        """获取异步文本模式客户端（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_async_redis_client
        return get_async_redis_client(
            redis_url=self.config.redis.url,
            decode_responses=True,
            max_connections=self.config.redis.max_connections
        )

    def _get_async_binary_client(self) -> aioredis.Redis:
        """获取异步二进制模式客户端（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_async_redis_client
        return get_async_redis_client(
            redis_url=self.config.redis.url,
            decode_responses=False,
            max_connections=self.config.redis.max_connections
        )

    def get_redis_client(self, async_mode: bool = False, binary: bool = False) -> Any:
        """
        获取 Redis 客户端（单例模式）

        Args:
            async_mode: 是否使用异步客户端
            binary: 是否使用二进制模式（用于Stream操作）

        Returns:
            Redis客户端实例

        示例:
            # 同步文本模式（用于普通操作）
            redis = container.get_redis_client(async_mode=False, binary=False)

            # 异步二进制模式（用于Stream操作）
            redis = container.get_redis_client(async_mode=True, binary=True)
        """
        if async_mode:
            if binary:
                if not self._async_binary_redis:
                    self._async_binary_redis = self._get_async_binary_client()
                    logger.debug("Obtained async binary Redis client from global cache")
                return self._async_binary_redis
            else:
                if not self._async_text_redis:
                    self._async_text_redis = self._get_async_text_client()
                    logger.debug("Obtained async text Redis client from global cache")
                return self._async_text_redis
        else:
            if binary:
                if not self._sync_binary_redis:
                    self._sync_binary_redis = self._get_sync_binary_client()
                    logger.debug("Obtained sync binary Redis client from global cache")
                return self._sync_binary_redis
            else:
                if not self._sync_text_redis:
                    self._sync_text_redis = self._get_sync_text_client()
                    logger.debug("Obtained sync text Redis client from global cache")
                return self._sync_text_redis

    # ==================== 消息处理组件 ====================

    def get_message_sender(self):
        """
        获取 MessageSender 实例（单例）

        Returns:
            MessageSender实例
        """
        if not self._message_sender:
            from ..messaging.sender import MessageSender

            self._message_sender = MessageSender(
                async_redis_client=self.get_redis_client(async_mode=True, binary=True),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created MessageSender")

        return self._message_sender

    def get_message_reader(self):
        """
        获取 MessageReader 实例（单例）

        Returns:
            MessageReader实例
        """
        if not self._message_reader:
            from ..messaging.reader import MessageReader

            self._message_reader = MessageReader(
                async_redis_client=self.get_redis_client(async_mode=True, binary=False),
                async_binary_redis_client=self.get_redis_client(async_mode=True, binary=True),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created MessageReader")

        return self._message_reader

    def get_delayed_scanner(self):
        """
        获取 DelayedMessageScanner 实例（单例）

        Returns:
            DelayedMessageScanner实例
        """
        if not self._delayed_scanner:
            from ..messaging.scanner import DelayedMessageScanner

            self._delayed_scanner = DelayedMessageScanner(
                async_binary_redis_client=self.get_redis_client(async_mode=True, binary=True),
                redis_prefix=self.config.redis.prefix,
                scan_interval=self.config.message.delayed_scan_interval,
                batch_size=self.config.message.delayed_batch_size
            )
            logger.info("Created DelayedMessageScanner")

        return self._delayed_scanner

    # ==================== Worker 管理组件 ====================

    def get_worker_state_manager(self):
        """
        获取 WorkerStateManager 实例（单例）

        Returns:
            WorkerStateManager实例
        """
        if not self._worker_state_manager:
            from .worker_state_manager import WorkerStateManager

            self._worker_state_manager = WorkerStateManager(
                redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created WorkerStateManager")

        return self._worker_state_manager

    def get_worker_scanner(self):
        """
        获取 WorkerScanner 实例（单例）

        Returns:
            WorkerScanner实例
        """
        if not self._worker_scanner:
            from jettask.worker.lifecycle import WorkerScanner

            self._worker_scanner = WorkerScanner(
                sync_redis=self.get_redis_client(async_mode=False, binary=False),
                async_redis=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix,
                heartbeat_timeout=self.config.executor.worker_heartbeat_timeout,
                worker_state_manager=self.get_worker_state_manager()
            )
            logger.info("Created WorkerScanner")

        return self._worker_scanner

    # ==================== 注册管理组件 ====================

    def get_worker_registry(self):
        """
        获取 WorkerRegistry 实例（单例）

        Returns:
            WorkerState实例（之前叫 WorkerRegistry）
        """
        if not self._worker_registry:
            from jettask.worker.manager import WorkerState

            self._worker_registry = WorkerState(
                redis_client=self.get_redis_client(async_mode=False, binary=False),
                async_redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created WorkerState")

        return self._worker_registry

    def get_queue_registry(self):
        """
        获取 QueueRegistry 实例（单例）

        Returns:
            QueueRegistry实例
        """
        if not self._queue_registry:
            from jettask.messaging.registry import QueueRegistry

            self._queue_registry = QueueRegistry(
                redis_client=self.get_redis_client(async_mode=False, binary=False),
                async_redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created QueueRegistry")

        return self._queue_registry

    def get_task_registry_with_redis(self):
        """
        获取带 Redis 功能的 TaskRegistry 实例（单例）

        Returns:
            TaskRegistry实例
        """
        if not self._task_registry_with_redis:
            from jettask.task.task_registry import TaskRegistry

            self._task_registry_with_redis = TaskRegistry(
                redis_client=self.get_redis_client(async_mode=False, binary=False),
                async_redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created TaskRegistry with Redis")

        return self._task_registry_with_redis

    # ==================== 其他组件 ====================

    def get_consumer_manager(self, queues=None, app=None):
        """
        获取 ConsumerManager 实例（单例）

        Args:
            queues: 队列列表（可选，首次调用时需要）
            app: Jettask应用实例（可选）

        Returns:
            ConsumerManager实例
        """
        if not self._consumer_manager:
            from .consumer_manager import ConsumerManager, ConsumerStrategy

            if queues is None:
                queues = []

            strategy = ConsumerStrategy(self.config.consumer.strategy)

            consumer_config = {
                'queues': queues,
                'redis_prefix': self.config.redis.prefix,
                'redis_url': self.config.redis.url,
                'heartbeat_interval': self.config.consumer.heartbeat_interval,
                'heartbeat_timeout': self.config.consumer.heartbeat_timeout,
                'reuse_timeout': self.config.consumer.reuse_timeout
            }

            self._consumer_manager = ConsumerManager(
                redis_client=self.get_redis_client(async_mode=False, binary=False),
                strategy=strategy,
                config=consumer_config,
                app=app
            )
            logger.info(f"Created ConsumerManager with strategy={strategy}")

        return self._consumer_manager

    # ==================== 新架构组件 ====================

    def get_queue_manager(self):
        """
        获取 QueueManager 实例（单例）

        Returns:
            QueueManager实例
        """
        if not self._queue_manager:
            from jettask.messaging import QueueManager

            self._queue_manager = QueueManager(
                message_sender=self.get_message_sender(),
                message_reader=self.get_message_reader(),
                redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix
            )
            logger.info("Created QueueManager")

        return self._queue_manager

    def get_queue_router(self):
        """
        获取 QueueRouter 实例（单例）

        Returns:
            QueueRouter实例
        """
        if not self._queue_router:
            from jettask.messaging import QueueRouter

            self._queue_router = QueueRouter()
            logger.info("Created QueueRouter")

        return self._queue_router

    def get_queue_monitor(self):
        """
        获取 QueueMonitor 实例（单例）

        Returns:
            QueueMonitor实例
        """
        if not self._queue_monitor:
            from jettask.messaging import QueueMonitor

            self._queue_monitor = QueueMonitor(
                queue_manager=self.get_queue_manager()
            )
            logger.info("Created QueueMonitor")

        return self._queue_monitor

    def get_task_registry(self):
        """
        获取 TaskRegistry 实例（单例）

        Returns:
            TaskRegistry实例
        """
        if not self._task_registry:
            from ..task import TaskRegistry

            self._task_registry = TaskRegistry()
            logger.info("Created TaskRegistry")

        return self._task_registry

    def get_task_executor(self, data_access=None, retry_manager=None):
        """
        获取 TaskExecutor 实例（单例）

        Args:
            data_access: 数据访问层（可选）
            retry_manager: 重试管理器（可选）

        Returns:
            TaskExecutor实例
        """
        if not self._task_executor:
            from ..task import TaskExecutor

            self._task_executor = TaskExecutor(
                task_registry=self.get_task_registry(),
                data_access=data_access,
                retry_manager=retry_manager
            )
            logger.info("Created TaskExecutor")

        return self._task_executor


    def get_worker_manager(self, strategy=None, worker_name=None):
        """
        获取 WorkerManager 实例（单例）

        Args:
            strategy: Worker策略（可选）
            worker_name: Worker名称（FIXED策略时使用）

        Returns:
            WorkerManager实例
        """
        if not self._worker_manager:
            from ..worker import WorkerManager, WorkerStrategy

            # 使用配置中的策略,如果没有则默认DYNAMIC
            if strategy is None:
                strategy_str = self.config.consumer.strategy
                if strategy_str == "fixed":
                    strategy = WorkerStrategy.FIXED
                elif strategy_str == "pod":
                    strategy = WorkerStrategy.POD
                else:
                    strategy = WorkerStrategy.DYNAMIC

            self._worker_manager = WorkerManager(
                redis_client=self.get_redis_client(async_mode=True, binary=False),
                redis_prefix=self.config.redis.prefix,
                strategy=strategy,
                worker_name=worker_name,
                heartbeat_interval=self.config.consumer.heartbeat_interval,
                heartbeat_timeout=self.config.consumer.heartbeat_timeout
            )
            logger.info(f"Created WorkerManager with strategy={strategy}")

        return self._worker_manager

    # ==================== 清理资源 ====================

    async def cleanup(self):
        """
        清理所有资源（异步）

        应在应用关闭时调用
        """
        logger.info("Cleaning up ServiceContainer resources...")

        # 停止延迟扫描器
        if self._delayed_scanner:
            await self._delayed_scanner.stop()
            logger.debug("Stopped DelayedMessageScanner")

        # 停止 WorkerStateManager
        if self._worker_state_manager:
            await self._worker_state_manager.stop_listener()
            logger.debug("Stopped WorkerStateManager")

        # 关闭异步Redis连接
        if self._async_text_redis:
            await self._async_text_redis.aclose()
            logger.debug("Closed async text Redis")

        if self._async_binary_redis:
            await self._async_binary_redis.aclose()
            logger.debug("Closed async binary Redis")

        # 关闭同步Redis连接
        if self._sync_text_redis:
            self._sync_text_redis.close()
            logger.debug("Closed sync text Redis")

        if self._sync_binary_redis:
            self._sync_binary_redis.close()
            logger.debug("Closed sync binary Redis")

        logger.info("ServiceContainer cleanup completed")

    def __del__(self):
        """析构函数：确保同步资源被释放"""
        if self._sync_text_redis:
            try:
                self._sync_text_redis.close()
            except:
                pass

        if self._sync_binary_redis:
            try:
                self._sync_binary_redis.close()
            except:
                pass
