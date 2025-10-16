"""
Web UI 模块

提供 Web 界面和 API 接口。
"""

# 不在 __init__ 中导入 app，避免循环导入
# 使用时直接: from jettask.webui.app import app
from .config import *

# 异常类直接从主模块导入（webui/exceptions.py已废弃并删除）
from jettask.exceptions import (
    JetTaskException,
    TaskTimeoutError,
    TaskExecutionError,
    TaskNotFoundError,
    RetryableError
)

__all__ = [
    # 'app',  # 移除，避免循环导入
    'JetTaskException',
    'TaskTimeoutError',
    'TaskExecutionError',
    'TaskNotFoundError',
    'RetryableError',
]
