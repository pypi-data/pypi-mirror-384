"""
限流器管理器

统一管理所有任务的限流器实例
职责：
1. 限流器生命周期管理
2. 配置动态更新
3. 统一的限流接口
"""

import asyncio
import logging
import time
from redis.asyncio import Redis
from typing import Dict, Optional, List, Any

from .task_limiter import TaskRateLimiter
from .config import RateLimitConfig, parse_rate_limit_config

logger = logging.getLogger('app')


class RateLimiterManager:
    """限流器管理器

    管理多个任务的限流器。
    """

    def __init__(
        self,
        redis_client: Redis,
        worker_id: str,
        redis_prefix: str = "jettask",
        registry_manager = None,
        worker_state_manager = None
    ):
        """初始化限流器管理器

        Args:
            redis_client: 异步 Redis 客户端
            worker_id: 当前 worker ID
            redis_prefix: Redis key 前缀
            registry_manager: RegistryManager 实例
            worker_state_manager: WorkerStateManager 实例
        """
        self.redis = redis_client
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.registry_manager = registry_manager
        self.worker_state_manager = worker_state_manager

        # 任务名 -> 限流器映射
        self.limiters: Dict[str, TaskRateLimiter] = {}

        logger.debug(f"RateLimiterManager initialized for worker {worker_id}")

    @staticmethod
    def register_rate_limit_config(redis_client, task_name: str, config: RateLimitConfig, redis_prefix: str = "jettask"):
        """注册任务的限流配置到 Redis（同步方法）

        Args:
            redis_client: 同步 Redis 客户端
            task_name: 任务名称
            config: RateLimitConfig 对象（ConcurrencyLimit 或 QPSLimit）
            redis_prefix: Redis key 前缀
        """
        try:
            rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
            # 将配置对象转换为字典并保存到 Redis
            config_dict = config.to_dict()
            redis_client.hset(rate_limit_key, mapping=config_dict)

            # 将任务名添加到索引集合中（用于避免 scan 操作）
            index_key = f"{redis_prefix}:RATE_LIMIT:INDEX"
            redis_client.sadd(index_key, task_name)

            logger.debug(f"Registered rate limit config for task '{task_name}': {config}")
        except Exception as e:
            logger.error(f"Failed to register rate limit config for task '{task_name}': {e}")

    @staticmethod
    def unregister_rate_limit_config(redis_client, task_name: str, redis_prefix: str = "jettask"):
        """从 Redis 中删除任务的限流配置（同步方法）

        Args:
            redis_client: 同步 Redis 客户端
            task_name: 任务名称
            redis_prefix: Redis key 前缀

        Returns:
            是否成功删除
        """
        try:
            rate_limit_key = f"{redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
            deleted = redis_client.delete(rate_limit_key)

            if deleted:
                # 从索引集合中移除
                index_key = f"{redis_prefix}:RATE_LIMIT:INDEX"
                redis_client.srem(index_key, task_name)
                logger.debug(f"Removed rate limit config for task '{task_name}'")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to remove rate limit config for task '{task_name}': {e}")
            return False

    async def add_limiter(self, task_name: str, config: RateLimitConfig):
        """添加限流器

        Args:
            task_name: 任务名称
            config: 限流配置（QPSLimit 或 ConcurrencyLimit）
        """
        if task_name in self.limiters:
            logger.warning(f"Limiter for {task_name} already exists")
            return

        limiter = TaskRateLimiter(
            redis_client=self.redis,
            task_name=task_name,
            worker_id=self.worker_id,
            config=config,
            redis_prefix=self.redis_prefix,
            registry_manager=self.registry_manager,
            worker_state_manager=self.worker_state_manager
        )

        await limiter.start()
        self.limiters[task_name] = limiter

        logger.debug(f"Added rate limiter for {task_name}: {config}")

    async def remove_limiter(self, task_name: str, remove_from_redis: bool = False):
        """移除任务限流器

        Args:
            task_name: 任务名称
            remove_from_redis: 是否从 Redis 中删除配置（默认 False）
        """
        if task_name not in self.limiters:
            return

        limiter = self.limiters.pop(task_name)
        await limiter.stop()

        # 如果需要，从 Redis 中删除配置和索引
        if remove_from_redis:
            try:
                # 删除配置 Hash
                rate_limit_key = f"{self.redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"
                await self.redis.delete(rate_limit_key)

                # 从索引集合中移除
                index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
                await self.redis.srem(index_key, task_name)

                logger.debug(f"Removed rate limit config and index for {task_name} from Redis")
            except Exception as e:
                logger.error(f"Failed to remove rate limit config from Redis: {e}")

        logger.debug(f"Removed rate limiter for {task_name}")

    async def load_config_from_redis(self, task_names: list = None):
        """从 Redis 加载限流配置

        Args:
            task_names: 任务名称列表（如果提供，只加载这些任务的配置；否则从索引集合中加载）
        """
        try:
            config_count = 0
            loaded_limiters = []

            # 如果没有提供 task_names，尝试从索引集合中获取
            if not task_names:
                index_key = f"{self.redis_prefix}:RATE_LIMIT:INDEX"
                task_names_bytes = await self.redis.smembers(index_key)
                task_names = [
                    name.decode('utf-8') if isinstance(name, bytes) else name
                    for name in task_names_bytes
                ]

                if not task_names:
                    logger.debug(f"No rate limit configs found in index {index_key}")
                    return

            # 遍历所有任务名称，加载配置
            for task_name in task_names:
                key = f"{self.redis_prefix}:RATE_LIMIT:CONFIG:{task_name}"

                # 检查 key 是否存在
                exists = await self.redis.exists(key)
                if not exists:
                    continue

                # 检查 key 类型
                key_type = await self.redis.type(key)
                if key_type != "hash":
                    logger.debug(f"Skipping non-hash key: {key} (type: {key_type})")
                    continue

                # 从 Hash 中读取配置
                config_dict = await self.redis.hgetall(key)
                if not config_dict:
                    continue

                # 转换 bytes 为 str
                config_dict = {
                    k.decode() if isinstance(k, bytes) else k:
                    v.decode() if isinstance(v, bytes) else v
                    for k, v in config_dict.items()
                }

                # 解析配置
                config = parse_rate_limit_config(config_dict)
                if config and task_name not in self.limiters:
                    try:
                        await self.add_limiter(task_name, config)
                        config_count += 1
                        loaded_limiters.append(task_name)
                    except Exception as e:
                        logger.error(f"Failed to add limiter for {task_name}: {e}")

            logger.debug(f"Loaded {config_count} rate limit configs from Redis")
            logger.debug(f"Loaded rate limit config from Redis, limiters: {loaded_limiters}")
        except Exception as e:
            logger.error(f"Failed to load config from Redis: {e}")

    async def acquire(self, task_name: str, timeout: float = 10.0) -> Optional[str]:
        """获取指定任务的执行许可

        Returns:
            成功返回 task_id (或 True), 失败返回 None
        """
        limiter = self.limiters.get(task_name)
        if not limiter:
            # 没有限流，直接返回 True
            return True

        return await limiter.acquire(timeout)

    async def release(self, task_name: str, task_id: Optional[str] = None):
        """释放指定任务的执行许可

        Args:
            task_name: 任务名称
            task_id: 任务ID (ConcurrencyLimit 需要)
        """
        limiter = self.limiters.get(task_name)
        if limiter:
            await limiter.release(task_id)

    async def stop_all(self):
        """停止所有限流器"""
        for task_name, limiter in list(self.limiters.items()):
            await limiter.stop()
        self.limiters.clear()
        logger.debug("Stopped all rate limiters")

    def get_all_stats(self) -> Dict[str, dict]:
        """获取所有限流器的统计信息"""
        stats = {}
        for task_name, limiter in self.limiters.items():
            if hasattr(limiter, 'get_stats'):
                stats[task_name] = limiter.get_stats()
        return stats


__all__ = ['RateLimiterManager']
