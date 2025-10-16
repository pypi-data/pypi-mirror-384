"""
数据库连接工具类

提供统一的 Redis 和 PostgreSQL 连接管理，避免代码重复。
所有数据库连接池均为全局单例，复用连接池以节省资源。

文件结构：
============================================================
1. 导入和全局配置 (第7-23行)
   - 第三方库导入
   - Logger 初始化

2. 全局变量 (第25-38行)
   - Redis 连接池缓存（同步/异步、文本/二进制）
   - PostgreSQL 引擎和会话工厂缓存

3. 工具类 (第41-83行)
   - InfiniteRetry: 无限重试策略

4. 自定义 Redis 连接池实现 (第85-453行)
   - IdleTrackingBlockingConnectionPool: 同步连接池（带空闲回收）
   - AsyncIdleTrackingBlockingConnectionPool: 异步连接池（带空闲回收）

5. 连接池获取函数 (第455-740行)
   - get_sync_redis_pool: 获取同步 Redis 连接池
   - get_async_redis_pool: 获取异步 Redis 连接池
   - get_async_redis_pool_for_pubsub: 获取 PubSub 专用连接池
   - get_pg_engine_and_factory: 获取 PostgreSQL 引擎和会话工厂

6. 配置和连接器类 (第742-1249行)
   - DBConfig: 数据库配置数据类
   - SyncRedisConnector: 同步 Redis 连接器
   - RedisConnector: 异步 Redis 连接器
   - PostgreSQLConnector: PostgreSQL 连接器
   - ConnectionManager: 统一连接管理器

7. 全局客户端实例管理 (第1251-1378行)
   - get_sync_redis_client: 获取全局同步 Redis 客户端
   - get_async_redis_client: 获取全局异步 Redis 客户端
   - clear_all_cache: 清理所有缓存

============================================================
"""

# ============================================================
# Section 1: 导入和全局配置
# ============================================================
import os
import logging
import traceback
import socket
import time
import threading
import asyncio
from typing import Optional, Dict, Any, Union
from contextlib import asynccontextmanager, contextmanager
import redis as sync_redis
import redis.asyncio as redis
from redis.asyncio import BlockingConnectionPool
from redis.backoff import ExponentialBackoff
from redis.retry import Retry
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

logger = logging.getLogger(__name__)


# ============================================================
# Section 2: 全局变量
# ============================================================

class _PoolRegistry:
    """
    全局连接池注册表（单例模式）

    统一管理所有数据库连接池和客户端实例，避免全局变量分散
    """

    # Redis 连接池缓存
    sync_redis_pools: Dict[str, sync_redis.ConnectionPool] = {}
    sync_binary_redis_pools: Dict[str, sync_redis.ConnectionPool] = {}
    async_redis_pools: Dict[str, redis.ConnectionPool] = {}
    async_binary_redis_pools: Dict[str, redis.ConnectionPool] = {}

    # PostgreSQL 引擎和会话工厂缓存
    pg_engines: Dict[str, Any] = {}
    pg_session_factories: Dict[str, async_sessionmaker] = {}

    # Redis 客户端实例缓存
    sync_redis_clients: Dict[str, sync_redis.StrictRedis] = {}
    sync_binary_redis_clients: Dict[str, sync_redis.StrictRedis] = {}
    async_redis_clients: Dict[str, redis.StrictRedis] = {}
    async_binary_redis_clients: Dict[str, redis.StrictRedis] = {}

    @classmethod
    def clear_all(cls):
        """清空所有缓存"""
        cls.sync_redis_pools.clear()
        cls.sync_binary_redis_pools.clear()
        cls.async_redis_pools.clear()
        cls.async_binary_redis_pools.clear()
        cls.pg_engines.clear()
        cls.pg_session_factories.clear()
        cls.sync_redis_clients.clear()
        cls.sync_binary_redis_clients.clear()
        cls.async_redis_clients.clear()
        cls.async_binary_redis_clients.clear()


# 兼容旧代码：保持旧的全局变量引用（指向 _PoolRegistry）
_sync_redis_pools = _PoolRegistry.sync_redis_pools
_sync_binary_redis_pools = _PoolRegistry.sync_binary_redis_pools
_async_redis_pools = _PoolRegistry.async_redis_pools
_async_binary_redis_pools = _PoolRegistry.async_binary_redis_pools
_pg_engines = _PoolRegistry.pg_engines
_pg_session_factories = _PoolRegistry.pg_session_factories


# ============================================================
# Section 3: 工具类
# ============================================================

class InfiniteRetry(Retry):
    """无限重试的 Retry 策略"""

    def __init__(self):
        # 使用指数退避，最大间隔30秒
        super().__init__(
            ExponentialBackoff(cap=30, base=1),
            retries=-1  # -1 表示无限重试
        )

    def call_with_retry(self, do, fail):
        """
        执行操作，失败时无限重试

        Args:
            do: 要执行的函数
            fail: 失败时的回调函数
        """
        failures = 0
        backoff = self._backoff

        while True:
            try:
                return do()
            except Exception as error:
                failures += 1

                # 记录重试日志
                if failures == 1 or failures % 10 == 0:  # 第1次和每10次记录一次
                    logger.warning(
                        f"Redis 连接失败 (第 {failures} 次), 将在 {backoff.compute(failures)} 秒后重试: {error}"
                    )

                # 调用失败回调
                fail(error)

                # 等待后重试
                time.sleep(backoff.compute(failures))

                # 继续重试，永不放弃


# ============================================================
# Section 4: 自定义 Redis 连接池实现
# ============================================================

