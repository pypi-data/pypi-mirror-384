"""
执行器模块

提供任务执行的核心功能，支持单进程和多进程两种模式。

主要组件：
- TaskExecutor: 任务执行器（新）
- ProcessOrchestrator: 多进程编排器
- ExecutorCore: 核心执行逻辑
"""

from .core import ExecutorCore
from .orchestrator import ProcessConfig, ProcessOrchestrator
from .task_executor import TaskExecutor

# 保留 UnifiedExecutor 作为兼容（已废弃）
try:
    from .executor import UnifiedExecutor
except ImportError:
    # 如果导入失败，提供一个废弃提示
    class UnifiedExecutor:
        def __init__(self, *args, **kwargs):
            raise DeprecationWarning(
                "UnifiedExecutor is deprecated. "
                "Use TaskExecutor for single task execution, "
                "or ProcessOrchestrator for multi-process management."
            )

__all__ = [
    # 新的推荐类
    'TaskExecutor',
    'ProcessOrchestrator',
    'ProcessConfig',
    'ExecutorCore',

    # 废弃但保留兼容性
    'UnifiedExecutor',
]
