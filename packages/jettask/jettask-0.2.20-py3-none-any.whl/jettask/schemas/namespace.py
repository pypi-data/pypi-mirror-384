"""
命名空间相关的数据模型
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class ConfigMode(str, Enum):
    """配置模式枚举"""
    DIRECT = "direct"  # 直接配置模式（自由输入）
    NACOS = "nacos"    # Nacos配置模式


class NamespaceCreate(BaseModel):
    """创建命名空间请求模型"""
    name: str = Field(..., description="命名空间名称")
    description: Optional[str] = Field(None, description="命名空间描述")
    
    # 配置模式
    config_mode: ConfigMode = Field(ConfigMode.DIRECT, description="配置模式: direct(直接配置) 或 nacos(Nacos配置)")
    
    # Redis配置 - 支持两种方式
    # 方式1: 直接配置字符串 (格式: redis://[password@]host:port/db)
    redis_url: Optional[str] = Field(None, description="Redis连接字符串，格式: redis://[password@]host:port/db")
    # 方式2: Nacos配置键
    redis_nacos_key: Optional[str] = Field(None, description="Redis连接字符串的Nacos配置键")
    
    # PostgreSQL配置 - 支持两种方式
    # 方式1: 直接配置字符串 (格式: postgresql://user:password@host:port/database)
    pg_url: Optional[str] = Field(None, description="PostgreSQL连接字符串，格式: postgresql://user:password@host:port/database")
    # 方式2: Nacos配置键
    pg_nacos_key: Optional[str] = Field(None, description="PostgreSQL连接字符串的Nacos配置键")


class NamespaceUpdate(BaseModel):
    """更新命名空间请求模型"""
    description: Optional[str] = Field(None, description="命名空间描述")
    
    # 配置模式
    config_mode: Optional[ConfigMode] = Field(None, description="配置模式: direct(直接配置) 或 nacos(Nacos配置)")
    
    # Redis配置 - 支持两种方式
    redis_url: Optional[str] = Field(None, description="Redis连接字符串，格式: redis://[password@]host:port/db")
    redis_nacos_key: Optional[str] = Field(None, description="Redis连接字符串的Nacos配置键")
    
    # PostgreSQL配置 - 支持两种方式
    pg_url: Optional[str] = Field(None, description="PostgreSQL连接字符串，格式: postgresql://user:password@host:port/database")
    pg_nacos_key: Optional[str] = Field(None, description="PostgreSQL连接字符串的Nacos配置键")
    
    enabled: Optional[bool] = Field(None, description="是否启用")


class NamespaceResponse(BaseModel):
    """命名空间响应模型"""
    name: str = Field(..., description="命名空间名称")
    description: Optional[str] = Field(None, description="命名空间描述")
    
    # Redis配置信息 - 只返回最终的URL
    redis_url: str = Field(..., description="Redis连接字符串")
    
    # PostgreSQL配置信息 - 只返回最终的URL
    pg_url: Optional[str] = Field(None, description="PostgreSQL连接字符串")
    
    # 连接信息
    connection_url: str = Field(..., description="用于连接此命名空间的URL路径")
    version: int = Field(default=1, description="配置版本号")
    
    enabled: bool = Field(..., description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NamespaceInfo(BaseModel):
    """命名空间详细信息模型"""
    name: str = Field(..., description="命名空间名称")
    description: Optional[str] = Field(None, description="命名空间描述")
    redis_config: Dict[str, Any] = Field(..., description="Redis配置")
    status: str = Field(..., description="状态")
    enabled: bool = Field(default=True, description="是否启用")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    last_activity: Optional[datetime] = Field(None, description="最后活动时间")
    
    # 统计信息
    total_queues: int = Field(default=0, description="总队列数")
    total_tasks: int = Field(default=0, description="总任务数")
    active_workers: int = Field(default=0, description="活跃工作节点数")
    pending_tasks: int = Field(default=0, description="待处理任务数")
    processing_tasks: int = Field(default=0, description="处理中任务数")
    completed_tasks: int = Field(default=0, description="已完成任务数")
    failed_tasks: int = Field(default=0, description="失败任务数")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }


class NamespaceCreateRequest(BaseModel):
    """命名空间创建请求模型（详细版）"""
    name: str = Field(..., min_length=1, max_length=100, description="命名空间名称")
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=1000, description="命名空间描述")
    
    # Redis连接配置
    redis_host: str = Field(..., description="Redis主机地址")
    redis_port: int = Field(..., ge=1, le=65535, description="Redis端口号")
    redis_db: int = Field(default=0, ge=0, le=15, description="Redis数据库编号")
    redis_password: Optional[str] = Field(None, description="Redis密码")
    redis_ssl: bool = Field(default=False, description="是否使用SSL连接")
    redis_ssl_cert_reqs: Optional[str] = Field(None, description="SSL证书验证")
    redis_ssl_ca_certs: Optional[str] = Field(None, description="SSL CA证书路径")
    redis_ssl_certfile: Optional[str] = Field(None, description="SSL客户端证书路径")
    redis_ssl_keyfile: Optional[str] = Field(None, description="SSL私钥路径")
    
    # 连接池配置
    redis_max_connections: int = Field(default=50, ge=1, le=1000, description="最大连接数")
    redis_connection_timeout: int = Field(default=30, ge=1, description="连接超时（秒）")
    redis_socket_timeout: int = Field(default=30, ge=1, description="套接字超时（秒）")
    
    # 业务配置
    default_queue_prefix: str = Field(default="task", description="默认队列前缀")
    max_queue_size: Optional[int] = Field(None, ge=1, description="队列最大大小")
    task_ttl: int = Field(default=86400, ge=60, description="任务TTL（秒）")
    result_ttl: int = Field(default=3600, ge=60, description="结果TTL（秒）")
    
    # 其他设置
    enabled: bool = Field(default=True, description="是否启用")
    auto_create_queues: bool = Field(default=True, description="是否自动创建队列")
    tags: List[str] = Field(default=[], description="标签列表")
    metadata: Dict[str, Any] = Field(default={}, description="元数据")


class NamespaceUpdateRequest(BaseModel):
    """命名空间更新请求模型（详细版）"""
    display_name: Optional[str] = Field(None, max_length=200, description="显示名称")
    description: Optional[str] = Field(None, max_length=1000, description="命名空间描述")
    
    # Redis连接配置
    redis_host: Optional[str] = Field(None, description="Redis主机地址")
    redis_port: Optional[int] = Field(None, ge=1, le=65535, description="Redis端口号")
    redis_db: Optional[int] = Field(None, ge=0, le=15, description="Redis数据库编号")
    redis_password: Optional[str] = Field(None, description="Redis密码")
    redis_ssl: Optional[bool] = Field(None, description="是否使用SSL连接")
    
    # 连接池配置
    redis_max_connections: Optional[int] = Field(None, ge=1, le=1000, description="最大连接数")
    redis_connection_timeout: Optional[int] = Field(None, ge=1, description="连接超时（秒）")
    redis_socket_timeout: Optional[int] = Field(None, ge=1, description="套接字超时（秒）")
    
    # 业务配置
    default_queue_prefix: Optional[str] = Field(None, description="默认队列前缀")
    max_queue_size: Optional[int] = Field(None, ge=1, description="队列最大大小")
    task_ttl: Optional[int] = Field(None, ge=60, description="任务TTL（秒）")
    result_ttl: Optional[int] = Field(None, ge=60, description="结果TTL（秒）")
    
    # 其他设置
    enabled: Optional[bool] = Field(None, description="是否启用")
    auto_create_queues: Optional[bool] = Field(None, description="是否自动创建队列")
    tags: Optional[List[str]] = Field(None, description="标签列表")
    metadata: Optional[Dict[str, Any]] = Field(None, description="元数据")