class IdleTrackingBlockingConnectionPool(sync_redis.BlockingConnectionPool):
    """
    带空闲连接跟踪和自动回收的同步阻塞连接池

    核心机制：
    1. 在 get_connection() 时记录连接的获取时间戳
    2. 在 release() 时更新连接的最后使用时间戳
    3. 使用后台线程定期检查并关闭超过 max_idle_time 的空闲连接
    """

    def __init__(self, *args, max_idle_time: int = 300, idle_check_interval: int = 60, **kwargs):
        """
        Args:
            max_idle_time: 最大空闲时间（秒），超过此时间的连接将被关闭，默认300秒
            idle_check_interval: 空闲检查间隔（秒），默认60秒
        """
        super().__init__(*args, **kwargs)

        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval

        # 连接最后使用时间戳字典 {connection_id: last_use_timestamp}
        self._connection_last_use: Dict[int, float] = {}
        self._connection_last_use_lock = threading.RLock()

        # 启动空闲连接清理线程
        self._cleaner_thread = None
        self._stop_cleaner = threading.Event()

        if max_idle_time > 0 and idle_check_interval > 0:
            self._start_idle_cleaner()
            # logger.info(f"启动同步空闲连接清理线程: max_idle_time={max_idle_time}s, check_interval={idle_check_interval}s")

    def get_connection(self, command_name=None, *keys, **options):
        """获取连接时记录获取时间"""
        conn = super().get_connection(command_name, *keys, **options)
        conn_id = id(conn)
        with self._connection_last_use_lock:
            if conn_id not in self._connection_last_use:
                self._connection_last_use[conn_id] = time.time()
                logger.debug(f"连接 {conn_id} 首次获取")
        return conn

    def release(self, connection):
        """释放连接时更新最后使用时间"""
        conn_id = id(connection)
        current_time = time.time()
        with self._connection_last_use_lock:
            self._connection_last_use[conn_id] = current_time
            logger.debug(f"连接 {conn_id} 释放，更新最后使用时间: {current_time}")
        super().release(connection)

    def _start_idle_cleaner(self):
        """启动空闲连接清理线程"""
        self._cleaner_thread = threading.Thread(
            target=self._idle_cleaner_loop,
            name="SyncIdleConnectionCleaner",
            daemon=True
        )
        self._cleaner_thread.start()

    def _idle_cleaner_loop(self):
        """空闲连接清理线程的主循环"""
        while not self._stop_cleaner.wait(self.idle_check_interval):
            try:
                self._cleanup_idle_connections()
            except Exception as e:
                logger.error(f"清理空闲连接时出错: {e}")
                logger.debug(traceback.format_exc())

    def _cleanup_idle_connections(self):
        """清理空闲连接"""
        current_time = time.time()
        connections_to_keep = []
        connections_to_close = []

        # 从队列中取出所有连接（非阻塞），并记录初始状态
        connections_to_check = []
        with self._lock:
            initial_total = len(self._connections)
            initial_available = self.pool.qsize()
            initial_in_use = initial_total - initial_available

            while True:
                try:
                    conn = self.pool.get_nowait()
                    connections_to_check.append(conn)
                except:
                    break

        available_count = len(connections_to_check)
        logger.debug(f"检查 {available_count} 个可用连接")

        if available_count <= 2:
            # 保留至少 2 个连接，全部放回
            with self._lock:
                for conn in connections_to_check:
                    self.pool.put(conn)
            logger.debug(f"可用连接数 {available_count} <= 2，跳过清理")
            return

        # 检查每个连接
        for conn in connections_to_check:
            if conn is None:
                # None 占位符，直接放回
                connections_to_keep.append(conn)
                continue

            conn_id = id(conn)
            with self._connection_last_use_lock:
                last_use = self._connection_last_use.get(conn_id, current_time)
                idle_time = current_time - last_use

            if idle_time > self.max_idle_time and len(connections_to_keep) + len(connections_to_check) - len(connections_to_close) > 2:
                # 标记为待关闭（确保至少保留2个）
                connections_to_close.append((conn, conn_id, idle_time))
            else:
                # 保留连接
                connections_to_keep.append(conn)

        # 关闭空闲连接
        closed_count = 0
        for conn, conn_id, idle_time in connections_to_close:
            try:
                # 1. 先从跟踪字典移除（避免其他线程访问）
                with self._connection_last_use_lock:
                    self._connection_last_use.pop(conn_id, None)

                # 2. 断开连接（这会关闭 socket）
                conn.disconnect()

                # 3. 从连接列表移除（必须在 disconnect 之后）
                with self._lock:
                    if conn in self._connections:
                        self._connections.remove(conn)

                closed_count += 1
                logger.debug(f"关闭空闲连接 {conn_id}，空闲时间: {idle_time:.1f}s")

            except Exception as e:
                logger.warning(f"断开连接 {conn_id} 失败: {e}")
                # 失败的连接也放回队列，避免丢失
                connections_to_keep.append(conn)
                # 恢复跟踪
                with self._connection_last_use_lock:
                    self._connection_last_use[conn_id] = time.time()

        # 将保留的连接放回队列
        with self._lock:
            for conn in connections_to_keep:
                self.pool.put(conn)

        if closed_count > 0:
            with self._lock:
                final_total = len(self._connections)
                final_available = self.pool.qsize()
                final_in_use = final_total - final_available
            logger.info(
                f"空闲连接清理完成: 清理前 {initial_total} (可用: {initial_available}, 使用中: {initial_in_use}), "
                f"关闭 {closed_count} 个, "
                f"剩余 {final_total} (可用: {final_available}, 使用中: {final_in_use})"
            )

    def _stop_idle_cleaner(self):
        """停止空闲连接清理线程"""
        if self._cleaner_thread and self._cleaner_thread.is_alive():
            self._stop_cleaner.set()
            self._cleaner_thread.join(timeout=5)
            # logger.info("同步空闲连接清理线程已停止")

        # 清空时间戳字典
        with self._connection_last_use_lock:
            self._connection_last_use.clear()

    def disconnect(self, inuse_connections: bool = True):
        """断开所有连接，停止清理线程"""
        self._stop_idle_cleaner()
        super().disconnect(inuse_connections)


