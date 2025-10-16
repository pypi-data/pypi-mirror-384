"""
QPS（每秒查询数）限流器

基于滑动窗口算法的QPS限流实现
"""

import asyncio
import logging
import time
from collections import deque
from redis.asyncio import Redis
from typing import Dict, Optional

from jettask.utils.time_sync import get_time_sync

logger = logging.getLogger('app')


class QPSRateLimiter:
    """QPS 限流器 - 本地滑动窗口算法

    使用滑动窗口算法在本地限流,不访问 Redis。
    记录每个任务的执行时间戳,检查窗口内的执行次数。
    使用全局时间同步器保证多个 worker 时间一致性。

    特点：
    - 纯本地计算，零 Redis 访问
    - 高性能，低延迟
    - 通过 Redis 协调配额分配
    """

    def __init__(
        self,
        qps: int,
        window_size: float = 1.0,
        worker_id: str = "unknown"
    ):
        """初始化 QPS 限流器

        Args:
            qps: 当前 worker 的 QPS 配额
            window_size: 滑动窗口大小（秒）
            worker_id: Worker ID，用于日志标识
        """
        self.qps_limit = qps
        self.window_size = window_size
        self.worker_id = worker_id
        self.timestamps = deque()  # 记录执行时间戳
        self._lock = asyncio.Lock()
        self.time_sync = get_time_sync()

    def _get_time(self) -> float:
        """获取当前时间"""
        return self.time_sync.time()

    async def acquire(self, timeout: float = 10.0) -> bool:
        """获取一个执行许可

        Args:
            timeout: 等待超时时间（秒）

        Returns:
            成功获取返回 True，超时返回 False
        """
        start_time = self._get_time()

        while True:
            async with self._lock:
                now = self._get_time()

                # 清理过期的时间戳（窗口外的）
                cutoff = now - self.window_size
                while self.timestamps and self.timestamps[0] < cutoff:
                    self.timestamps.popleft()

                # 检查 QPS 限制
                current_count = len(self.timestamps)
                if current_count < self.qps_limit:
                    # 未达到限制，允许执行
                    self.timestamps.append(now)
                    logger.debug(
                        f"[QPS] Acquired, count={current_count + 1}/{self.qps_limit}"
                    )
                    return True

            # 达到限制，检查超时
            if timeout is not None and self._get_time() - start_time > timeout:
                logger.warning(f"[QPS] Acquire timeout after {timeout}s")
                return False

            # 短暂休眠后重试
            await asyncio.sleep(0.01)

    async def try_acquire(self) -> bool:
        """尝试获取执行许可（非阻塞）"""
        async with self._lock:
            now = self._get_time()

            # 清理过期的时间戳
            cutoff = now - self.window_size
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()

            # 检查是否可以执行
            current_count = len(self.timestamps)
            if current_count < self.qps_limit:
                self.timestamps.append(now)
                logger.debug(f"[QPS] Try acquired, count={current_count + 1}/{self.qps_limit}")
                return True

            logger.debug(f"[QPS] Try acquire failed, count={current_count}/{self.qps_limit}")
            return False

    async def release(self):
        """释放执行许可（QPS 模式不需要 release）"""
        pass

    async def update_limit(self, new_limit: int):
        """动态更新 QPS 限制

        Args:
            new_limit: 新的 QPS 限制
        """
        async with self._lock:
            if self.qps_limit != new_limit:
                old_limit = self.qps_limit
                self.qps_limit = new_limit
                logger.debug(
                    f"[WORKER:{self.worker_id}] [QPS] Limit changed: {old_limit} → {new_limit}"
                )

    async def get_stats(self) -> dict:
        """获取统计信息"""
        async with self._lock:
            now = self._get_time()
            cutoff = now - self.window_size
            while self.timestamps and self.timestamps[0] < cutoff:
                self.timestamps.popleft()

            return {
                'mode': 'qps',
                'qps_limit': self.qps_limit,
                'current_qps': len(self.timestamps),
                'window_size': self.window_size,
            }


# ============================================================
# 并发限流器 - 分布式信号量
# ============================================================



__all__ = ['QPSRateLimiter']
