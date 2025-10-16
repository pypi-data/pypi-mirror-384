"""
任务状态和结果定义
"""
from enum import Enum
from dataclasses import dataclass
from typing import Any, Optional, Dict
import time


class TaskStatus(Enum):
    """任务状态枚举"""
    # 基本状态
    PENDING = "pending"          # 任务已创建，等待执行
    RUNNING = "running"          # 任务正在执行
    SUCCESS = "success"          # 任务执行成功
    ERROR = "error"              # 任务执行失败
    
    # 特殊状态
    DELAYED = "delayed"          # 延迟任务，等待触发
    REJECTED = "rejected"        # 任务被拒绝（on_before返回reject）
    RETRY = "retry"              # 任务等待重试
    TIMEOUT = "timeout"          # 任务执行超时
    CANCELLED = "cancelled"      # 任务被取消
    
    # 定时任务相关状态
    SCHEDULED = "scheduled"      # 已调度（定时任务专用）
    
    @classmethod
    def is_terminal(cls, status: 'TaskStatus') -> bool:
        """判断是否是终态（不会再改变的状态）"""
        return status in {cls.SUCCESS, cls.ERROR, cls.REJECTED, cls.TIMEOUT, cls.CANCELLED}
    
    @classmethod
    def is_active(cls, status: 'TaskStatus') -> bool:
        """判断是否是活跃状态（正在处理中）"""
        return status in {cls.PENDING, cls.RUNNING, cls.DELAYED, cls.RETRY, cls.SCHEDULED}


@dataclass
class TaskResult:
    """
    任务结果对象
    apply_async 返回的结果，包含任务的完整信息
    """
    id: str                                    # 任务ID（event_id）
    name: str                                   # 任务名称
    queue: str                                  # 队列名称
    status: TaskStatus = TaskStatus.PENDING    # 任务状态
    created_at: float = None                   # 创建时间
    trigger_time: float = None                 # 触发时间
    scheduled_task_id: Optional[int] = None    # 定时任务ID（如果由定时任务触发）
    args: tuple = None                         # 位置参数
    kwargs: dict = None                        # 关键字参数
    metadata: Dict[str, Any] = None           # 其他元数据
    
    def __post_init__(self):
        """初始化默认值"""
        if self.created_at is None:
            self.created_at = time.time()
        if self.trigger_time is None:
            self.trigger_time = self.created_at
        if self.args is None:
            self.args = ()
        if self.kwargs is None:
            self.kwargs = {}
        if self.metadata is None:
            self.metadata = {}
    
    def __str__(self) -> str:
        """字符串表示"""
        return f"TaskResult(id={self.id}, name={self.name}, status={self.status.value})"
    
    def __repr__(self) -> str:
        """详细表示"""
        return (f"TaskResult(id={self.id}, name={self.name}, queue={self.queue}, "
                f"status={self.status.value}, created_at={self.created_at})")
    
    async def wait(self, timeout: Optional[float] = None):
        """
        等待任务完成
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            任务执行结果
        """
        # TODO: 实现等待逻辑
        raise NotImplementedError("wait method not implemented yet")
    
    async def get_result(self, timeout: Optional[float] = None):
        """
        获取任务结果
        
        Args:
            timeout: 超时时间（秒）
            
        Returns:
            任务执行结果
        """
        # TODO: 实现获取结果逻辑
        raise NotImplementedError("get_result method not implemented yet")
    
    async def cancel(self) -> bool:
        """
        取消任务
        
        Returns:
            是否成功取消
        """
        # TODO: 实现取消逻辑
        raise NotImplementedError("cancel method not implemented yet")
    
    async def get_status(self) -> TaskStatus:
        """
        获取任务当前状态
        
        Returns:
            任务状态
        """
        # TODO: 实现获取状态逻辑
        raise NotImplementedError("get_status method not implemented yet")
    
    @property
    def is_ready(self) -> bool:
        """任务是否已完成（终态）"""
        return TaskStatus.is_terminal(self.status)
    
    @property
    def is_successful(self) -> bool:
        """任务是否成功"""
        return self.status == TaskStatus.SUCCESS
    
    @property
    def is_failed(self) -> bool:
        """任务是否失败"""
        return self.status in {TaskStatus.ERROR, TaskStatus.TIMEOUT, TaskStatus.REJECTED}