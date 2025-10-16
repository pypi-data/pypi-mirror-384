"""
任务服务层
处理任务相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)


class TaskService:
    """任务服务类"""
    
    def __init__(self, data_access):
        """
        初始化任务服务
        
        Args:
            data_access: 数据访问层实例
        """
        self.data_access = data_access
    
    async def get_tasks_with_filters(
        self,
        queue_name: str,
        page: int = 1,
        page_size: int = 20,
        filters: Optional[List[Dict]] = None,
        time_range: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        获取任务列表（支持灵活筛选和时间范围）
        
        Args:
            queue_name: 队列名称
            page: 页码
            page_size: 每页大小
            filters: 筛选条件
            time_range: 时间范围字符串
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            任务列表结果
        """
        # 处理时间范围
        if not start_time or not end_time:
            if time_range:
                start_time, end_time = await self._calculate_time_range(
                    time_range, queue_name
                )
        
        # 转换时间格式
        if start_time and isinstance(start_time, str):
            start_time = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
        if end_time and isinstance(end_time, str):
            end_time = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        
        logger.info(
            f"获取队列 {queue_name} 的任务列表, "
            f"页码: {page}, 每页: {page_size}, "
            f"筛选条件: {filters}, "
            f"时间范围: {start_time} - {end_time}"
        )
        
        # 调用数据访问层
        return await self.data_access.fetch_tasks_with_filters(
            queue_name=queue_name,
            page=page,
            page_size=page_size,
            filters=filters or [],
            start_time=start_time,
            end_time=end_time
        )
    
    async def get_task_details(
        self, 
        task_id: str,
        consumer_group: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取任务详细信息
        
        Args:
            task_id: 任务ID
            consumer_group: 消费者组名称（可选）
            
        Returns:
            任务详细信息
            
        Raises:
            ValueError: 当任务不存在时
        """
        logger.info(
            f"获取任务 {task_id} 的详细数据, "
            f"consumer_group={consumer_group}"
        )
        
        task_details = await self.data_access.fetch_task_details(
            task_id, consumer_group
        )
        
        if not task_details:
            raise ValueError(f"Task {task_id} not found")
        
        return task_details
    
    async def _calculate_time_range(
        self,
        time_range: str,
        queue_name: str
    ) -> tuple[datetime, datetime]:
        """
        计算时间范围
        
        Args:
            time_range: 时间范围字符串 (如 "15m", "1h", "7d")
            queue_name: 队列名称
            
        Returns:
            (开始时间, 结束时间) 元组
        """
        now = datetime.now(timezone.utc)
        
        time_range_map = {
            "15m": timedelta(minutes=15),
            "30m": timedelta(minutes=30),
            "1h": timedelta(hours=1),
            "3h": timedelta(hours=3),
            "6h": timedelta(hours=6),
            "12h": timedelta(hours=12),
            "24h": timedelta(hours=24),
            "7d": timedelta(days=7),
            "30d": timedelta(days=30),
        }
        
        delta = time_range_map.get(time_range, timedelta(minutes=15))
        
        # 获取队列的最新任务时间
        latest_time = await self.data_access.get_latest_task_time(queue_name)
        if latest_time:
            # 使用最新任务时间作为结束时间
            end_time = latest_time.replace(second=59, microsecond=999999)
            logger.info(f"使用最新任务时间: {latest_time}")
        else:
            # 如果没有任务，使用当前时间
            end_time = now.replace(second=0, microsecond=0)
        
        start_time = end_time - delta
        logger.info(
            f"使用时间范围 {time_range}: {start_time} 到 {end_time}"
        )
        
        return start_time, end_time