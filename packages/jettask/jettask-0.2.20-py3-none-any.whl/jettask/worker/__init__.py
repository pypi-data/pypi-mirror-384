"""
Worker 管理模块

提供 Worker 的创建、生命周期管理、状态监控等功能。

推荐使用新接口:
    from jettask.worker import WorkerManager

    manager = WorkerManager(redis, async_redis, 'jettask')
    worker_id = await manager.start_worker('MyApp', ['queue1'])
"""

# 主要接口
from .manager import (
    WorkerManager,
    WorkerState,       # Worker 状态管理（之前叫 WorkerRegistry）
    ConsumerManager,
    WorkerNaming,
)

# 生命周期和状态管理
from .lifecycle import (
    WorkerLifecycle,
    WorkerStateManager,
    HeartbeatThreadManager,
    WorkerScanner,
    HeartbeatConsumerStrategy,  # 兼容性
)

# 恢复
from .recovery import OfflineWorkerRecovery

# 兼容性别名：WorkerRegistry -> WorkerState
WorkerRegistry = WorkerState

__all__ = [
    # 主要接口
    'WorkerManager',
    'WorkerState',        # 新名称（推荐使用）
    'WorkerRegistry',     # 兼容性别名
    'ConsumerManager',
    'WorkerNaming',

    # 生命周期和状态管理
    'WorkerLifecycle',
    'WorkerStateManager',
    'HeartbeatThreadManager',
    'WorkerScanner',
    'HeartbeatConsumerStrategy',  # 兼容性

    # 恢复
    'OfflineWorkerRecovery',
]
