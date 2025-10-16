"""
配置管理模块 - 统一的配置定义
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any


@dataclass
class RedisConfig:
    """Redis 配置"""
    url: str = "redis://localhost:6379/0"
    prefix: str = "jettask"

    # 连接池配置
    max_connections: int = 50
    decode_responses: bool = True  # 文本模式客户端

    def __post_init__(self):
        """验证配置"""
        if not self.url:
            raise ValueError("Redis URL is required")
        if not self.prefix:
            raise ValueError("Redis prefix is required")


@dataclass
class ExecutorConfig:
    """执行器配置"""
    type: str = "asyncio"  # asyncio, multi_asyncio, process, thread
    concurrency: int = 10
    prefetch_multiplier: int = 1  # 预取倍数

    # Worker配置
    worker_heartbeat_interval: float = 1.0  # 心跳间隔（秒）
    worker_heartbeat_timeout: float = 3.0   # 心跳超时（秒）

    def __post_init__(self):
        """验证配置"""
        if self.concurrency < 1:
            raise ValueError("Concurrency must be at least 1")
        if self.prefetch_multiplier < 1:
            raise ValueError("Prefetch multiplier must be at least 1")


@dataclass
class RateLimitConfig:
    """限流配置"""
    enabled: bool = False
    strategy: str = "local"  # local, ondemand

    # Local sliding window配置
    qps_limit: Optional[int] = None
    window_size: float = 1.0
    sync_interval: float = 5.0  # 配额同步间隔（秒）

    def __post_init__(self):
        """验证配置"""
        if self.enabled and not self.qps_limit:
            raise ValueError("QPS limit is required when rate limit is enabled")


@dataclass
class MessageConfig:
    """消息配置"""
    # 延迟队列扫描
    delayed_scan_interval: float = 0.05  # 扫描间隔（秒）
    delayed_batch_size: int = 100  # 批量处理大小

    # 消息读取
    read_block_time: int = 1000  # 阻塞读取时间（毫秒）
    read_batch_size: int = 1  # 每次读取消息数

    # 消息重试
    max_retries: int = 3
    retry_backoff: float = 1.0  # 重试退避时间（秒）


@dataclass
class ConsumerConfig:
    """消费者配置"""
    strategy: str = "heartbeat"  # heartbeat, reuse

    # 心跳策略配置
    heartbeat_interval: float = 1.0
    heartbeat_timeout: float = 3.0

    # 复用策略配置
    reuse_timeout: float = 60.0

    def __post_init__(self):
        """验证配置"""
        valid_strategies = ["heartbeat", "reuse"]
        if self.strategy not in valid_strategies:
            raise ValueError(f"Consumer strategy must be one of {valid_strategies}")


@dataclass
class WorkerConfig:
    """Worker 配置"""
    worker_id: Optional[str] = None  # 如果不指定，会自动生成
    hostname: Optional[str] = None   # 如果不指定，会自动获取

    # Worker状态管理
    state_sync_enabled: bool = True
    state_pubsub_enabled: bool = True  # 是否启用状态变化的Pub/Sub通知

    # Worker扫描配置
    scanner_enabled: bool = True
    scanner_interval: float = 1.0  # 扫描间隔（秒）


@dataclass
class JetTaskConfig:
    """
    JetTask 统一配置

    示例:
        config = JetTaskConfig(
            redis=RedisConfig(
                url="redis://localhost:6379/0",
                prefix="myapp"
            ),
            executor=ExecutorConfig(
                type="asyncio",
                concurrency=20
            ),
            rate_limit=RateLimitConfig(
                enabled=True,
                qps_limit=100
            )
        )
    """
    redis: RedisConfig = field(default_factory=RedisConfig)
    executor: ExecutorConfig = field(default_factory=ExecutorConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)
    message: MessageConfig = field(default_factory=MessageConfig)
    consumer: ConsumerConfig = field(default_factory=ConsumerConfig)
    worker: WorkerConfig = field(default_factory=WorkerConfig)

    # 其他全局配置
    debug: bool = False
    extra: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'JetTaskConfig':
        """
        从字典创建配置对象

        Args:
            config_dict: 配置字典

        Returns:
            JetTaskConfig实例

        示例:
            config = JetTaskConfig.from_dict({
                'redis': {
                    'url': 'redis://localhost:6379/0',
                    'prefix': 'myapp'
                },
                'executor': {
                    'concurrency': 20
                }
            })
        """
        redis_config = RedisConfig(**config_dict.get('redis', {}))
        executor_config = ExecutorConfig(**config_dict.get('executor', {}))
        rate_limit_config = RateLimitConfig(**config_dict.get('rate_limit', {}))
        message_config = MessageConfig(**config_dict.get('message', {}))
        consumer_config = ConsumerConfig(**config_dict.get('consumer', {}))
        worker_config = WorkerConfig(**config_dict.get('worker', {}))

        return cls(
            redis=redis_config,
            executor=executor_config,
            rate_limit=rate_limit_config,
            message=message_config,
            consumer=consumer_config,
            worker=worker_config,
            debug=config_dict.get('debug', False),
            extra=config_dict.get('extra', {})
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        转换为字典

        Returns:
            配置字典
        """
        from dataclasses import asdict
        return asdict(self)

    def validate(self):
        """验证所有配置"""
        # 各个子配置在__post_init__中已经验证
        # 这里可以添加跨配置的验证逻辑
        pass


# 便捷函数：创建默认配置
def create_default_config(redis_url: str = "redis://localhost:6379/0",
                         redis_prefix: str = "jettask") -> JetTaskConfig:
    """
    创建默认配置

    Args:
        redis_url: Redis连接URL
        redis_prefix: Redis键前缀

    Returns:
        默认配置对象
    """
    return JetTaskConfig(
        redis=RedisConfig(url=redis_url, prefix=redis_prefix)
    )


# 便捷函数：从环境变量创建配置
def create_config_from_env() -> JetTaskConfig:
    """
    从环境变量创建配置

    环境变量:
        JETTASK_REDIS_URL: Redis连接URL
        JETTASK_REDIS_PREFIX: Redis键前缀
        JETTASK_EXECUTOR_CONCURRENCY: 并发数
        JETTASK_DEBUG: 调试模式

    Returns:
        配置对象
    """
    import os

    redis_url = os.getenv('JETTASK_REDIS_URL', 'redis://localhost:6379/0')
    redis_prefix = os.getenv('JETTASK_REDIS_PREFIX', 'jettask')
    concurrency = int(os.getenv('JETTASK_EXECUTOR_CONCURRENCY', '10'))
    debug = os.getenv('JETTASK_DEBUG', 'false').lower() == 'true'

    return JetTaskConfig(
        redis=RedisConfig(url=redis_url, prefix=redis_prefix),
        executor=ExecutorConfig(concurrency=concurrency),
        debug=debug
    )
