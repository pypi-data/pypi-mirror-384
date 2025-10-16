# -*- coding: utf-8 -*-
"""
JetTask - High Performance Distributed Task Queue System
"""

import logging
import inspect

# Core class imports
from jettask.core.app import Jettask
from jettask.core.message import TaskMessage
from jettask.core.context import TaskContext
from jettask.task.task_center.client import TaskCenter
from jettask.task.router import TaskRouter

# Rate limit config imports
from jettask.utils.rate_limit.config import QPSLimit, ConcurrencyLimit

# Import logger components from utils
from jettask.utils.task_logger import (
    TaskContextFilter,
    ExtendedTextFormatter,
    LogContext
)

# Version info
__version__ = "0.1.0"


def get_task_logger(name: str = None) -> logging.Logger:
    """
    获取带任务上下文的logger
    
    Args:
        name: logger名称，默认使用调用者的模块名
    
    Returns:
        配置好的logger实例
        
    Example:
        from jettask import get_task_logger
        logger = get_task_logger()
        logger.info("处理任务")
    """
    if name is None:
        # 自动获取调用者的模块名
        frame = inspect.currentframe()
        if frame and frame.f_back:
            name = frame.f_back.f_globals.get('__name__', 'jettask')
        else:
            name = 'jettask'
    
    logger = logging.getLogger(name)
    
    # 如果logger还没有处理器，添加默认处理器
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(ExtendedTextFormatter(
            '%(asctime)s - %(levelname)s - [%(task_id)s] - %(name)s - %(message)s'
        ))
        handler.addFilter(TaskContextFilter())
        logger.addHandler(handler)
        logger.propagate = False
    
    return logger


# Public API exports
__all__ = [
    "Jettask",
    "TaskMessage",
    "TaskCenter",
    "TaskRouter",
    "QPSLimit",
    "ConcurrencyLimit",
    "get_task_logger",
    "LogContext",
    "TaskContext"
]