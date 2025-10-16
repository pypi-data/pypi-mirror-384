"""
任务中心数据模型
"""
from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime
import uuid


@dataclass
class Namespace:
    """命名空间模型"""
    id: int  # 自增整数ID
    name: str  # 唯一的命名空间名称
    connection_url: str  # 专属连接URL
    redis_config: Dict[str, Any]  # Redis配置
    pg_config: Dict[str, Any]  # PostgreSQL配置
    created_at: datetime
    updated_at: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    @classmethod
    def create(cls, name: str, redis_config: Dict, pg_config: Dict) -> 'Namespace':
        """创建新的命名空间"""
        # 使用名称作为URL，更直观
        connection_url = f"/api/namespaces/{name}"
        return cls(
            id=0,  # 将由数据库自动分配
            name=name,
            connection_url=connection_url,
            redis_config=redis_config,
            pg_config=pg_config,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )


@dataclass
class TaskCenterConfig:
    """任务中心配置"""
    task_center_url: Optional[str] = None  # 任务中心连接URL
    namespace_id: Optional[str] = None  # 从URL解析出的命名空间ID
    namespace_name: Optional[str] = None  # 命名空间名称
    
    @property
    def is_enabled(self) -> bool:
        """是否启用任务中心"""
        return self.task_center_url is not None
    
    @classmethod
    def from_url(cls, url: str) -> 'TaskCenterConfig':
        """从连接URL创建配置"""
        if not url or not url.startswith("taskcenter://"):
            return cls()
        
        # 解析URL: taskcenter://namespace/{namespace_id}
        parts = url.replace("taskcenter://", "").split("/")
        if len(parts) >= 2 and parts[0] == "namespace":
            return cls(
                task_center_url=url,
                namespace_id=parts[1]
            )
        return cls(task_center_url=url)