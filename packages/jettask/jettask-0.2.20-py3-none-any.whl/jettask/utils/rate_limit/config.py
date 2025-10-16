#!/usr/bin/env python
"""限流配置类

定义各种限流策略的配置类，通过不同的类来区分限流模式。
"""

from abc import ABC, abstractmethod
from typing import Optional


class RateLimitConfig(ABC):
    """限流配置基类"""

    @abstractmethod
    def to_dict(self) -> dict:
        """转换为字典格式，用于存储到 Redis"""
        pass

    @abstractmethod
    def get_type(self) -> str:
        """获取限流类型标识"""
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, data: dict) -> 'RateLimitConfig':
        """从字典创建配置实例"""
        pass


class QPSLimit(RateLimitConfig):
    """QPS 限流配置

    控制每秒最多执行多少个任务（使用滑动窗口算法）

    Args:
        qps: 每秒允许的最大请求数（所有 workers 总和）
        window_size: 滑动窗口大小（秒），默认 1.0

    Example:
        @app.task(rate_limit=QPSLimit(qps=100))
        async def my_task():
            pass
    """

    def __init__(self, qps: int, window_size: float = 1.0):
        # 转换为正确的类型（处理从 Redis 读取的字符串）
        qps = int(qps)
        window_size = float(window_size)

        if qps <= 0:
            raise ValueError(f"qps must be positive, got {qps}")
        if window_size <= 0:
            raise ValueError(f"window_size must be positive, got {window_size}")

        self.qps = qps
        self.window_size = window_size

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'type': 'qps',
            'qps': self.qps,
            'window_size': self.window_size,
        }

    def get_type(self) -> str:
        """获取限流类型标识"""
        return 'qps'

    @classmethod
    def from_dict(cls, data: dict) -> 'QPSLimit':
        """从字典创建配置实例"""
        return cls(
            qps=data['qps'],
            window_size=data.get('window_size', 1.0)
        )

    def __repr__(self):
        return f"QPSLimit(qps={self.qps}, window_size={self.window_size})"


class ConcurrencyLimit(RateLimitConfig):
    """并发限流配置

    控制同一时刻最多可以运行多少个任务

    Args:
        max_concurrency: 最大并发数（所有 workers 总和）

    Example:
        @app.task(rate_limit=ConcurrencyLimit(max_concurrency=10))
        async def my_task():
            pass
    """

    def __init__(self, max_concurrency: int):
        # 转换为正确的类型（处理从 Redis 读取的字符串）
        max_concurrency = int(max_concurrency)

        if max_concurrency <= 0:
            raise ValueError(f"max_concurrency must be positive, got {max_concurrency}")

        self.max_concurrency = max_concurrency

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'type': 'concurrency',
            'max_concurrency': self.max_concurrency,
        }

    def get_type(self) -> str:
        """获取限流类型标识"""
        return 'concurrency'

    @classmethod
    def from_dict(cls, data: dict) -> 'ConcurrencyLimit':
        """从字典创建配置实例"""
        return cls(max_concurrency=data['max_concurrency'])

    def __repr__(self):
        return f"ConcurrencyLimit(max_concurrency={self.max_concurrency})"


def parse_rate_limit_config(data: dict) -> Optional[RateLimitConfig]:
    """从字典解析限流配置

    Args:
        data: 限流配置字典

    Returns:
        RateLimitConfig 实例，如果解析失败则返回 None
    """
    if not data or not isinstance(data, dict):
        return None

    limit_type = data.get('type')

    if limit_type == 'qps':
        return QPSLimit.from_dict(data)
    elif limit_type == 'concurrency':
        return ConcurrencyLimit.from_dict(data)
    else:
        return None
