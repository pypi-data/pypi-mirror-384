"""
并发限流器

基于Redis锁的并发数限流实现
支持：
1. 并发锁管理
2. 自动锁超时清理
3. Worker下线时的锁释放
"""

import asyncio
import logging
import time
import traceback
import uuid
from redis.asyncio import Redis
from typing import Dict, Optional, Set, List, Tuple
from collections import defaultdict

from jettask.utils.db_connector import get_sync_redis_client

logger = logging.getLogger('app')


class ConcurrencyRateLimiter:
    """并发限流器 - 基于 Redis 的分布式信号量

    使用 Redis 实现分布式信号量，控制全局并发数。
    所有 workers 共享同一个信号量，保证全局并发不超过限制。

    特点：
    - 分布式协调，真正的全局并发控制
    - 使用 Redis 有序集合（Sorted Set）追踪正在运行的任务
    - 自动清理超时任务
    - 支持多进程、多机器部署

    性能优化：
    - 使用 Redis Pub/Sub 代替轮询等待
    - 分离超时清理，避免每次 acquire 都清理
    - 本地缓存减少 Redis 访问
    """

    def __init__(
        self,
        redis_client: Redis,
        task_name: str,
        worker_id: str,
        max_concurrency: int,
        redis_prefix: str = "jettask",
        timeout: float = 5.0,  # 锁超时时间（秒），改为5秒以支持心跳续租
        cleanup_interval: float = 1.0,  # 超时清理间隔（秒），改为1秒更频繁检测
        renewal_interval: float = 1.0  # 心跳续租间隔（秒）
    ):
        """初始化并发限流器（支持心跳续租机制）

        Args:
            redis_client: 异步 Redis 客户端
            task_name: 任务名称
            worker_id: Worker ID
            max_concurrency: 全局最大并发数
            redis_prefix: Redis key 前缀
            timeout: 锁超时时间（秒），默认5秒
            cleanup_interval: 超时清理间隔（秒），默认1秒
            renewal_interval: 心跳续租间隔（秒），默认1秒
        """
        self.redis = redis_client
        self.task_name = task_name
        self.worker_id = worker_id
        self.max_concurrency = max_concurrency
        self.redis_prefix = redis_prefix
        self.timeout = timeout
        self.cleanup_interval = cleanup_interval
        self.renewal_interval = renewal_interval

        # Redis key 定义
        # 使用有序集合存储正在运行的任务，score 为最后更新时间
        self.semaphore_key = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY:{task_name}"
        # Pub/Sub 通道，用于通知有信号量释放
        self.release_channel = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY_RELEASE:{task_name}"

        # Lua 脚本：原子性地获取信号量（优化版，不做清理）
        self.acquire_script = """
            local semaphore_key = KEYS[1]
            local max_concurrency = tonumber(ARGV[1])
            local current_time = tonumber(ARGV[2])
            local task_id = ARGV[3]

            -- 检查当前并发数（不做清理，由后台任务定期清理）
            local current_count = redis.call('ZCARD', semaphore_key)

            if current_count < max_concurrency then
                -- 未达到限制，添加任务
                redis.call('ZADD', semaphore_key, current_time, task_id)
                return 1
            else
                return 0
            end
        """

        # Lua 脚本：释放信号量并通知
        self.release_script = """
            local semaphore_key = KEYS[1]
            local release_channel = KEYS[2]
            local task_id = ARGV[1]

            -- 移除任务
            local removed = redis.call('ZREM', semaphore_key, task_id)

            -- 如果成功移除，通知等待者
            if removed > 0 then
                redis.call('PUBLISH', release_channel, '1')
            end

            return removed
        """

        # Lua 脚本：清理超时任务
        self.cleanup_script = """
            local semaphore_key = KEYS[1]
            local release_channel = KEYS[2]
            local timeout_threshold = tonumber(ARGV[1])

            -- 清理超时任务
            local removed = redis.call('ZREMRANGEBYSCORE', semaphore_key, '-inf', timeout_threshold)

            -- 如果清理了任务，通知等待者
            if removed > 0 then
                redis.call('PUBLISH', release_channel, tostring(removed))
            end

            return removed
        """

        # Lua 脚本：续租（更新时间戳）
        self.renewal_script = """
            local semaphore_key = KEYS[1]
            local task_id = ARGV[1]
            local current_time = tonumber(ARGV[2])

            -- 检查任务是否存在
            local exists = redis.call('ZSCORE', semaphore_key, task_id)
            if exists then
                -- 更新时间戳
                redis.call('ZADD', semaphore_key, current_time, task_id)
                return 1
            else
                return 0
            end
        """

        # 无锁设计：
        # - _local_tasks: set 操作通过 GIL 保护，在单个 worker 内线程安全
        # - 所有状态变更都是原子的，不需要显式锁
        self._local_tasks = set()  # 本地追踪当前 worker 获取的任务 ID（正在运行的任务）
        # 已移除 _renewal_tasks，改用统一的心跳管理器
        self._unified_heartbeat_task = None  # 统一的心跳协程
        self._cleanup_task = None  # 后台清理任务
        self._pubsub = None  # Pub/Sub 订阅
        self._pubsub_listener_task = None  # Pub/Sub 监听协程
        self._periodic_trigger_task = None  # 定时触发协程
        self._release_event = asyncio.Event()  # 释放事件，用于通知等待者
        self._poll_interval = 10.0  # 定时触发间隔（秒）

    def _trigger_release_signal(self):
        """触发释放信号，唤醒所有等待者"""
        self._release_event.set()
        # 立即清除事件，为下次通知做准备
        self._release_event.clear()

    async def _pubsub_listener(self):
        """Pub/Sub 监听协程：持续监听释放通知并触发信号"""
        try:
            logger.debug(f"[CONCURRENCY] Pub/Sub listener started for {self.release_channel}")
            async for message in self._pubsub.listen():
                # 忽略订阅确认消息
                if message['type'] == 'message':
                    logger.debug(f"[CONCURRENCY] Received Pub/Sub release notification, triggering signal")
                    self._trigger_release_signal()
        except asyncio.CancelledError:
            logger.debug(f"[CONCURRENCY] Pub/Sub listener cancelled")
            raise
        except Exception as e:
            logger.error(f"[CONCURRENCY] Error in Pub/Sub listener: {e}")

    async def _periodic_trigger(self):
        """定时触发协程：定期触发信号作为兜底机制"""
        try:
            logger.debug(f"[CONCURRENCY] Periodic trigger started, interval={self._poll_interval}s")
            while True:
                await asyncio.sleep(self._poll_interval)
                logger.debug(f"[CONCURRENCY] Periodic trigger firing, triggering signal")
                self._trigger_release_signal()
        except asyncio.CancelledError:
            logger.debug(f"[CONCURRENCY] Periodic trigger cancelled")
            raise
        except Exception as e:
            logger.error(f"[CONCURRENCY] Error in periodic trigger: {e}")

    async def _unified_heartbeat_manager(self):
        """统一的心跳管理器：定期为所有正在运行的任务更新时间戳（无锁设计）

        这个协程会定期扫描 _local_tasks 集合，批量更新所有任务的心跳
        """
        try:
            logger.debug(f"[CONCURRENCY] Unified heartbeat manager started, interval={self.renewal_interval}s")
            while True:
                await asyncio.sleep(self.renewal_interval)

                # 获取当前所有任务的快照（set 是线程安全的）
                if not self._local_tasks:
                    # 没有任务，继续等待
                    continue

                # 批量更新所有任务的心跳（使用 Pipeline 减少网络往返）
                current_time = time.time()
                tasks_snapshot = list(self._local_tasks)  # 复制一份避免迭代时修改

                logger.debug(f"[CONCURRENCY] Renewing heartbeat for {len(tasks_snapshot)} tasks")

                try:
                    # 使用 Pipeline 批量执行所有续租操作
                    pipe = self.redis.pipeline()
                    for task_id in tasks_snapshot:
                        pipe.eval(
                            self.renewal_script,
                            1,
                            self.semaphore_key,
                            task_id,
                            current_time
                        )

                    # 一次性执行所有命令
                    results = await pipe.execute()

                    # 处理结果
                    for task_id, result in zip(tasks_snapshot, results):
                        if result == 0:
                            # 任务已被清理（可能是超时），从本地集合移除
                            logger.warning(f"[CONCURRENCY] Task {task_id} was cleaned up, removing from local tasks")
                            self._local_tasks.discard(task_id)
                        else:
                            logger.debug(f"[CONCURRENCY] Renewed lease for task {task_id}")

                except Exception as e:
                    logger.error(f"[CONCURRENCY] Error renewing leases in batch: {e}")
                    # Pipeline 失败，降级为逐个更新
                    for task_id in tasks_snapshot:
                        try:
                            result = await self.redis.eval(
                                self.renewal_script,
                                1,
                                self.semaphore_key,
                                task_id,
                                current_time
                            )
                            if result == 0:
                                logger.warning(f"[CONCURRENCY] Task {task_id} was cleaned up, removing from local tasks")
                                self._local_tasks.discard(task_id)
                        except Exception as e2:
                            logger.error(f"[CONCURRENCY] Error renewing lease for {task_id}: {e2}")

        except asyncio.CancelledError:
            logger.debug(f"[CONCURRENCY] Unified heartbeat manager cancelled")
            raise

    async def _ensure_pubsub(self):
        """确保 Pub/Sub 订阅和后台协程已启动"""
        if self._pubsub is None:
            # 订阅 Pub/Sub 频道
            self._pubsub = self.redis.pubsub()
            await self._pubsub.subscribe(self.release_channel)
            logger.debug(f"[CONCURRENCY] Subscribed to channel {self.release_channel}")

            # 启动 Pub/Sub 监听协程
            if self._pubsub_listener_task is None:
                self._pubsub_listener_task = asyncio.create_task(self._pubsub_listener())
                logger.debug(f"[CONCURRENCY] Pub/Sub listener task started")

            # 启动定时触发协程
            if self._periodic_trigger_task is None:
                self._periodic_trigger_task = asyncio.create_task(self._periodic_trigger())
                logger.debug(f"[CONCURRENCY] Periodic trigger task started")

            # 启动统一心跳管理器
            if self._unified_heartbeat_task is None:
                self._unified_heartbeat_task = asyncio.create_task(self._unified_heartbeat_manager())
                logger.debug(f"[CONCURRENCY] Unified heartbeat manager started")

            # 启动定期清理任务
            if self._cleanup_task is None:
                self._cleanup_task = asyncio.create_task(self._periodic_cleanup())
                logger.debug(f"[CONCURRENCY] Periodic cleanup task started")

    async def _try_acquire_slot(self, task_id: str) -> bool:
        """尝试获取一个执行许可槽位

        Args:
            task_id: 任务ID

        Returns:
            成功返回 True，失败返回 False
        """
        try:
            # 执行 Lua 脚本尝试获取
            result = await self.redis.eval(
                self.acquire_script,
                1,
                self.semaphore_key,
                self.max_concurrency,
                time.time(),
                task_id
            )

            if result == 1:
                logger.debug(f"[CONCURRENCY] Acquired slot for task_id={task_id}")
                # 成功获取，添加到正在运行的任务集合（无锁操作）
                # set.add() 在 Python 中是原子操作（GIL保护）
                # 统一的心跳管理器会自动为这个任务续租
                self._local_tasks.add(task_id)

                # 确保统一心跳管理器已启动
                if self._unified_heartbeat_task is None:
                    self._unified_heartbeat_task = asyncio.create_task(self._unified_heartbeat_manager())
                    logger.debug(f"[CONCURRENCY] Unified heartbeat manager started on first acquire")

                return True
            else:
                return False

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error in _try_acquire_slot: {e}")
            return False

    async def _periodic_cleanup(self):
        """定期清理超时任务的后台协程"""
        try:
            logger.debug(f"[CONCURRENCY] Periodic cleanup task started, interval={self.cleanup_interval}s")
            while True:
                await asyncio.sleep(self.cleanup_interval)

                current_time = time.time()
                timeout_threshold = current_time - self.timeout
                try:
                    removed = await self.redis.eval(
                        self.cleanup_script,
                        2,  # 2 个 keys
                        self.semaphore_key,
                        self.release_channel,
                        timeout_threshold
                    )
                    if removed > 0:
                        logger.info(f"[CONCURRENCY] Cleaned up {removed} timeout tasks")
                except Exception as e:
                    logger.error(f"[CONCURRENCY] Cleanup error: {e}")
        except asyncio.CancelledError:
            logger.debug(f"[CONCURRENCY] Periodic cleanup task cancelled")
            raise
        except Exception as e:
            logger.error(f"[CONCURRENCY] Error in periodic cleanup: {e}")

    async def acquire(self, timeout: float = 10.0) -> Optional[str]:
        """获取一个执行许可（优化版，使用 Pub/Sub + 定时触发）

        Args:
            timeout: 等待超时时间（秒）

        Returns:
            成功获取返回 task_id，超时返回 None
        """
        start_time = time.time()
        task_id = f"{self.worker_id}:{uuid.uuid4().hex}"

        logger.debug(f"[CONCURRENCY] Attempting to acquire, task_id={task_id}")
        # 首次尝试直接获取
        if await self._try_acquire_slot(task_id):
            logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Acquired immediately, task_id={task_id}, current_concurrency={len(self._local_tasks)}")
            return task_id

        # 如果首次失败，启动后台协程并等待信号
        await self._ensure_pubsub()

        while True:
            # 检查超时
            logger.debug(f"[CONCURRENCY] Waiting to acquire, task_id={task_id}")
            elapsed = time.time() - start_time
            if timeout is not None and elapsed >= timeout:
                logger.warning(f"[CONCURRENCY] Acquire timeout after {timeout}s")
                return None

            # 等待内部信号（由 Pub/Sub 监听协程或定时触发协程触发）
            try:
                # 计算剩余超时时间
                if timeout is not None:
                    remaining = timeout - elapsed
                    await asyncio.wait_for(self._release_event.wait(), timeout=remaining)
                else:
                    # 无超时限制，纯等待信号
                    await self._release_event.wait()

                logger.debug(f"[CONCURRENCY] Received signal, attempting acquire for task_id={task_id}")

            except asyncio.TimeoutError:
                # 达到用户指定的超时时间
                logger.warning(f"[CONCURRENCY] Acquire timeout after {timeout}s")
                return None

            # 收到信号，尝试获取槽位
            if await self._try_acquire_slot(task_id):
                logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Acquired after wait, task_id={task_id}, current_concurrency={len(self._local_tasks)}")
                return task_id
            else:
                # 获取失败（可能被其他任务抢占），继续等待下一个信号
                logger.debug(f"[CONCURRENCY] Acquire failed (slot taken by others), waiting for next signal")

    async def try_acquire(self) -> bool:
        """尝试获取执行许可（非阻塞）

        Returns:
            成功获取返回 True，失败返回 False
        """
        task_id = f"{self.worker_id}:{uuid.uuid4().hex}"

        if await self._try_acquire_slot(task_id):
            logger.debug(f"[CONCURRENCY] Try acquired, task_id={task_id}")
            return True
        else:
            logger.debug(f"[CONCURRENCY] Try acquire failed, no available slot")
            return False

    async def release(self, task_id: str):
        """释放一个执行许可（无锁设计，通知等待者）

        Args:
            task_id: 要释放的任务ID（由 acquire() 返回）
        """
        # 从本地集合移除（set.discard 是原子操作，且不会抛异常）
        # 统一的心跳管理器会自动停止为这个任务续租
        self._local_tasks.discard(task_id)

        try:
            # 执行 Lua 脚本，释放信号量并通知
            result = await self.redis.eval(
                self.release_script,
                2,  # 2 个 keys
                self.semaphore_key,
                self.release_channel,
                task_id
            )

            logger.debug(f"[WORKER:{self.worker_id}] [CONCURRENCY] Released semaphore, task_id={task_id}, remaining_concurrency={len(self._local_tasks)}")

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error releasing semaphore: {e}")

    async def update_limit(self, new_limit: int):
        """动态更新并发限制

        Args:
            new_limit: 新的并发限制
        """
        if self.max_concurrency != new_limit:
            old_limit = self.max_concurrency
            self.max_concurrency = new_limit
            logger.debug(
                f"[WORKER:{self.worker_id}] [CONCURRENCY] Limit changed: {old_limit} → {new_limit}"
            )

    async def get_stats(self) -> dict:
        """获取统计信息"""
        try:
            # 清理超时任务
            timeout_threshold = time.time() - self.timeout
            await self.redis.zremrangebyscore(
                self.semaphore_key,
                '-inf',
                timeout_threshold
            )

            # 获取当前并发数
            current_count = await self.redis.zcard(self.semaphore_key)

            return {
                'mode': 'concurrency',
                'concurrency_limit': self.max_concurrency,
                'current_concurrency': current_count,
                'local_tasks': len(self._local_tasks),
            }

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error getting stats: {e}")
            return {
                'mode': 'concurrency',
                'concurrency_limit': self.max_concurrency,
                'current_concurrency': 0,
                'local_tasks': len(self._local_tasks),
            }

    async def stop(self):
        """停止并清理资源"""
        try:
            # 取消统一心跳管理器
            if self._unified_heartbeat_task is not None:
                self._unified_heartbeat_task.cancel()
                try:
                    await self._unified_heartbeat_task
                except asyncio.CancelledError:
                    pass
                self._unified_heartbeat_task = None
                logger.debug(f"[CONCURRENCY] Unified heartbeat manager cancelled")

            # 取消 Pub/Sub 监听协程
            if self._pubsub_listener_task is not None:
                self._pubsub_listener_task.cancel()
                try:
                    await self._pubsub_listener_task
                except asyncio.CancelledError:
                    pass
                self._pubsub_listener_task = None
                logger.debug(f"[CONCURRENCY] Pub/Sub listener task cancelled")

            # 取消定时触发协程
            if self._periodic_trigger_task is not None:
                self._periodic_trigger_task.cancel()
                try:
                    await self._periodic_trigger_task
                except asyncio.CancelledError:
                    pass
                self._periodic_trigger_task = None
                logger.debug(f"[CONCURRENCY] Periodic trigger task cancelled")

            # 清理 Pub/Sub 订阅
            if self._pubsub is not None:
                await self._pubsub.unsubscribe(self.release_channel)
                await self._pubsub.close()
                self._pubsub = None
                logger.debug(f"[CONCURRENCY] Cleaned up pubsub for {self.task_name}")

            # 清理本地追踪的任务（从 Redis 中移除）
            if self._local_tasks:
                for task_id in list(self._local_tasks):
                    try:
                        await self.redis.zrem(self.semaphore_key, task_id)
                    except Exception as e:
                        logger.error(f"[CONCURRENCY] Error removing task {task_id}: {e}")
                self._local_tasks.clear()
                logger.debug(f"[CONCURRENCY] Cleaned up local tasks for {self.task_name}")

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error during stop: {e}")

    async def __aenter__(self):
        """异步上下文管理器入口 - 获取执行许可

        使用示例:
            async with limiter:
                # 执行任务
                await do_something()

        Returns:
            self: 限流器实例
        """
        task_id = await self.acquire()
        if task_id is None:
            raise TimeoutError("Failed to acquire concurrency slot")
        # 保存task_id供__aexit__使用
        self._current_task_id = task_id
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出 - 自动释放许可"""
        if hasattr(self, '_current_task_id'):
            await self.release(self._current_task_id)
            delattr(self, '_current_task_id')
        return False  # 不抑制异常

    @classmethod
    def cleanup_worker_locks(cls, redis_url: str, redis_prefix: str, worker_id: str = None, task_names: list = None):
        """
        清理指定worker的并发锁（同步方法，用于进程退出时）

        Args:
            redis_url: Redis连接URL
            redis_prefix: Redis key前缀
            worker_id: Worker ID（如果提供，精确清理该worker的锁；否则清理过期锁）
            task_names: 任务名称列表（如果提供，只清理这些任务的锁；否则无法清理）

        Returns:
            清理的锁数量

        注意：
            如果没有提供 task_names，方法将无法清理锁。
            调用者需要维护任务名称列表以便进行清理。
        """
        try:
            if not task_names:
                logger.warning(f"[CONCURRENCY] No task_names provided, cannot cleanup locks. Please provide task_names.")
                return 0

            # 使用全局单例获取同步 Redis 客户端
            sync_redis = get_sync_redis_client(redis_url, decode_responses=False)
            try:
                total_cleaned = 0

                # 遍历所有提供的任务名称
                for task_name in task_names:
                    key = f"{redis_prefix}:RATE_LIMIT:CONCURRENCY:{task_name}"

                    # 检查 key 是否存在
                    if not sync_redis.exists(key):
                        continue

                    # 如果知道worker_id，精确清理该worker的锁
                    if worker_id:
                        try:
                            # 获取所有成员
                            all_members = sync_redis.zrange(key, 0, -1)
                            to_remove = []
                            for member in all_members:
                                # task_id格式: worker_id:uuid
                                if isinstance(member, bytes):
                                    member_str = member.decode('utf-8')
                                else:
                                    member_str = member

                                # 检查是否属于当前worker
                                if member_str.startswith(worker_id + ':'):
                                    to_remove.append(member)

                            if to_remove:
                                removed = sync_redis.zrem(key, *to_remove)
                                total_cleaned += removed
                                logger.debug(f"[CONCURRENCY] Cleaned up {removed} locks for worker {worker_id} from {key}")
                        except Exception as e:
                            logger.error(f"[CONCURRENCY] Error cleaning {key}: {e}")
                    else:
                        # 如果不知道worker_id，清理所有超过5秒的锁
                        try:
                            current_time = __import__('time').time()
                            # 清理5秒前的所有task
                            timeout_threshold = current_time - 5
                            removed = sync_redis.zremrangebyscore(key, '-inf', timeout_threshold)
                            if removed > 0:
                                total_cleaned += removed
                                logger.debug(f"[CONCURRENCY] Cleaned up {removed} stale locks from {key}")
                        except Exception as e:
                            logger.error(f"[CONCURRENCY] Error cleaning {key}: {e}")

                logger.debug(f"[CONCURRENCY] Cleanup completed, total cleaned: {total_cleaned}")
                return total_cleaned
            finally:
                # 关闭客户端连接
                sync_redis.close()

        except Exception as e:
            logger.error(f"[CONCURRENCY] Error during cleanup_worker_locks: {e}")
            return 0


# ============================================================
# 统一的任务限流器
# ============================================================



__all__ = ['ConcurrencyRateLimiter']