class AsyncIdleTrackingBlockingConnectionPool(redis.BlockingConnectionPool):
    """
    带空闲连接跟踪和自动回收的异步阻塞连接池

    核心机制：
    1. 在 get_connection() 时记录连接的获取时间戳
    2. 在 release() 时更新连接的最后使用时间戳
    3. 使用 asyncio.Task 定期检查并关闭超过 max_idle_time 的空闲连接
    """

    def __init__(self, *args, max_idle_time: int = 300, idle_check_interval: int = 60, **kwargs):
        """
        Args:
            max_idle_time: 最大空闲时间（秒），超过此时间的连接将被关闭，默认300秒
            idle_check_interval: 空闲检查间隔（秒），默认60秒
        """
        # 提取自定义参数,避免传递给父类
        kwargs.pop('max_idle_time', None)
        kwargs.pop('idle_check_interval', None)

        super().__init__(*args, **kwargs)

        self.max_idle_time = max_idle_time
        self.idle_check_interval = idle_check_interval

        # 连接最后使用时间戳字典 {connection_id: last_use_timestamp}
        self._connection_last_use: Dict[int, float] = {}
        self._connection_last_use_lock = None  # 延迟创建，因为需要事件循环

        # 启动空闲连接清理任务
        self._cleaner_task = None
        self._stop_cleaner = None  # 延迟创建

        # if max_idle_time > 0 and idle_check_interval > 0:
        #     logger.info(f"将在首次使用时启动异步空闲连接清理任务: max_idle_time={max_idle_time}s, check_interval={idle_check_interval}s")

    async def get_connection(self, command_name=None, *keys, **options):
        """获取连接时记录获取时间"""
        # 确保清理任务已启动
        await self._ensure_cleaner_task_started()
        conn = await super().get_connection(command_name, *keys, **options)
        conn_id = id(conn)

        # 延迟初始化锁
        if self._connection_last_use_lock is None:
            self._connection_last_use_lock = asyncio.Lock()

        async with self._connection_last_use_lock:
            if conn_id not in self._connection_last_use:
                self._connection_last_use[conn_id] = time.time()
                logger.debug(f"连接 {conn_id} 首次获取")
        return conn

    async def release(self, connection):
        """释放连接时更新最后使用时间（异步方法）"""
        conn_id = id(connection)
        current_time = time.time()

        # 延迟初始化锁
        if self._connection_last_use_lock is None:
            self._connection_last_use_lock = asyncio.Lock()

        # 使用异步锁更新时间戳
        async with self._connection_last_use_lock:
            self._connection_last_use[conn_id] = current_time
            logger.debug(f"连接 {conn_id} 释放，更新最后使用时间: {current_time}")

        await super().release(connection)

    async def _ensure_cleaner_task_started(self):
        """确保清理任务已启动"""
        if self.max_idle_time > 0 and self.idle_check_interval > 0 and self._cleaner_task is None:
            # 延迟初始化事件
            if self._stop_cleaner is None:
                self._stop_cleaner = asyncio.Event()
            self._cleaner_task = asyncio.create_task(self._idle_cleaner_loop())
            # logger.info("异步空闲连接清理任务已启动")

    async def _idle_cleaner_loop(self):
        """空闲连接清理任务的主循环"""
        while True:
            try:
                # 等待指定间隔或停止信号
                await asyncio.wait_for(
                    self._stop_cleaner.wait(),
                    timeout=self.idle_check_interval
                )
                # 如果收到停止信号，退出循环
                break
            except asyncio.TimeoutError:
                # 超时，执行清理
                try:
                    await self._cleanup_idle_connections()
                except Exception as e:
                    logger.error(f"清理空闲连接时出错: {e}")
                    logger.debug(traceback.format_exc())

    async def _cleanup_idle_connections(self):
        """清理空闲连接"""
        if self._connection_last_use_lock is None:
            return

        current_time = time.time()
        connections_to_keep = []
        connections_to_close = []

        # 从 _available_connections 获取所有可用连接，并记录初始状态
        async with self._lock:
            if not hasattr(self, '_available_connections'):
                return
            connections_to_check = list(self._available_connections)
            initial_available = len(self._available_connections)
            initial_in_use = len(self._in_use_connections) if hasattr(self, '_in_use_connections') else 0
            initial_total = initial_available + initial_in_use

        available_count = len(connections_to_check)
        logger.debug(f"检查 {available_count} 个可用连接")

        if available_count <= 2:
            logger.debug(f"可用连接数 {available_count} <= 2，跳过清理")
            return

        # 检查每个连接
        for conn in connections_to_check:
            if conn is None:
                connections_to_keep.append(conn)
                continue

            conn_id = id(conn)
            async with self._connection_last_use_lock:
                last_use = self._connection_last_use.get(conn_id, current_time)
                idle_time = current_time - last_use

            if idle_time > self.max_idle_time and len(connections_to_keep) + len(connections_to_check) - len(connections_to_close) > 2:
                # 标记为待关闭（确保至少保留2个）
                connections_to_close.append((conn, conn_id, idle_time))
            else:
                # 保留连接
                connections_to_keep.append(conn)

        # 关闭空闲连接
        closed_count = 0
        for conn, conn_id, idle_time in connections_to_close:
            try:
                # 1. 先从跟踪字典移除（避免其他协程访问）
                async with self._connection_last_use_lock:
                    self._connection_last_use.pop(conn_id, None)

                # 2. 断开连接（这会关闭 socket）
                await conn.disconnect()
            
                # 3. 从连接集合/列表移除（必须在 disconnect 之后）
                async with self._lock:
                    if hasattr(self, '_available_connections') and conn in self._available_connections:
                        self._available_connections.remove(conn)
                    if hasattr(self, '_in_use_connections') and conn in self._in_use_connections:
                        # _in_use_connections 可能是 set 或 list，尝试两种方法
                        try:
                            self._in_use_connections.discard(conn)
                        except AttributeError:
                            self._in_use_connections.remove(conn)

                closed_count += 1
                logger.debug(f"关闭空闲连接 {conn_id}，空闲时间: {idle_time:.1f}s")

            except Exception as e:
                import traceback 
                traceback.print_exc()
                logger.warning(f"断开连接 {conn_id} 失败: {e}")
                logger.debug(traceback.format_exc())
                # 恢复跟踪
                async with self._connection_last_use_lock:
                    self._connection_last_use[conn_id] = time.time()

        # if closed_count > 0:
        #     async with self._lock:
        #         final_available = len(self._available_connections) if hasattr(self, '_available_connections') else 0
        #         final_in_use = len(self._in_use_connections) if hasattr(self, '_in_use_connections') else 0
        #         final_total = final_available + final_in_use
        #     logger.info(
        #         f"空闲连接清理完成: 清理前 {initial_total}, "
        #         f"关闭 {closed_count} 个, "
        #         f"剩余 {final_total} "
        #         f"{len(self._connection_last_use)=}"
        #     )

    async def _stop_idle_cleaner(self):
        """停止空闲连接清理任务"""
        if self._cleaner_task and not self._cleaner_task.done():
            if self._stop_cleaner:
                self._stop_cleaner.set()
            try:
                await asyncio.wait_for(self._cleaner_task, timeout=5)
            except asyncio.TimeoutError:
                self._cleaner_task.cancel()
            # logger.info("异步空闲连接清理任务已停止")

        # 清空时间戳字典
        if self._connection_last_use_lock:
            async with self._connection_last_use_lock:
                self._connection_last_use.clear()
        else:
            self._connection_last_use.clear()

    async def disconnect(self, inuse_connections: bool = True):
        """断开所有连接，停止清理任务"""
        await self._stop_idle_cleaner()
        await super().disconnect(inuse_connections)


# ============================================================
# Section 5: 连接池获取函数
# ============================================================

