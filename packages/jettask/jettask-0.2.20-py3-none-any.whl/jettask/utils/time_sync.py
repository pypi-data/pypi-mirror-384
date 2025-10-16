#!/usr/bin/env python
"""时间同步模块

提供与 Redis 服务器时间同步的功能，避免多个 worker 因系统时间不一致导致的限流问题。
在启动时一次性校准与 Redis 服务器的时间差，后续使用本地时间加上时间差来获得标准时间。
"""

import time
import logging
from typing import Optional
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


class TimeSync:
    """时间同步类

    在初始化时与 Redis 服务器时间进行一次校准，计算时间差。
    后续所有时间获取都使用 本地时间 + 时间差 的方式，避免频繁访问 Redis。

    使用方式:
        # 初始化（异步）
        time_sync = TimeSync()
        await time_sync.sync(redis_client)

        # 获取标准时间
        now = time_sync.time()
    """

    def __init__(self):
        """初始化时间同步器"""
        self._offset = 0.0  # Redis 服务器时间与本地时间的差值（秒）
        self._synced = False  # 是否已同步
        self._sync_timestamp = 0.0  # 同步时的本地时间戳

    async def sync(self, redis_client: aioredis.Redis, retry: int = 3) -> bool:
        """与 Redis 服务器时间同步

        Args:
            redis_client: 异步 Redis 客户端
            retry: 重试次数

        Returns:
            同步是否成功
        """
        for attempt in range(retry):
            try:
                # 记录请求前的本地时间
                local_before = time.time()

                # 获取 Redis 服务器时间（微秒级）
                # TIME 命令返回 [seconds, microseconds]
                redis_time = await redis_client.time()

                # 记录请求后的本地时间
                local_after = time.time()

                # 计算网络往返时间的一半（估算单程延迟）
                network_delay = (local_after - local_before) / 2.0

                # Redis 时间转换为秒（包含微秒）
                redis_timestamp = float(redis_time[0]) + float(redis_time[1]) / 1_000_000.0

                # 估算 Redis 服务器在请求时刻的时间
                # 使用请求前时间 + 单程延迟来估算
                estimated_local_time = local_before + network_delay

                # 计算时间差：Redis 服务器时间 - 本地时间
                self._offset = redis_timestamp - estimated_local_time
                self._sync_timestamp = time.time()
                self._synced = True

                logger.debug(
                    f"时间同步成功: offset={self._offset:.6f}s, "
                    f"network_delay={network_delay*1000:.2f}ms, "
                    f"redis_time={redis_timestamp:.6f}, "
                    f"local_time={estimated_local_time:.6f}"
                )

                # 如果时间差超过 1 秒，给出警告
                if abs(self._offset) > 1.0:
                    logger.warning(
                        f"本地时间与 Redis 服务器时间差异较大: {self._offset:.2f}s，"
                        f"建议检查系统时间配置"
                    )

                return True

            except Exception as e:
                logger.error(f"时间同步失败 (attempt {attempt + 1}/{retry}): {e}")
                if attempt < retry - 1:
                    await asyncio.sleep(0.1)

        logger.error("时间同步失败，使用本地时间")
        self._synced = False
        return False

    def time(self) -> float:
        """获取标准时间

        Returns:
            标准时间戳（秒）
        """
        if not self._synced:
            # 未同步时使用本地时间
            return time.time()

        # 使用本地时间 + 时间差
        return time.time() + self._offset

    def is_synced(self) -> bool:
        """检查是否已同步

        Returns:
            是否已同步
        """
        return self._synced

    def get_offset(self) -> float:
        """获取时间偏移量

        Returns:
            时间偏移量（秒）
        """
        return self._offset

    def get_sync_info(self) -> dict:
        """获取同步信息

        Returns:
            同步信息字典
        """
        return {
            'synced': self._synced,
            'offset': self._offset,
            'sync_timestamp': self._sync_timestamp,
            'time_since_sync': time.time() - self._sync_timestamp if self._synced else None,
        }


# 全局时间同步实例（单例模式）
_global_time_sync: Optional[TimeSync] = None


def get_time_sync() -> TimeSync:
    """获取全局时间同步实例

    Returns:
        TimeSync 实例
    """
    global _global_time_sync
    if _global_time_sync is None:
        _global_time_sync = TimeSync()
    return _global_time_sync


async def init_time_sync(redis_client: aioredis.Redis) -> TimeSync:
    """初始化全局时间同步

    Args:
        redis_client: 异步 Redis 客户端

    Returns:
        TimeSync 实例
    """
    time_sync = get_time_sync()
    await time_sync.sync(redis_client)
    return time_sync


# 添加缺失的 asyncio 导入
import asyncio
