"""
任务中心配置模块
明确区分：
1. 任务中心元数据库 - 存储命名空间、配置等管理数据
2. JetTask应用数据库 - 每个命名空间配置的Redis和PostgreSQL
"""
import os
from typing import Optional


class TaskCenterDatabaseConfig:
    """任务中心元数据库配置（用于存储命名空间等配置）"""
    
    def __init__(self):
        # 元数据库配置 - 从环境变量读取
        self.meta_db_host = os.getenv("TASK_CENTER_DB_HOST", "localhost")
        self.meta_db_port = int(os.getenv("TASK_CENTER_DB_PORT", "5432"))
        self.meta_db_user = os.getenv("TASK_CENTER_DB_USER", "jettask")  # 使用jettask作为默认用户
        self.meta_db_password = os.getenv("TASK_CENTER_DB_PASSWORD", "123456")  # 使用现有密码
        self.meta_db_name = os.getenv("TASK_CENTER_DB_NAME", "jettask")  # 使用现有数据库
        
        # API服务配置
        self.api_host = os.getenv("TASK_CENTER_API_HOST", "0.0.0.0")
        self.api_port = int(os.getenv("TASK_CENTER_API_PORT", "8001"))
        
        # 基础URL配置（用于生成connection_url）
        self.base_url = os.getenv("TASK_CENTER_BASE_URL", "http://localhost:8001")
    
    @property
    def meta_database_url(self) -> str:
        """获取元数据库连接URL"""
        return f"postgresql+asyncpg://{self.meta_db_user}:{self.meta_db_password}@{self.meta_db_host}:{self.meta_db_port}/{self.meta_db_name}"
    
    @property
    def sync_meta_database_url(self) -> str:
        """获取同步元数据库连接URL（用于初始化）"""
        return f"postgresql://{self.meta_db_user}:{self.meta_db_password}@{self.meta_db_host}:{self.meta_db_port}/{self.meta_db_name}"
    
    @property
    def pg_url(self) -> str:
        """获取PostgreSQL连接URL（兼容旧代码）"""
        return self.meta_database_url


# 全局配置实例
task_center_config = TaskCenterDatabaseConfig()


def get_task_center_config() -> TaskCenterDatabaseConfig:
    """获取任务中心配置"""
    return task_center_config