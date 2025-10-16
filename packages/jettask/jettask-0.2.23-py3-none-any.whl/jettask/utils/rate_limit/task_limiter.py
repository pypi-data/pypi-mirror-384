"""
任务级限流器

组合QPS和并发限流，提供统一的任务级限流接口
"""

import asyncio
import logging
import time
from redis.asyncio import Redis
from typing import Dict, Optional, List, Tuple, Any

from .qps_limiter import QPSRateLimiter
from .concurrency_limiter import ConcurrencyRateLimiter
from .config import RateLimitConfig, QPSLimit, ConcurrencyLimit, parse_rate_limit_config

logger = logging.getLogger('app')


class TaskRateLimiter:
    """任务级别的限流器

    根据配置类型自动选择合适的限流器实现：
    - QPSLimit: 使用本地滑动窗口 + Redis 协调配额
    - ConcurrencyLimit: 使用 Redis 分布式信号量
    """

    def __init__(
        self,
        redis_client: Redis,
        task_name: str,
        worker_id: str,
        config: RateLimitConfig,
        redis_prefix: str = "jettask",
        sync_interval: float = 5.0,
        registry_manager = None,
        worker_state_manager = None
    ):
        """初始化任务限流器

        Args:
            redis_client: 异步 Redis 客户端
            task_name: 任务名称
            worker_id: 当前 worker ID
            config: 限流配置（QPSLimit 或 ConcurrencyLimit）
            redis_prefix: Redis key 前缀
            sync_interval: 配额同步间隔（秒），仅用于 QPS 限流
            registry_manager: RegistryManager 实例
            worker_state_manager: WorkerStateManager 实例
        """
        self.redis = redis_client
        self.task_name = task_name
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.global_config = config
        self.sync_interval = sync_interval
        self.registry_manager = registry_manager
        self.worker_state_manager = worker_state_manager

        # Redis key 定义
        self.rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"

        # 根据配置类型创建具体的限流器
        if isinstance(config, QPSLimit):
            self.limiter = QPSRateLimiter(
                qps=config.qps,
                window_size=config.window_size,
                worker_id=worker_id
            )
            self.mode = 'qps'
            # QPS 模式需要配额同步
            self._sync_task: Optional[asyncio.Task] = None
            self._running = False
        elif isinstance(config, ConcurrencyLimit):
            self.limiter = ConcurrencyRateLimiter(
                redis_client=redis_client,
                task_name=task_name,
                worker_id=worker_id,
                max_concurrency=config.max_concurrency,
                redis_prefix=redis_prefix
            )
            self.mode = 'concurrency'
            # 并发模式不需要配额同步（分布式信号量自动协调）
            self._sync_task = None
            self._running = False
        else:
            raise ValueError(f"Unsupported config type: {type(config)}")

        # 统计信息
        self.stats = {
            'syncs': 0,
            'last_sync_time': 0,
            'current_worker_count': 0,
        }

    async def start(self):
        """启动限流器"""
        if self._running:
            logger.warning(f"TaskRateLimiter for {self.task_name} already running")
            return

        logger.debug(
            f"Starting TaskRateLimiter for task={self.task_name}, "
            f"config={self.global_config}, mode={self.mode}"
        )

        # 初始化 Redis 配置
        await self._initialize_redis()

        # 只有 QPS 模式需要启动配额同步
        if self.mode == 'qps':
            self._running = True
            self._sync_task = asyncio.create_task(self._sync_loop())

            # 注册 worker 状态变更回调
            if self.worker_state_manager:
                self.worker_state_manager.register_callback(self._on_worker_state_change)
                logger.debug(f"Registered worker state change listener for {self.task_name}")

        logger.debug(f"TaskRateLimiter started for {self.task_name}")
    def __delattr__(self, name):
        self.stop()
        
    async def stop(self):
        """停止限流器"""
        
        print(f'准备退出限流器 {self.task_name} {self.mode}')
        if not self._running and self.mode == 'qps':
            return

        logger.debug(f"Stopping TaskRateLimiter for {self.task_name}")

        if self.mode == 'qps':
            self._running = False

            # 注销状态变更回调
            if self.worker_state_manager:
                self.worker_state_manager.unregister_callback(self._on_worker_state_change)

            # 取消后台任务
            if self._sync_task:
                self._sync_task.cancel()
                try:
                    await self._sync_task
                except asyncio.CancelledError:
                    pass
        elif self.mode == 'concurrency':
            # 清理并发限流器（释放所有持有的锁）
            if hasattr(self.limiter, 'stop'):
                try:
                    await self.limiter.stop()
                    logger.debug(f"Concurrency limiter stopped and locks released for {self.task_name}")
                except Exception as e:
                    logger.error(f"Error stopping concurrency limiter for {self.task_name}: {e}")

        logger.debug(f"TaskRateLimiter stopped for {self.task_name}")

    async def _initialize_redis(self):
        """初始化 Redis 配置"""
        try:
            exists = await self.redis.exists(self.rate_limit_key)
            if not exists:
                config_dict = self.global_config.to_dict()
                await self.redis.hset(self.rate_limit_key, mapping=config_dict)
                logger.debug(
                    f"Initialized rate limit config for {self.task_name}: {self.global_config}"
                )

            # 将任务名添加到索引集合中（用于避免 scan 操作）
            index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
            await self.redis.sadd(index_key, self.task_name)
            logger.debug(f"Added {self.task_name} to rate limit index")

        except Exception as e:
            logger.error(f"Failed to initialize Redis: {e}")

    async def _on_worker_state_change(self, state_data: dict):
        """Worker 状态变更回调（仅用于 QPS 模式）"""
        if self.mode == 'qps':
            logger.debug(f"[{self.task_name}] Worker state changed: {state_data}")
            await self._sync_quota()

    async def _sync_quota(self):
        """同步配额（仅用于 QPS 模式）"""
        if self.mode != 'qps':
            return

        try:
            # 1. 从 Redis 读取全局配置
            config_dict = await self.redis.hgetall(self.rate_limit_key)
            if not config_dict:
                logger.warning(f"No config found in Redis for {self.task_name}")
                return

            # 转换 bytes 为 str
            config_dict = {
                k.decode() if isinstance(k, bytes) else k:
                v.decode() if isinstance(v, bytes) else v
                for k, v in config_dict.items()
            }

            # 解析配置
            global_config = parse_rate_limit_config(config_dict)
            if not isinstance(global_config, QPSLimit):
                logger.error(f"Invalid QPS config for {self.task_name}: {config_dict}")
                return

            # 2. 获取当前活跃的 workers
            worker_ids = [self.worker_id]
            if self.registry_manager and hasattr(self.registry_manager, 'get_workers_for_task'):
                try:
                    workers = await self.registry_manager.get_workers_for_task(self.task_name, only_alive=True)
                    if workers:
                        worker_ids = sorted(list(workers))
                except Exception as e:
                    logger.debug(f"Failed to get workers from registry: {e}")
                    # 降级到只使用当前 worker

            worker_count = len(worker_ids)

            # 3. 协商配额分配
            await self._allocate_quotas(global_config.qps, worker_ids)

            # 4. 读取当前 worker 的配额
            quota_key = f"quota:{self.worker_id}"
            quota_str = await self.redis.hget(self.rate_limit_key, quota_key)

            if quota_str:
                quota_value = int(quota_str)
            else:
                # 降级方案：平均分配
                quota_value = global_config.qps // worker_count if worker_count > 0 else global_config.qps

            # 5. 更新本地限流器的配额
            await self.limiter.update_limit(quota_value)

            # 6. 更新统计信息
            self.stats['syncs'] += 1
            self.stats['last_sync_time'] = time.time()
            self.stats['current_worker_count'] = worker_count

        except Exception as e:
            logger.error(f"Quota sync error: {e}")

    async def _sync_loop(self):
        """后台同步循环（仅用于 QPS 模式）"""
        while self._running:
            try:
                await self._sync_quota()
                await asyncio.sleep(self.sync_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Sync loop error: {e}")
                await asyncio.sleep(1)

    async def _allocate_quotas(self, total_qps: int, worker_ids: list):
        """协商配额分配（仅用于 QPS 模式）"""
        lock_key = f"{self.rate_limit_key}:lock"

        try:
            async with self.redis.lock(lock_key, timeout=3, blocking_timeout=2):
                worker_count = len(worker_ids)
                base_quota = total_qps // worker_count
                remainder = total_qps % worker_count

                # 分配配额
                allocations = {}
                for i, worker_id in enumerate(worker_ids):
                    quota = base_quota + (1 if i < remainder else 0)
                    allocations[f"quota:{worker_id}"] = quota

                # 批量写入 Redis
                if allocations:
                    await self.redis.hset(self.rate_limit_key, mapping=allocations)

                # 清理不活跃 workers 的配额
                await self._cleanup_stale_quotas(worker_ids)

                logger.debug(f"[ALLOCATE] Allocated quotas for {worker_count} workers: {allocations}")

        except asyncio.TimeoutError:
            logger.debug(f"[ALLOCATE] Failed to acquire lock, skipping allocation")
        except Exception as e:
            logger.error(f"[ALLOCATE] Error allocating quotas: {e}")

    async def _cleanup_stale_quotas(self, active_worker_ids: list):
        """清理不活跃 workers 的配额"""
        try:
            all_fields = await self.redis.hkeys(self.rate_limit_key)
            active_quota_keys = {f"quota:{wid}" for wid in active_worker_ids}

            to_delete = []
            for field in all_fields:
                if isinstance(field, bytes):
                    field = field.decode('utf-8')

                if field.startswith("quota:") and field not in active_quota_keys:
                    to_delete.append(field)

            if to_delete:
                await self.redis.hdel(self.rate_limit_key, *to_delete)
                logger.debug(f"[CLEANUP] Removed {len(to_delete)} stale quotas")

        except Exception as e:
            logger.error(f"[CLEANUP] Error cleaning up quotas: {e}")

    async def acquire(self, timeout: float = 10.0) -> Optional[str]:
        """获取执行许可

        Returns:
            成功返回 task_id (ConcurrencyLimit) 或 True (QPSLimit)，失败返回 None
        """
        result = await self.limiter.acquire(timeout=timeout)
        # QPSLimit 返回 bool，ConcurrencyLimit 返回 task_id 或 None
        if self.mode == 'qps':
            return True if result else None
        else:
            return result  # ConcurrencyLimit 直接返回 task_id 或 None

    async def release(self, task_id: Optional[str] = None):
        """释放执行许可

        Args:
            task_id: 任务ID (仅 ConcurrencyLimit 需要)
        """
        if self.mode == 'concurrency' and task_id is None:
            raise ValueError("ConcurrencyLimit requires task_id for release")

        if self.mode == 'concurrency':
            await self.limiter.release(task_id)
        else:
            # QPSLimit 不需要 release（本地计数）
            pass

    async def try_acquire(self) -> bool:
        """尝试获取执行许可（非阻塞）"""
        return await self.limiter.try_acquire()

    def get_stats(self) -> dict:
        """获取统计信息"""
        return {
            **self.stats,
            'task_name': self.task_name,
            'worker_id': self.worker_id,
            'config': str(self.global_config),
        }

    async def __aenter__(self):
        """异步上下文管理器入口 - 获取执行许可

        使用示例:
            async with rate_limiter:
                # 执行任务
                await do_something()

        Returns:
            self: 限流器实例
        """
        task_id = await self.acquire()
        if task_id is None:
            raise TimeoutError("Failed to acquire rate limit slot")
        # 保存task_id供__aexit__使用
        self._current_task_id = task_id
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器退出 - 自动释放许可"""
        if hasattr(self, '_current_task_id'):
            task_id = self._current_task_id
            delattr(self, '_current_task_id')
            if self.mode == 'concurrency':
                await self.release(task_id)
            # QPSLimit 不需要显式 release
        return False  # 不抑制异常


# ============================================================
# 限流器管理器
# ============================================================



__all__ = ['TaskRateLimiter']
