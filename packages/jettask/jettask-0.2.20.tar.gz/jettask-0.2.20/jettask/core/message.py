"""
任务消息类 - 完全独立的任务发送对象
与task定义完全解耦，可以在任何项目中使用
"""
from typing import Optional, Dict, Any, Tuple
from dataclasses import dataclass, field, asdict
import time


@dataclass
class TaskMessage:
    """
    任务消息对象
    
    这是一个完全独立的类，不依赖任何task定义。
    可以在没有执行器代码的项目中单独使用。
    
    使用示例:
        # 创建任务消息
        msg = TaskMessage(
            queue="order_processing",
            args=(12345,),
            kwargs={"customer_id": "C001", "amount": 99.99},
            delay=5  # 延迟5秒执行
        )
        
        # 批量创建
        messages = [
            TaskMessage(queue="email", kwargs={"to": "user1@example.com"}),
            TaskMessage(queue="email", kwargs={"to": "user2@example.com"}),
        ]
        
        # 发送
        await app.send_tasks([msg])
        await app.send_tasks(messages)
    """
    
    # 必需参数
    queue: str  # 队列名称（必需）
    
    # 任务参数
    args: Tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    
    # 执行选项
    delay: Optional[int] = None  # 延迟执行（秒）
    priority: Optional[int] = None  # 优先级（1最高，数字越大优先级越低）
    
    # 调度相关
    scheduled_task_id: Optional[int] = None  # 定时任务ID
    
    # 路由信息（用于复杂的路由场景）
    routing: Optional[Dict[str, Any]] = None
    
    # 元数据
    trigger_time: Optional[float] = None  # 触发时间
    
    def __post_init__(self):
        """初始化后处理"""
        # 自动设置触发时间
        if self.trigger_time is None:
            self.trigger_time = time.time()
    
    def to_dict(self) -> dict:
        """
        转换为字典格式（用于序列化发送到Redis）
        
        Returns:
            dict: 消息字典，只包含非None的字段
        """
        data = {
            'queue': self.queue,
            'args': self.args,
            'kwargs': self.kwargs,
            'trigger_time': self.trigger_time
        }
        
        # 添加可选字段（只添加非None的）
        optional_fields = [
            'delay', 'priority', 'scheduled_task_id', 'routing'
        ]
        
        for field_name in optional_fields:
            value = getattr(self, field_name)
            if value is not None:
                # 对于空列表/字典，也不添加
                if isinstance(value, (list, dict)) and not value:
                    continue
                data[field_name] = value
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'TaskMessage':
        """
        从字典创建TaskMessage实例
        
        Args:
            data: 消息字典
            
        Returns:
            TaskMessage: 任务消息实例
        """
        # 提取构造函数需要的参数
        init_fields = {
            'queue', 'args', 'kwargs', 
            'delay', 'priority', 'scheduled_task_id', 'routing', 'trigger_time'
        }
        
        init_data = {k: v for k, v in data.items() if k in init_fields}
        return cls(**init_data)
    
    def validate(self) -> bool:
        """
        验证消息是否有效
        
        Returns:
            bool: 是否有效
            
        Raises:
            ValueError: 如果消息无效
        """
        if not self.queue:
            raise ValueError("Queue name is required")
        
        if self.delay and self.delay < 0:
            raise ValueError(f"Delay must be non-negative, got {self.delay}")
        
        if self.priority is not None and self.priority < 1:
            raise ValueError(f"Priority must be positive (1 is highest), got {self.priority}")
        
        return True
    
    def __repr__(self) -> str:
        """友好的字符串表示"""
        parts = [f"TaskMessage(queue='{self.queue}'"]
        
        if self.args:
            parts.append(f"args={self.args}")
        
        if self.kwargs:
            parts.append(f"kwargs={self.kwargs}")
        
        if self.delay:
            parts.append(f"delay={self.delay}s")
        
        return ", ".join(parts) + ")"