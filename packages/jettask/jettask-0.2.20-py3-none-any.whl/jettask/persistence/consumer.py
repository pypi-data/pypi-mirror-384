"""PostgreSQL消费者主模块

协调各个子模块，提供统一的消费者接口。
"""

import asyncio
import logging
import os
import socket
import traceback
from typing import Optional

import redis.asyncio as redis
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from jettask.webui.config import PostgreSQLConfig, RedisConfig
from jettask.worker.manager import ConsumerManager

from .backlog_monitor import BacklogMonitor
from .task_updater import TaskUpdater
from .offline_recovery import OfflineRecoveryHandler
from .task_persistence import TaskPersistence
from .queue_discovery import QueueDiscovery
from .message_consumer import MessageConsumer
from .maintenance import DatabaseMaintenance

logger = logging.getLogger(__name__)


class PostgreSQLConsumer:
    """PostgreSQL消费者，从Redis队列消费任务并持久化到PostgreSQL

    支持多租户（命名空间）隔离

    架构说明：
    - BacklogMonitor: 监控Stream积压情况
    - TaskUpdater: 更新任务状态（从TASK_CHANGES流）
    - OfflineRecoveryHandler: 恢复离线worker的消息
    - TaskPersistence: 解析并持久化任务数据
    - QueueDiscovery: 发现和管理队列
    - MessageConsumer: 消费队列消息
    - DatabaseMaintenance: 数据库维护任务
    """

    def __init__(
        self,
        pg_config: PostgreSQLConfig,
        redis_config: RedisConfig,
        prefix: str = "jettask",
        node_id: str = None,
        # consumer_strategy 参数已移除，现在只使用 HEARTBEAT 策略
        namespace_id: str = None,
        namespace_name: str = None,
        enable_backlog_monitor: bool = True,
        backlog_monitor_interval: int = 1
    ):
        """初始化PostgreSQL消费者

        Args:
            pg_config: PostgreSQL配置
            redis_config: Redis配置
            prefix: Redis键前缀
            node_id: 节点ID
            consumer_strategy: 消费者策略
            namespace_id: 命名空间ID
            namespace_name: 命名空间名称
            enable_backlog_monitor: 是否启用积压监控
            backlog_monitor_interval: 积压监控间隔（秒）
        """
        self.pg_config = pg_config
        self.redis_config = redis_config
        self.prefix = prefix

        # 命名空间支持
        self.namespace_id = namespace_id
        self.namespace_name = namespace_name or "default"

        # 节点标识
        hostname = socket.gethostname()
        self.node_id = node_id or f"{hostname}_{os.getpid()}"

        # 消费者配置
        # consumer_strategy 已移除，现在只使用 HEARTBEAT 策略
        self.consumer_group = f"{prefix}_pg_consumer"

        # Redis和数据库连接（将在start时初始化）
        self.redis_client: Optional[Redis] = None
        self.async_engine = None
        self.AsyncSessionLocal = None

        # ConsumerManager（将在start时初始化）
        self.consumer_manager = None
        self.consumer_id = None

        # 各个子模块（将在start时初始化）
        self.backlog_monitor: Optional[BacklogMonitor] = None
        self.task_updater: Optional[TaskUpdater] = None
        self.offline_recovery: Optional[OfflineRecoveryHandler] = None
        self.task_persistence: Optional[TaskPersistence] = None
        self.queue_discovery: Optional[QueueDiscovery] = None
        self.message_consumer: Optional[MessageConsumer] = None
        self.database_maintenance: Optional[DatabaseMaintenance] = None

        # 积压监控配置
        self.enable_backlog_monitor = enable_backlog_monitor
        self.backlog_monitor_interval = backlog_monitor_interval

        self._running = False

    async def start(self):
        """启动消费者"""
        logger.info(f"Starting PostgreSQL consumer (modular) on node: {self.node_id}")

        # 1. 连接Redis（使用全局客户端实例）
        from jettask.utils.db_connector import get_async_redis_client, get_sync_redis_client

        # 构建 Redis URL
        redis_url = f"redis://"
        if self.redis_config.password:
            redis_url += f":{self.redis_config.password}@"
        redis_url += f"{self.redis_config.host}:{self.redis_config.port}/{self.redis_config.db}"

        self.redis_client = get_async_redis_client(
            redis_url=redis_url,
            decode_responses=False  # 保持二进制模式
        )

        # 2. 初始化ConsumerManager（需要同步的Redis客户端）
        sync_redis_client = get_sync_redis_client(
            redis_url=redis_url,
            decode_responses=True
        )

        # 配置ConsumerManager
        initial_queues = ['TASK_CHANGES']  # TASK_CHANGES是固定的
        consumer_config = {
            'redis_prefix': self.prefix,
            'queues': initial_queues,
            'worker_prefix': 'PG_CONSUMER',  # 使用不同的前缀，与task worker区分开
        }

        self.consumer_manager = ConsumerManager(
            redis_client=sync_redis_client,
            # strategy 参数已移除，现在只使用 HEARTBEAT 策略
            config=consumer_config
        )

        # 获取稳定的consumer_id
        self.consumer_id = self.consumer_manager.get_consumer_name('TASK_CHANGES')
        logger.debug(f"Using consumer_id: {self.consumer_id} with strategy: HEARTBEAT")

        # 3. 创建SQLAlchemy异步引擎
        if self.pg_config.dsn.startswith('postgresql://'):
            dsn = self.pg_config.dsn.replace('postgresql://', 'postgresql+asyncpg://', 1)
        else:
            dsn = self.pg_config.dsn

        self.async_engine = create_async_engine(
            dsn,
            pool_size=50,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=300,
            echo=False
        )

        # 预热连接池
        logger.debug("Pre-warming database connection pool...")
        async with self.async_engine.begin() as conn:
            await conn.execute(text("SELECT 1"))

        # 创建异步会话工厂
        self.AsyncSessionLocal = sessionmaker(
            self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        # 4. 初始化各个子模块
        # 任务持久化处理器
        self.task_persistence = TaskPersistence(
            async_session_local=self.AsyncSessionLocal,
            namespace_id=self.namespace_id,
            namespace_name=self.namespace_name
        )

        # 队列发现器
        self.queue_discovery = QueueDiscovery(
            redis_client=self.redis_client,
            redis_prefix=self.prefix,
            consumer_group=self.consumer_group,
            consumer_manager=self.consumer_manager
        )

        # 先进行一次队列发现，确保ConsumerManager有正确的队列列表
        await self.queue_discovery.initial_queue_discovery()

        # 消息消费器
        self.message_consumer = MessageConsumer(
            redis_client=self.redis_client,
            redis_prefix=self.prefix,
            consumer_group=self.consumer_group,
            consumer_id=self.consumer_id,
            task_persistence=self.task_persistence,
            queue_discovery=self.queue_discovery
        )

        # 任务状态更新器
        self.task_updater = TaskUpdater(
            redis_client=self.redis_client,
            async_session_local=self.AsyncSessionLocal,
            redis_prefix=self.prefix,
            consumer_id=self.consumer_id
        )

        # 离线恢复处理器
        self.offline_recovery = OfflineRecoveryHandler(
            redis_client=self.redis_client,
            redis_prefix=self.prefix,
            consumer_id=self.consumer_id,
            task_updater=self.task_updater
        )
        # 延迟初始化（需要consumer_manager）
        self.offline_recovery.set_consumer_manager(self.consumer_manager)

        # 数据库维护
        self.database_maintenance = DatabaseMaintenance(
            async_session_local=self.AsyncSessionLocal
        )

        # 积压监控器
        self.backlog_monitor = BacklogMonitor(
            redis_client=self.redis_client,
            async_session_local=self.AsyncSessionLocal,
            redis_prefix=self.prefix,
            namespace_name=self.namespace_name,
            node_id=self.node_id,
            enable_monitor=self.enable_backlog_monitor,
            monitor_interval=self.backlog_monitor_interval
        )

        # 5. 启动所有子模块
        self._running = True

        # 启动队列发现
        await self.queue_discovery.start_discovery()

        # 启动消息消费
        await self.message_consumer.start()

        # 启动任务状态更新
        await self.task_updater.start()

        # 启动离线恢复
        await self.offline_recovery.start()

        # 启动数据库维护
        await self.database_maintenance.start()

        # 启动积压监控
        if self.enable_backlog_monitor:
            await self.backlog_monitor.start()
            logger.info(f"Stream backlog monitor enabled with {self.backlog_monitor_interval}s interval")

        # 如果使用HEARTBEAT策略，ConsumerManager会自动管理心跳
        if self.consumer_manager:
            logger.debug("Heartbeat is managed by ConsumerManager")

        logger.debug("PostgreSQL consumer started successfully")

    async def stop(self):
        """停止消费者"""
        logger.debug("Stopping PostgreSQL consumer...")
        self._running = False

        # 停止所有子模块
        if self.backlog_monitor:
            await self.backlog_monitor.stop()

        if self.database_maintenance:
            await self.database_maintenance.stop()

        if self.offline_recovery:
            await self.offline_recovery.stop()

        if self.task_updater:
            await self.task_updater.stop()

        if self.message_consumer:
            await self.message_consumer.stop()

        if self.queue_discovery:
            await self.queue_discovery.stop_discovery()

        # 清理ConsumerManager
        if self.consumer_manager:
            try:
                self.consumer_manager.cleanup()
                logger.debug(f"Cleaned up ConsumerManager for consumer: {self.consumer_id}")
            except Exception as e:
                logger.error(f"Error cleaning up ConsumerManager: {e}")
                logger.error(traceback.format_exc())

        # 关闭连接
        if self.redis_client:
            await self.redis_client.close()

        if self.async_engine:
            await self.async_engine.dispose()

        logger.debug("PostgreSQL consumer stopped")