def _get_socket_keepalive_options() -> Dict[int, int]:
    """构建 socket keepalive 选项（仅在 Linux 上使用）"""
    socket_keepalive_options = {}
    if hasattr(socket, 'TCP_KEEPIDLE'):
        socket_keepalive_options[socket.TCP_KEEPIDLE] = 1
    if hasattr(socket, 'TCP_KEEPINTVL'):
        socket_keepalive_options[socket.TCP_KEEPINTVL] = 3
    if hasattr(socket, 'TCP_KEEPCNT'):
        socket_keepalive_options[socket.TCP_KEEPCNT] = 5
    return socket_keepalive_options


def get_sync_redis_pool(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 200,
    socket_connect_timeout: int = 30,
    socket_timeout: int = 60,
    timeout: int = 60,
    health_check_interval: int = 30,
    max_idle_time: int = 120,
    idle_check_interval: int = 10,
    **pool_kwargs
) -> IdleTrackingBlockingConnectionPool:
    """
    获取或创建同步 Redis 连接池（全局单例，使用自定义 IdleTrackingBlockingConnectionPool）

    连接池优化策略：
    1. BlockingConnectionPool：连接数达到上限时阻塞等待，避免连接泄漏
    2. health_check_interval：利用 redis-py 内置健康检查，自动清理僵尸连接
    3. TCP Keepalive：通过系统级保活机制检测断开的连接
    4. 无限重试：网络抖动时自动重连，提高可用性
    5. 空闲连接自动回收：跟踪连接真实使用时间，自动关闭长时间空闲的连接

    Args:
        redis_url: Redis 连接 URL
        decode_responses: 是否解码响应为字符串
        max_connections: 连接池最大连接数（默认200）
        socket_connect_timeout: Socket 连接超时（秒），默认30秒
        socket_timeout: Socket 读写超时（秒），默认60秒
        timeout: 等待可用连接的超时时间（秒），默认60秒
        health_check_interval: 健康检查间隔（秒），默认30秒
            - 每次从池中获取连接时，如果距离上次使用超过此时间，会自动发送 PING 检查
            - 设置为 0 禁用健康检查（不推荐）
            - 推荐值：30-60秒，需小于 Redis 服务器 timeout 配置
        max_idle_time: 最大空闲时间（秒），超过此时间的连接将被关闭，默认300秒（5分钟）
            - 设置为 0 禁用空闲连接回收
        idle_check_interval: 空闲检查间隔（秒），默认60秒
        **pool_kwargs: 其他连接池参数

    Returns:
        IdleTrackingBlockingConnectionPool: 带空闲连接自动回收的阻塞连接池

    推荐配置（需与 Redis 服务器配置协同）：
        redis.conf:
            timeout 60              # 服务器端60秒空闲关闭
            tcp-keepalive 30        # 30秒发送一次保活探测

        客户端：
            health_check_interval=30  # < server timeout (60s)
            socket_keepalive=True
            TCP_KEEPIDLE=60          # < server timeout (60s)
            max_idle_time=300        # 5分钟空闲后回收连接
            idle_check_interval=60   # 每分钟检查一次
    """
    # 选择连接池缓存字典
    pool_cache = _sync_redis_pools if decode_responses else _sync_binary_redis_pools

    # 构建缓存键（包含影响连接的关键参数）
    cache_key = redis_url

    if cache_key not in pool_cache:
        socket_keepalive_options = _get_socket_keepalive_options()

        # 创建无限重试实例
        infinite_retry = InfiniteRetry()

        # 使用 IdleTrackingBlockingConnectionPool.from_url 创建连接池
        pool = IdleTrackingBlockingConnectionPool.from_url(
            redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            timeout=timeout,  # BlockingConnectionPool 特有参数：等待连接的超时时间
            retry_on_timeout=True,
            retry_on_error=[ConnectionError, TimeoutError, OSError, BrokenPipeError],
            retry=infinite_retry,  # 使用无限重试策略
            socket_keepalive=True,
            socket_keepalive_options=socket_keepalive_options if socket_keepalive_options else None,
            health_check_interval=health_check_interval,  # 利用 redis-py 内置的健康检查机制
            socket_connect_timeout=socket_connect_timeout,
            socket_timeout=socket_timeout,
            max_idle_time=max_idle_time,  # 空闲连接回收配置
            idle_check_interval=idle_check_interval,
            **pool_kwargs
        )

        pool_cache[cache_key] = pool

        logger.debug(
            f"创建同步Redis阻塞连接池 (max={max_connections}, timeout={timeout}s, "
            f"health_check={health_check_interval}s, max_idle={max_idle_time}s): "
            f"{redis_url}, decode={decode_responses}"
        )

    return pool_cache[cache_key]


def get_async_redis_pool(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 200,
    socket_connect_timeout: int = 30,
    socket_timeout: int = 60,
    socket_keepalive: bool = True,
    health_check_interval: int = 30,
    timeout: int = 60,
    max_idle_time: int = 120,
    idle_check_interval: int = 10,
    **pool_kwargs
) -> AsyncIdleTrackingBlockingConnectionPool:
    """
    获取或创建异步 Redis 连接池（全局单例，使用自定义 AsyncIdleTrackingBlockingConnectionPool）

    连接池优化策略：
    1. BlockingConnectionPool：连接数达到上限时阻塞等待，避免连接泄漏
    2. health_check_interval：利用 redis-py 内置健康检查，自动清理僵尸连接
    3. TCP Keepalive：通过系统级保活机制检测断开的连接
    4. 无限重试：网络抖动时自动重连，提高可用性
    5. 空闲连接自动回收：跟踪连接真实使用时间，自动关闭长时间空闲的连接

    Args:
        redis_url: Redis 连接 URL
        decode_responses: 是否解码响应为字符串
        max_connections: 连接池最大连接数（默认200）
        socket_connect_timeout: Socket 连接超时（秒），默认30秒
        socket_timeout: Socket 读写超时（秒），默认60秒，0表示无限等待
        socket_keepalive: 是否启用 socket keepalive
        health_check_interval: 健康检查间隔（秒），默认30秒（推荐30-60秒）
        timeout: 等待可用连接的超时时间（秒），默认60秒
        max_idle_time: 最大空闲时间（秒），超过此时间的连接将被关闭，默认300秒（5分钟）
            - 设置为 0 禁用空闲连接回收
        idle_check_interval: 空闲检查间隔（秒），默认60秒
        **pool_kwargs: 其他连接池参数

    Returns:
        AsyncIdleTrackingBlockingConnectionPool: 带空闲连接自动回收的异步阻塞连接池
    """
    # 选择连接池缓存字典
    pool_cache = _async_redis_pools if decode_responses else _async_binary_redis_pools

    # 构建缓存键
    cache_key = redis_url

    if cache_key not in pool_cache:
        socket_keepalive_options = _get_socket_keepalive_options()

        # 创建无限重试实例
        infinite_retry = InfiniteRetry()

        # 构建连接池参数
        pool_params = {
            'decode_responses': decode_responses,
            'max_connections': max_connections,
            'retry_on_timeout': True,
            'retry_on_error': [ConnectionError, TimeoutError, OSError, BrokenPipeError],
            'retry': infinite_retry,  # 使用无限重试策略
            'socket_keepalive': socket_keepalive,
            'health_check_interval': health_check_interval,
            'socket_connect_timeout': socket_connect_timeout,
            'max_idle_time': max_idle_time,  # 空闲连接回收配置
            'idle_check_interval': idle_check_interval,
        }

        # 添加 socket_keepalive_options（如果启用）
        if socket_keepalive and socket_keepalive_options:
            pool_params['socket_keepalive_options'] = socket_keepalive_options

        # 添加 socket_timeout（0 表示无限等待）
        if socket_timeout > 0:
            pool_params['socket_timeout'] = socket_timeout

        # 合并其他参数
        pool_params.update(pool_kwargs)

        # 使用 AsyncIdleTrackingBlockingConnectionPool.from_url 创建连接池
        pool = AsyncIdleTrackingBlockingConnectionPool.from_url(
           redis_url,
            **pool_params
        )
        pool_cache[cache_key] = pool

        logger.debug(
            f"创建异步Redis阻塞连接池 (max={max_connections}, timeout={timeout}s, "
            f"health_check={health_check_interval}s, max_idle={max_idle_time}s): "
            f"{redis_url}, decode={decode_responses}"
        )

    return pool_cache[cache_key]


