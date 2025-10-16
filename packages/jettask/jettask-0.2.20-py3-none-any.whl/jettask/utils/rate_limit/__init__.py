"""
限流模块

提供QPS和并发限流功能

主要组件：
- QPSRateLimiter: QPS限流器
- ConcurrencyRateLimiter: 并发限流器
- TaskRateLimiter: 任务级限流器
- RateLimiterManager: 限流器管理器
- RateLimitConfig: 限流配置
"""

from .config import RateLimitConfig, QPSLimit, ConcurrencyLimit
from .qps_limiter import QPSRateLimiter
from .concurrency_limiter import ConcurrencyRateLimiter
from .task_limiter import TaskRateLimiter
from .manager import RateLimiterManager

# 向后兼容：保持原有的导入方式
# 旧代码可以继续使用: from jettask.rate_limit.limiter import RateLimiterManager
__all__ = [
    'RateLimitConfig',
    'QPSLimit',
    'ConcurrencyLimit',
    'QPSRateLimiter',
    'ConcurrencyRateLimiter',
    'TaskRateLimiter',
    'RateLimiterManager',
]
