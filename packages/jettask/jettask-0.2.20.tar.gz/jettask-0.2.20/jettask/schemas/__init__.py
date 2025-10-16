"""
数据模型定义
所有的Pydantic模型集中管理
"""

# 任务相关模型
from .task import (
    TasksRequest,
    TaskDetailResponse,
    TaskInfo,
    TaskActionRequest,
    TaskListResponse
)

# 队列相关模型
from .queue import (
    TimeRangeQuery,
    QueueStatsResponse,
    QueueTimelineResponse,
    TrimQueueRequest,
    QueueInfo,
    QueueStats,
    QueueActionRequest
)

# 定时任务相关模型
from .scheduled_task import (
    ScheduledTaskRequest,
    ScheduledTaskResponse,
    ScheduledTaskInfo,
    ScheduleConfig,
    ScheduledTaskCreate,
    ScheduledTaskUpdate,
    ScheduledTaskCreateRequest
)

# 告警相关模型
from .alert import (
    AlertRuleRequest,
    AlertRuleCreate,
    AlertRuleUpdate,
    AlertRule,
    AlertInstance,
    AlertSummary
)

# 命名空间相关模型
from .namespace import (
    ConfigMode,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse,
    NamespaceInfo,
    NamespaceCreateRequest,
    NamespaceUpdateRequest
)

# 积压监控相关模型
from .backlog import (
    BacklogTrendRequest,
    BacklogSnapshot,
    BacklogStatistics,
    BacklogTrendResponse,
    BacklogAlert
)

# 通用模型
from .common import (
    ErrorResponse,
    FilterCondition,
    BaseListRequest,
    TimeRangeRequest,
    BatchOperationRequest,
    BatchOperationResponse,
    PaginationResponse,
    ListResponse,
    HealthCheck,
    SystemConfigUpdateRequest,
    ApiResponse
)

# 监控和分析模型
from .monitoring import (
    MetricPoint,
    TimeSeries,
    MonitoringMetrics,
    AnalyticsData,
    SystemHealth,
    DashboardOverviewRequest,
    DashboardOverview,
    WorkerMetrics
)

__all__ = [
    # Task
    'TasksRequest',
    'TaskDetailResponse',
    'TaskInfo',
    'TaskActionRequest',
    'TaskListResponse',
    
    # Queue
    'TimeRangeQuery',
    'QueueStatsResponse',
    'QueueTimelineResponse',
    'TrimQueueRequest',
    'QueueInfo',
    'QueueStats',
    'QueueActionRequest',
    
    # Scheduled Task
    'ScheduledTaskRequest',
    'ScheduledTaskResponse',
    'ScheduledTaskInfo',
    'ScheduleConfig',
    'ScheduledTaskCreate',
    'ScheduledTaskUpdate',
    'ScheduledTaskCreateRequest',
    
    # Alert
    'AlertRuleRequest',
    'AlertRuleCreate',
    'AlertRuleUpdate',
    'AlertRule',
    'AlertInstance',
    'AlertSummary',
    
    # Namespace
    'ConfigMode',
    'NamespaceCreate',
    'NamespaceUpdate',
    'NamespaceResponse',
    'NamespaceInfo',
    'NamespaceCreateRequest',
    'NamespaceUpdateRequest',
    
    # Backlog
    'BacklogTrendRequest',
    'BacklogSnapshot',
    'BacklogStatistics',
    'BacklogTrendResponse',
    'BacklogAlert',
    
    # Common
    'ErrorResponse',
    'FilterCondition',
    'BaseListRequest',
    'TimeRangeRequest',
    'BatchOperationRequest',
    'BatchOperationResponse',
    'PaginationResponse',
    'ListResponse',
    'HealthCheck',
    'SystemConfigUpdateRequest',
    'ApiResponse',
    
    # Monitoring
    'MetricPoint',
    'TimeSeries',
    'MonitoringMetrics',
    'AnalyticsData',
    'SystemHealth',
    'DashboardOverviewRequest',
    'DashboardOverview',
    'WorkerMetrics'
]