def get_dual_mode_async_redis_client(
    redis_url: str,
    max_connections: int = 200,
    **pool_kwargs
) -> tuple[redis.Redis, redis.Redis]:
    """
    获取双模式异步 Redis 客户端（使用两个独立的连接池）

    核心机制：
    - 创建两个连接池：
      * text_pool: decode_responses=True
      * binary_pool: decode_responses=False
    - 两个连接池使用相同的 max_connections 配置，总共不会超过 max_connections*2
    - 实际使用中，通常只会用到一种模式的池，所以资源浪费很小

    优势：
    - 正确处理文本和二进制数据
    - 两个池独立管理，不会互相干扰
    - 完美解决 Stream 等二进制操作的需求

    Args:
        redis_url: Redis 连接 URL
        max_connections: 每个连接池的最大连接数
        **pool_kwargs: 其他连接池参数

    Returns:
        tuple: (text_client, binary_client)
            - text_client: decode_responses=True，返回字符串
            - binary_client: decode_responses=False，返回字节

    Example:
        >>> text_redis, binary_redis = get_dual_mode_async_redis_client("redis://localhost:6379/0")
        >>> await text_redis.set("key", "value")
        >>> result = await text_redis.get("key")  # str: "value"
        >>> messages = await binary_redis.xreadgroup(...)  # 返回字节数据
    """
    # 创建文本模式连接池（decode=True）
    text_pool = get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=True,
        max_connections=max_connections,
        **pool_kwargs
    )

    # 创建二进制模式连接池（decode=False）
    binary_pool = get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=False,
        max_connections=max_connections,
        **pool_kwargs
    )

    # 创建两个客户端
    text_client = redis.Redis(connection_pool=text_pool)
    binary_client = redis.Redis(connection_pool=binary_pool)

    return text_client, binary_client


def get_async_redis_pool_for_pubsub(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 10,
    health_check_interval: int = 60,
    **pool_kwargs
) -> redis.ConnectionPool:
    """
    获取或创建专门用于 Pub/Sub 的异步 Redis 连接池

    Pub/Sub 是长连接，可能长时间没有消息，因此使用特殊配置：
    - socket_timeout=0 （无限等待，不会因为没有消息而超时）
    - max_connections=10 （Pub/Sub 只需要少量连接）
    - health_check_interval=60 （每60秒主动检查连接健康）

    Args:
        redis_url: Redis 连接 URL
        decode_responses: 是否解码响应为字符串
        max_connections: 连接池最大连接数（默认10，Pub/Sub 不需要很多）
        health_check_interval: 健康检查间隔（秒），默认60秒
        **pool_kwargs: 其他连接池参数

    Returns:
        redis.ConnectionPool: 专门配置的 Pub/Sub 连接池
    """
    return get_async_redis_pool(
        redis_url=redis_url,
        decode_responses=decode_responses,
        max_connections=max_connections,
        socket_connect_timeout=30,
        socket_timeout=0,  # 无限等待！不会因为没有消息而超时
        socket_keepalive=True,
        health_check_interval=health_check_interval,
        **pool_kwargs
    )


def get_pg_engine_and_factory(
    dsn: str,
    pool_size: int = 5,
    max_overflow: int = 10,
    pool_recycle: int = 3600,
    echo: bool = False,
    **engine_kwargs
) -> tuple:
    """
    获取或创建 PostgreSQL 引擎和会话工厂（全局单例）

    Args:
        dsn: PostgreSQL 连接 DSN
        pool_size: 连接池大小
        max_overflow: 连接池溢出大小
        pool_recycle: 连接回收时间（秒）
        echo: 是否打印 SQL 语句
        **engine_kwargs: 其他引擎参数

    Returns:
        tuple: (engine, session_factory)
    """
    if dsn not in _pg_engines:
        # 创建异步引擎
        engine = create_async_engine(
            dsn,
            pool_size=pool_size,
            max_overflow=max_overflow,
            pool_recycle=pool_recycle,
            echo=echo,
            **engine_kwargs
        )

        # 创建会话工厂
        session_factory = async_sessionmaker(
            bind=engine,
            class_=AsyncSession,
            expire_on_commit=False
        )

        _pg_engines[dsn] = engine
        _pg_session_factories[dsn] = session_factory

        logger.debug(f"创建PostgreSQL引擎: {dsn}")

    return _pg_engines[dsn], _pg_session_factories[dsn]


# ============================================================
# Section 6: 配置和连接器类
# ============================================================

