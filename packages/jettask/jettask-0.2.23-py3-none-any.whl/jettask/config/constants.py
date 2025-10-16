"""
JetTask 系统常量定义

集中管理所有系统级别的常量配置，包括：
- 内部消费者组
- 系统保留关键字
- 默认配置值
- 其他常量
"""

# ============================================================================
# 内部消费者组配置
# ============================================================================

# 内部消费者组前缀列表
# 任何以这些前缀开头的消费者组都会被视为内部消费者组，不会在用户界面显示
INTERNAL_CONSUMER_PREFIXES = [
    'pg_consumer_',      # PostgreSQL 消费者
    'webui_consumer_',   # WebUI 消费者
    'monitor_',          # 监控消费者
    'system_',           # 系统消费者
    '_internal_',        # 通用内部消费者
    '__',                # 双下划线开头的保留消费者
]

# 特定的内部消费者组名称（完全匹配）
INTERNAL_CONSUMER_NAMES = [
    'pg_consumer',       # 默认的 PostgreSQL 消费者
    'webui_consumer',    # 默认的 WebUI 消费者
    'system',            # 系统消费者
]

# ============================================================================
# Redis 键前缀和模式
# ============================================================================

# Redis 键前缀
REDIS_KEY_PREFIX = {
    'QUEUE': 'QUEUE',                    # 队列前缀
    'TASK': 'TASK',                      # 任务前缀
    'WORKER': 'WORKER',                  # Worker前缀
    'LEADER': 'leader',                  # Leader锁前缀
    'QUEUE_OFFSETS': 'QUEUE_OFFSETS',    # 队列偏移量
    'TASK_OFFSETS': 'TASK_OFFSETS',      # 任务偏移量
    'SCHEDULED': 'scheduled',            # 定时任务前缀
    'MONITOR': 'monitor',                # 监控前缀
}

# ============================================================================
# 数据库相关常量
# ============================================================================

# 分区表配置
PARTITION_TABLE_CONFIG = {
    'tasks': {
        'partition_by': 'created_at',
        'interval': 'daily',              # daily, weekly, monthly
        'retention_days': 30,             # 保留天数
    },
    'task_runs': {
        'partition_by': 'created_at',
        'interval': 'daily',
        'retention_days': 30,
    },
    'stream_backlog_monitor': {
        'partition_by': 'created_at',
        'interval': 'hourly',             # 小时级分区
        'retention_days': 7,              # 保留7天
    }
}

# ============================================================================
# 系统默认值
# ============================================================================

# 默认超时设置（秒）
DEFAULT_TIMEOUTS = {
    'task_execution': 300,        # 任务执行超时（5分钟）
    'task_ack': 60,               # 任务确认超时（1分钟）
    'worker_heartbeat': 30,       # Worker心跳超时（30秒）
    'lock_ttl': 60,               # 分布式锁TTL（60秒）
    'redis_operation': 5,         # Redis操作超时（5秒）
}

# 默认限制值
DEFAULT_LIMITS = {
    'max_retries': 3,             # 最大重试次数
    'max_pending_per_group': 1000,  # 每个消费组最大pending数
    'max_batch_size': 100,        # 最大批处理大小
    'max_prefetch': 100,          # 最大预取数量
}

# 监控和统计间隔（秒）
MONITOR_INTERVALS = {
    'backlog_monitor': 1,         # 积压监控间隔
    'health_check': 30,           # 健康检查间隔
    'namespace_check': 60,        # 命名空间检查间隔（默认）
    'stats_aggregation': 60,      # 统计聚合间隔
}

# ============================================================================
# 任务状态定义
# ============================================================================

# 任务状态优先级（数值越大，状态越"新"）
TASK_STATUS_PRIORITY = {
    'pending': 1,      # 待处理
    'running': 2,      # 运行中
    'success': 3,      # 成功（终态）
    'error': 3,        # 错误（终态）
    'failed': 3,       # 失败（终态）
    'timeout': 3,      # 超时（终态）
    'rejected': 3,     # 拒绝（终态）
    'cancelled': 3,    # 取消（终态）
}

# 终态状态列表
TASK_FINAL_STATES = ['success', 'error', 'failed', 'timeout', 'rejected', 'cancelled']

# 可重试状态列表
TASK_RETRYABLE_STATES = ['error', 'failed', 'timeout']

# ============================================================================
# 辅助函数
# ============================================================================

def is_internal_consumer(consumer_group: str) -> bool:
    """
    判断给定的消费者组是否为内部消费者组
    
    Args:
        consumer_group: 消费者组名称
        
    Returns:
        如果是内部消费者组返回 True，否则返回 False
    """
    if not consumer_group:
        return False
    
    # 转换为小写进行比较
    consumer_group_lower = consumer_group.lower()
    
    # 检查完全匹配（不区分大小写）
    for name in INTERNAL_CONSUMER_NAMES:
        if consumer_group_lower == name.lower():
            return True
    
    # 检查前缀匹配（不区分大小写）
    for prefix in INTERNAL_CONSUMER_PREFIXES:
        if consumer_group_lower.startswith(prefix.lower()):
            return True
    
    # 特殊处理：模糊匹配包含特定关键字的消费者组
    # 例如：pg_consumer 可能以不同格式出现，如 pg_consumer_YYDG_12345
    internal_keywords = [
        'pg_consumer',      # PostgreSQL 消费者的各种变体
        'webui_consumer',   # WebUI 消费者的各种变体
    ]
    
    for keyword in internal_keywords:
        if keyword in consumer_group_lower:
            return True
    
    return False


def filter_internal_consumers(consumer_groups: list) -> list:
    """
    从消费者组列表中过滤掉内部消费者组
    
    Args:
        consumer_groups: 消费者组名称列表
        
    Returns:
        过滤后的消费者组列表
    """
    return [cg for cg in consumer_groups if not is_internal_consumer(cg)]


def get_redis_key(namespace: str, key_type: str, *parts) -> str:
    """
    构建Redis键
    
    Args:
        namespace: 命名空间
        key_type: 键类型（从REDIS_KEY_PREFIX中选择）
        *parts: 其他键组成部分
        
    Returns:
        完整的Redis键
    """
    prefix = REDIS_KEY_PREFIX.get(key_type, key_type)
    key_parts = [namespace, prefix] + list(parts)
    return ':'.join(str(p) for p in key_parts if p)


def get_partition_interval_seconds(interval: str) -> int:
    """
    获取分区间隔对应的秒数
    
    Args:
        interval: 分区间隔（hourly, daily, weekly, monthly）
        
    Returns:
        对应的秒数
    """
    intervals = {
        'hourly': 3600,
        'daily': 86400,
        'weekly': 604800,
        'monthly': 2592000,  # 30天
    }
    return intervals.get(interval, 86400)  # 默认返回一天