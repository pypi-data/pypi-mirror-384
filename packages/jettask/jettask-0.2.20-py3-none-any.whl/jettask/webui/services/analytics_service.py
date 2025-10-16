"""
分析服务层
处理数据分析相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class AnalyticsService:
    """分析服务类"""
    
    def __init__(self, namespace_data_access):
        """
        初始化分析服务
        
        Args:
            namespace_data_access: 命名空间数据访问实例
        """
        self.namespace_data_access = namespace_data_access
    
    async def get_namespaces(self) -> List[Dict[str, Any]]:
        """
        获取所有命名空间
        
        Returns:
            命名空间列表
        """
        return await self.namespace_data_access.get_all_namespaces()
    
    async def get_queue_stats(
        self,
        namespace: str
    ) -> List[Dict[str, Any]]:
        """
        获取队列统计信息
        
        Args:
            namespace: 命名空间
            
        Returns:
            队列统计数据
        """
        return await self.namespace_data_access.get_queue_stats(namespace)