class DBConfig:
    """数据库配置基类"""

    @staticmethod
    def parse_redis_config(config: Union[str, Dict[str, Any]]) -> str:
        """
        解析 Redis 配置，统一返回连接 URL

        Args:
            config: 可以是：
                - 字符串: "redis://host:port/db"
                - 字典: {"url": "redis://..."} 或 {"host": ..., "port": ..., "db": ...}

        Returns:
            str: Redis 连接 URL

        Examples:
            >>> DBConfig.parse_redis_config("redis://localhost:6379/0")
            'redis://localhost:6379/0'

            >>> DBConfig.parse_redis_config({"host": "localhost", "port": 6379, "db": 0})
            'redis://localhost:6379/0'

            >>> DBConfig.parse_redis_config({"url": "redis://10.0.0.1:6379/5"})
            'redis://10.0.0.1:6379/5'
        """
        if isinstance(config, str):
            return config

        if isinstance(config, dict):
            # 优先使用 url 字段
            if 'url' in config:
                return config['url']

            # 从分离的配置构建 URL
            host = config.get('host', 'localhost')
            port = config.get('port', 6379)
            db = config.get('db', 0)
            password = config.get('password')

            if password:
                return f"redis://:{password}@{host}:{port}/{db}"
            else:
                return f"redis://{host}:{port}/{db}"

        raise ValueError(f"不支持的 Redis 配置格式: {type(config)}")

    @staticmethod
    def parse_pg_config(config: Union[str, Dict[str, Any]]) -> str:
        """
        解析 PostgreSQL 配置，统一返回 DSN

        Args:
            config: 可以是：
                - 字符串: "postgresql://user:pass@host:port/db"
                - 字典: {"url": "postgresql://..."} 或 {"host": ..., "user": ..., ...}

        Returns:
            str: PostgreSQL DSN (asyncpg 格式)

        Examples:
            >>> DBConfig.parse_pg_config("postgresql://user:pass@localhost/mydb")
            'postgresql+asyncpg://user:pass@localhost/mydb'

            >>> DBConfig.parse_pg_config({
            ...     "host": "localhost",
            ...     "user": "admin",
            ...     "password": "secret",
            ...     "database": "mydb"
            ... })
            'postgresql+asyncpg://admin:secret@localhost:5432/mydb'
        """
        if isinstance(config, str):
            # 确保使用 asyncpg 驱动
            if config.startswith('postgresql://'):
                return config.replace('postgresql://', 'postgresql+asyncpg://', 1)
            elif config.startswith('postgresql+asyncpg://'):
                return config
            else:
                raise ValueError(f"不支持的 PostgreSQL URL 格式: {config}")

        if isinstance(config, dict):
            # 优先使用 url 字段
            if 'url' in config:
                url = config['url']
                if url.startswith('postgresql://'):
                    return url.replace('postgresql://', 'postgresql+asyncpg://', 1)
                return url

            # 从分离的配置构建 DSN
            user = config.get('user', 'postgres')
            password = config.get('password', '')
            host = config.get('host', 'localhost')
            port = config.get('port', 5432)
            database = config.get('database', 'postgres')

            return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"

        raise ValueError(f"不支持的 PostgreSQL 配置格式: {type(config)}")


class SyncRedisConnector:
    """
    同步 Redis 连接管理器（使用全局单例连接池）

    使用示例:
        # 方式1: 直接使用
        connector = SyncRedisConnector("redis://localhost:6379/0")
        client = connector.get_client()
        client.set("key", "value")

        # 方式2: 上下文管理器
        with SyncRedisConnector("redis://localhost:6379/0") as client:
            client.set("key", "value")
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        decode_responses: bool = False,
        max_connections: int = 200,
        **pool_kwargs
    ):
        """
        初始化同步 Redis 连接器

        Args:
            config: Redis 配置（URL 或字典）
            decode_responses: 是否自动解码响应为字符串
            max_connections: 连接池最大连接数
            **pool_kwargs: 其他连接池参数
        """
        self.redis_url = DBConfig.parse_redis_config(config)
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.pool_kwargs = pool_kwargs

        # 使用全局单例连接池
        self._pool: sync_redis.ConnectionPool = get_sync_redis_pool(
            self.redis_url,
            decode_responses=self.decode_responses,
            max_connections=self.max_connections,
            **self.pool_kwargs
        )
        self._client: Optional[sync_redis.Redis] = None
        logger.debug(f"同步 Redis 连接器初始化: {self.redis_url}")

    def get_client(self) -> sync_redis.Redis:
        """
        获取同步 Redis 客户端

        Returns:
            sync_redis.Redis: 同步 Redis 客户端实例
        """
        try:
            return sync_redis.Redis(connection_pool=self._pool)
        except Exception as e:
            logger.error(f"获取同步 Redis 客户端失败: {e}")
            traceback.print_exc()
            raise

    def close(self):
        """关闭客户端（连接池由全局管理，不需要关闭）"""
        # 注意：连接池是全局单例，不需要关闭
        # 只关闭客户端连接
        pass

    def __enter__(self) -> sync_redis.Redis:
        """上下文管理器入口"""
        self._client = self.get_client()
        return self._client

    def __exit__(self, exc_type, exc_val, exc_tb):
        """上下文管理器退出"""
        if self._client:
            self._client.close()
            self._client = None


class RedisConnector:
    """
    异步 Redis 连接管理器（支持双模式，使用全局单例连接池）

    双模式说明：
    - 文本模式（decode_responses=True）：返回字符串，用于普通操作
    - 二进制模式（decode_responses=False）：返回字节，用于 Stream 等需要原始数据的操作

    注意：两个模式使用独立的连接池，但都享受全局单例机制

    使用示例:
        # 方式1: 文本模式（默认）
        connector = RedisConnector("redis://localhost:6379/0")
        client = await connector.get_client()
        await client.set("key", "value")

        # 方式2: 二进制模式
        binary_client = await connector.get_client(binary_mode=True)
        messages = await binary_client.xreadgroup(...)

        # 方式3: 便捷方法
        messages = await connector.xreadgroup_binary(...)
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        decode_responses: bool = True,
        max_connections: int = 200,
        **pool_kwargs
    ):
        """
        初始化 Redis 连接器

        Args:
            config: Redis 配置（URL 或字典）
            decode_responses: 是否自动解码响应为字符串（默认True）
            max_connections: 连接池最大连接数
            **pool_kwargs: 其他连接池参数
        """
        self.redis_url = DBConfig.parse_redis_config(config)
        self.decode_responses = decode_responses
        self.max_connections = max_connections
        self.pool_kwargs = pool_kwargs

        # 延迟创建双模式客户端
        self._text_client: Optional[redis.Redis] = None
        self._binary_client: Optional[redis.Redis] = None
        logger.debug(f"异步 Redis 连接器初始化: {self.redis_url}")

    async def initialize(self):
        """
        初始化连接池（向后兼容）

        注意：连接池已延迟创建，此方法保留用于向后兼容
        """
        pass  # 连接池延迟创建

    async def get_client(self, binary_mode: bool = False) -> redis.Redis:
        """
        获取 Redis 客户端（支持双模式）

        Args:
            binary_mode: 是否使用二进制模式（不自动解码）
                - False（默认）：返回文本客户端（decode_responses=True）
                - True：返回二进制客户端（decode_responses=False）

        Returns:
            redis.Redis: Redis 客户端实例

        Example:
            # 文本模式
            client = await connector.get_client()
            value = await client.get("key")  # 返回 str

            # 二进制模式
            binary_client = await connector.get_client(binary_mode=True)
            messages = await binary_client.xreadgroup(...)  # 返回 bytes
        """
        try:
            # 延迟创建双模式客户端
            if self._text_client is None:
                self._text_client, self._binary_client = get_dual_mode_async_redis_client(
                    redis_url=self.redis_url,
                    max_connections=self.max_connections,
                    **self.pool_kwargs
                )

            return self._binary_client if binary_mode else self._text_client
        except Exception as e:
            logger.error(f"获取 Redis 客户端失败: {e}")
            traceback.print_exc()
            raise

    async def xreadgroup_binary(self, *args, **kwargs):
        """
        便捷方法：使用二进制模式读取 Stream

        这是对 binary_client.xreadgroup() 的封装，避免每次都要指定 binary_mode=True

        Args:
            *args, **kwargs: xreadgroup 的参数

        Returns:
            Stream 消息列表（原始字节数据）

        Example:
            messages = await connector.xreadgroup_binary(
                groupname="mygroup",
                consumername="consumer1",
                streams={"mystream": ">"},
                count=10,
                block=1000
            )
        """
        binary_client = await self.get_client(binary_mode=True)
        return await binary_client.xreadgroup(*args, **kwargs)

    async def xread_binary(self, *args, **kwargs):
        """
        便捷方法：使用二进制模式读取 Stream

        Args:
            *args, **kwargs: xread 的参数

        Returns:
            Stream 消息列表（原始字节数据）
        """
        binary_client = await self.get_client(binary_mode=True)
        return await binary_client.xread(*args, **kwargs)

    async def close(self):
        """关闭客户端（连接池由全局管理，不需要关闭）"""
        # 注意：连接池是全局单例，不需要关闭
        # 只关闭客户端连接
        pass

    async def __aenter__(self) -> redis.Redis:
        """异步上下文管理器入口"""
        await self.initialize()
        self._client = await self.get_client()
        return self._client

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        if self._client:
            await self._client.close()
            self._client = None


