"""
定时任务数据模型
"""
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dataclasses import dataclass, field, asdict
from enum import Enum
from decimal import Decimal
import croniter


class TaskType(Enum):
    """任务类型"""
    ONCE = "once"        # 一次性任务
    INTERVAL = "interval"  # 间隔任务
    CRON = "cron"        # Cron表达式任务


class TaskStatus(Enum):
    """任务执行状态"""
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"


@dataclass
class ScheduledTask:
    """定时任务模型"""
    task_name: str                      # 要执行的函数名（对应@app.task注册的函数名）
    task_type: TaskType                 # 任务类型
    queue_name: str                     # 目标队列
    
    # 可选字段
    id: Optional[int] = None            # 数据库自增ID（唯一标识）
    scheduler_id: Optional[str] = None  # 任务的唯一标识符（用于去重）
    namespace: str = 'default'          # 命名空间
    task_args: List[Any] = field(default_factory=list)
    task_kwargs: Dict[str, Any] = field(default_factory=dict)
    cron_expression: Optional[str] = None
    interval_seconds: Optional[float] = None
    next_run_time: Optional[datetime] = None
    last_run_time: Optional[datetime] = None
    enabled: bool = True
    max_retries: int = 3
    retry_delay: int = 60
    timeout: int = 300
    priority: Optional[int] = None      # 任务优先级 (1=最高, 数字越大优先级越低，None=默认最低)
    description: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        # 转换枚举类型
        if isinstance(self.task_type, str):
            self.task_type = TaskType(self.task_type)
        
        # 验证配置
        self._validate()
        
        # 计算下次执行时间
        if self.next_run_time is None:
            self.next_run_time = self.calculate_next_run_time()
    
    def _validate(self):
        """验证任务配置"""
        if self.task_type == TaskType.CRON and not self.cron_expression:
            raise ValueError(f"Task {self.task_name} with type CRON must have cron_expression")
        
        if self.task_type == TaskType.INTERVAL and not self.interval_seconds:
            raise ValueError(f"Task {self.task_name} with type INTERVAL must have interval_seconds")
        
        # ONCE类型任务不应该有interval_seconds参数
        if self.task_type == TaskType.ONCE and self.interval_seconds is not None:
            raise ValueError(f"Task {self.task_name} with type ONCE should not have interval_seconds. Use next_run_time to specify when to run the task")
    
    def calculate_next_run_time(self, from_time: Optional[datetime] = None) -> Optional[datetime]:
        """计算下次执行时间"""
        if not self.enabled:
            return None
        
        from_time = from_time or datetime.now()
        
        if self.task_type == TaskType.ONCE:
            # 一次性任务，如果没有执行过就返回设定的时间
            if self.last_run_time is None:
                return self.next_run_time or from_time
            return None
        
        elif self.task_type == TaskType.INTERVAL:
            # 间隔任务
            if self.last_run_time:
                return self.last_run_time + timedelta(seconds=float(self.interval_seconds))
            return from_time
        
        elif self.task_type == TaskType.CRON:
            # Cron表达式任务
            cron = croniter.croniter(self.cron_expression, from_time)
            return cron.get_next(datetime)
        
        return None
    
    def update_next_run_time(self):
        """更新下次执行时间"""
        self.last_run_time = datetime.now()
        self.next_run_time = self.calculate_next_run_time(from_time=self.last_run_time)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['task_type'] = self.task_type.value
        
        # 转换datetime为字符串
        for key in ['next_run_time', 'last_run_time', 'created_at', 'updated_at']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        
        # 转换Decimal为float
        if data.get('interval_seconds') and isinstance(data['interval_seconds'], Decimal):
            data['interval_seconds'] = float(data['interval_seconds'])
        
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ScheduledTask':
        """从字典创建实例"""
        # 转换datetime字符串
        for key in ['next_run_time', 'last_run_time', 'created_at', 'updated_at']:
            if data.get(key) and isinstance(data[key], str):
                data[key] = datetime.fromisoformat(data[key])
        
        # 转换task_type为枚举
        if 'task_type' in data and isinstance(data['task_type'], str):
            data['task_type'] = TaskType(data['task_type'])
        
        # 转换interval_seconds为float（处理Decimal类型）
        if data.get('interval_seconds'):
            if isinstance(data['interval_seconds'], Decimal):
                data['interval_seconds'] = float(data['interval_seconds'])
        
        return cls(**data)
    
    def to_redis_value(self) -> str:
        """转换为Redis存储的值"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_redis_value(cls, value: str) -> 'ScheduledTask':
        """从Redis值创建实例"""
        return cls.from_dict(json.loads(value))


@dataclass
class TaskExecutionHistory:
    """任务执行历史"""
    task_id: int  # 对应 ScheduledTask 的 id
    event_id: str
    scheduled_time: datetime
    status: TaskStatus
    
    # 可选字段
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    result: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    retry_count: int = 0
    duration_ms: Optional[int] = None
    worker_id: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初始化后处理"""
        if isinstance(self.status, str):
            self.status = TaskStatus(self.status)
        
        if self.created_at is None:
            self.created_at = datetime.now()
        
        # 计算执行耗时
        if self.started_at and self.finished_at and self.duration_ms is None:
            delta = self.finished_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
    
    def to_dict(self) -> dict:
        """转换为字典"""
        data = asdict(self)
        data['status'] = self.status.value
        
        # 转换datetime为字符串
        for key in ['scheduled_time', 'started_at', 'finished_at', 'created_at']:
            if data.get(key):
                data[key] = data[key].isoformat() if isinstance(data[key], datetime) else data[key]
        
        return data