class PostgreSQLConnector:
    """
    PostgreSQL 连接管理器（使用全局单例引擎）

    使用示例:
        # 方式1: 直接使用
        connector = PostgreSQLConnector("postgresql://user:pass@localhost/db")
        session = await connector.get_session()

        # 方式2: 上下文管理器
        async with PostgreSQLConnector(config) as session:
            result = await session.execute(select(User))
    """

    def __init__(
        self,
        config: Union[str, Dict[str, Any]],
        pool_size: int = 5,
        max_overflow: int = 10,
        pool_recycle: int = 3600,
        echo: bool = False,
        **engine_kwargs
    ):
        """
        初始化 PostgreSQL 连接器

        Args:
            config: PostgreSQL 配置（DSN 或字典）
            pool_size: 连接池大小
            max_overflow: 连接池溢出大小
            pool_recycle: 连接回收时间（秒）
            echo: 是否打印 SQL 语句
            **engine_kwargs: 其他引擎参数
        """
        self.dsn = DBConfig.parse_pg_config(config)
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_recycle = pool_recycle
        self.echo = echo
        self.engine_kwargs = engine_kwargs

        # 使用全局单例引擎和会话工厂
        self._engine, self._session_factory = get_pg_engine_and_factory(
            self.dsn,
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_recycle=self.pool_recycle,
            echo=self.echo,
            **self.engine_kwargs
        )
        logger.debug(f"PostgreSQL 连接器初始化: {self.dsn}")

    async def initialize(self):
        """初始化数据库引擎和会话工厂（向后兼容）"""
        # 引擎已在 __init__ 中通过全局单例获取
        pass

    async def get_session(self) -> AsyncSession:
        """
        获取数据库会话

        Returns:
            AsyncSession: SQLAlchemy 异步会话

        Raises:
            RuntimeError: 引擎未初始化
        """
        try:
            return self._session_factory()
        except Exception as e:
            logger.error(f"获取 PostgreSQL 会话失败: {e}")
            traceback.print_exc()
            raise

    @asynccontextmanager
    async def session_scope(self):
        """
        会话上下文管理器（自动提交/回滚）

        使用示例:
            async with connector.session_scope() as session:
                user = User(name="Alice")
                session.add(user)
                # 自动提交
        """
        session = await self.get_session()
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

    async def close(self):
        """关闭客户端（引擎由全局管理，不需要关闭）"""
        # 注意：引擎是全局单例，不需要关闭
        pass

    async def __aenter__(self) -> AsyncSession:
        """异步上下文管理器入口"""
        await self.initialize()
        return await self.get_session()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出"""
        # 引擎是全局单例，不需要关闭
        pass


class ConnectionManager:
    """
    连接管理器 - 统一管理 Redis 和 PostgreSQL 连接

    使用示例:
        manager = ConnectionManager(
            redis_config="redis://localhost:6379/0",
            pg_config={"host": "localhost", "user": "admin", "password": "secret", "database": "mydb"}
        )

        # 获取 Redis 客户端
        redis_client = await manager.get_redis_client()

        # 获取 PostgreSQL 会话
        pg_session = await manager.get_pg_session()

        # 关闭所有连接
        await manager.close_all()
    """

    def __init__(
        self,
        redis_config: Optional[Union[str, Dict[str, Any]]] = None,
        pg_config: Optional[Union[str, Dict[str, Any]]] = None,
        redis_decode: bool = True,
        redis_max_connections: int = 50,
        pg_pool_size: int = 5,
        pg_max_overflow: int = 10,
    ):
        """
        初始化连接管理器

        Args:
            redis_config: Redis 配置
            pg_config: PostgreSQL 配置
            redis_decode: Redis 是否解码响应
            redis_max_connections: Redis 最大连接数
            pg_pool_size: PostgreSQL 连接池大小
            pg_max_overflow: PostgreSQL 最大溢出连接数
        """
        self._redis_connector: Optional[RedisConnector] = None
        self._pg_connector: Optional[PostgreSQLConnector] = None

        if redis_config:
            self._redis_connector = RedisConnector(
                redis_config,
                decode_responses=redis_decode,
                max_connections=redis_max_connections
            )

        if pg_config:
            self._pg_connector = PostgreSQLConnector(
                pg_config,
                pool_size=pg_pool_size,
                max_overflow=pg_max_overflow
            )

    async def get_redis_client(self, decode: bool = True) -> redis.Redis:
        """获取 Redis 客户端"""
        if not self._redis_connector:
            raise ValueError("未配置 Redis 连接")

        # 如果需要不同的解码设置，创建新的连接器
        if decode != self._redis_connector.decode_responses:
            temp_connector = RedisConnector(
                self._redis_connector.redis_url,
                decode_responses=decode
            )
            return await temp_connector.get_client()

        return await self._redis_connector.get_client()

    async def get_pg_session(self) -> AsyncSession:
        """获取 PostgreSQL 会话"""
        if not self._pg_connector:
            raise ValueError("未配置 PostgreSQL 连接")

        return await self._pg_connector.get_session()

    @asynccontextmanager
    async def pg_session_scope(self):
        """PostgreSQL 会话上下文（自动提交/回滚）"""
        if not self._pg_connector:
            raise ValueError("未配置 PostgreSQL 连接")

        async with self._pg_connector.session_scope() as session:
            yield session

    async def close_all(self):
        """关闭所有连接"""
        if self._redis_connector:
            await self._redis_connector.close()
        if self._pg_connector:
            await self._pg_connector.close()
        # logger.info("所有数据库连接已关闭")


# 便捷函数

async def create_redis_client(
    config: Union[str, Dict[str, Any]],
    decode_responses: bool = True
) -> redis.Redis:
    """
    快捷创建 Redis 客户端

    Args:
        config: Redis 配置
        decode_responses: 是否解码响应

    Returns:
        redis.Redis: Redis 客户端
    """
    connector = RedisConnector(config, decode_responses=decode_responses)
    return await connector.get_client()


async def create_pg_session(
    config: Union[str, Dict[str, Any]]
) -> AsyncSession:
    """
    快捷创建 PostgreSQL 会话

    Args:
        config: PostgreSQL 配置

    Returns:
        AsyncSession: SQLAlchemy 异步会话
    """
    connector = PostgreSQLConnector(config)
    return await connector.get_session()


# ============================================================
# Section 7: 全局客户端实例管理
# ============================================================

# 兼容旧代码：保持旧的全局变量引用（指向 _PoolRegistry）
_sync_redis_clients = _PoolRegistry.sync_redis_clients
_sync_binary_redis_clients = _PoolRegistry.sync_binary_redis_clients
_async_redis_clients = _PoolRegistry.async_redis_clients
_async_binary_redis_clients = _PoolRegistry.async_binary_redis_clients

def get_sync_redis_client(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 1000,
    **pool_kwargs
) -> sync_redis.StrictRedis:
    """
    获取同步 Redis 客户端实例（全局单例）

    与 get_sync_redis_pool 的区别：
    - get_sync_redis_pool: 返回连接池，需要自己创建客户端
    - get_sync_redis_client: 直接返回可用的客户端实例（推荐使用）

    Args:
        redis_url: Redis 连接 URL
        decode_responses: 是否解码响应为字符串
        max_connections: 连接池最大连接数
        **pool_kwargs: 其他连接池参数

    Returns:
        sync_redis.StrictRedis: 同步 Redis 客户端实例（全局单例）
    """
    # 过滤掉不被 redis 连接池支持的参数
    # 'name' 参数不被 redis.Connection 支持,会导致 TypeError
    pool_kwargs.pop('name', None)

    # 选择客户端缓存
    client_cache = _sync_redis_clients if decode_responses else _sync_binary_redis_clients

    # 构建缓存键
    cache_key = redis_url

    if cache_key not in client_cache:
        # 获取连接池（已经是单例）
        pool = get_sync_redis_pool(
            redis_url=redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            **pool_kwargs
        )

        # 创建客户端实例并缓存
        client_cache[cache_key] = sync_redis.StrictRedis(connection_pool=pool)
        logger.debug(f"创建同步Redis客户端实例: {redis_url}, decode={decode_responses}, PID={os.getpid()}")

    return client_cache[cache_key]


def get_async_redis_client(
    redis_url: str,
    decode_responses: bool = True,
    max_connections: int = 1000,
    socket_timeout: int = 60,
    **pool_kwargs
) -> redis.StrictRedis:
    """
    获取异步 Redis 客户端实例（全局单例）

    Args:
        redis_url: Redis 连接 URL
        decode_responses: 是否解码响应为字符串
        max_connections: 连接池最大连接数
        socket_timeout: Socket 读写超时（秒）
        **pool_kwargs: 其他连接池参数

    Returns:
        redis.StrictRedis: 异步 Redis 客户端实例（全局单例）
    """
    # 过滤掉不被 redis 连接池支持的参数
    # 'name' 参数不被 redis.asyncio.Connection 支持,会导致 TypeError
    pool_kwargs.pop('name', None)

    # 选择客户端缓存
    client_cache = _async_redis_clients if decode_responses else _async_binary_redis_clients

    # 构建缓存键
    cache_key = redis_url

    if cache_key not in client_cache:
        # 获取连接池（已经是单例）
        pool = get_async_redis_pool(
            redis_url=redis_url,
            decode_responses=decode_responses,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            **pool_kwargs
        )

        # 创建客户端实例并缓存
        client_cache[cache_key] = redis.StrictRedis(connection_pool=pool)
        logger.debug(f"创建异步Redis客户端实例: {redis_url}, decode={decode_responses}, PID={os.getpid()}")

    return client_cache[cache_key]


def clear_all_cache():
    """
    清空所有缓存（连接池 + 客户端实例）

    用于子进程fork后彻底重置所有连接

    注意：此函数可能在logging未配置前被调用（如子进程fork后），因此使用print而非logger
    """
    # 使用 _PoolRegistry 统一清空
    _PoolRegistry.clear_all()

    # 使用print而非logger，因为在子进程fork后可能还未配置logging
    # print(f"[PID {os.getpid()}] 清空所有Redis连接池和客户端缓存", flush=True)


__all__ = [
    # 全局连接池函数（保留，向后兼容）
    'get_sync_redis_pool',
    'get_async_redis_pool',
    'get_async_redis_pool_for_pubsub',  # 专门用于 Pub/Sub 的连接池
    'get_pg_engine_and_factory',

    # 客户端实例函数（推荐使用）
    'get_sync_redis_client',
    'get_async_redis_client',

    # 缓存清理
    'clear_all_cache',

    # 配置解析
    'DBConfig',

    # 连接器类（包装全局连接池）
    'SyncRedisConnector',
    'RedisConnector',
    'PostgreSQLConnector',
    'ConnectionManager',

    # 便捷函数
    'create_redis_client',
    'create_pg_session',
]
