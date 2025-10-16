"""
定时任务服务层
处理定时任务相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ScheduledTaskService:
    """定时任务服务类"""
    
    def __init__(self, data_access):
        """
        初始化定时任务服务
        
        Args:
            data_access: 数据访问层实例
        """
        self.data_access = data_access
    
    @staticmethod
    def validate_schedule_config(schedule_type: str, schedule_config: dict):
        """
        验证调度配置
        
        Args:
            schedule_type: 调度类型
            schedule_config: 调度配置
            
        Raises:
            ValueError: 配置无效时
        """
        if schedule_type == 'interval':
            if 'seconds' in schedule_config:
                seconds = schedule_config.get('seconds')
                if seconds is None or seconds <= 0:
                    raise ValueError(f"间隔时间必须大于0秒，当前值: {seconds}")
                if seconds < 1:
                    raise ValueError(
                        f"间隔时间不能小于1秒，当前值: {seconds}秒。"
                        f"小于1秒的高频任务可能影响系统性能"
                    )
            elif 'minutes' in schedule_config:
                minutes = schedule_config.get('minutes')
                if minutes is None or minutes <= 0:
                    raise ValueError(f"间隔时间必须大于0分钟，当前值: {minutes}")
            else:
                raise ValueError("interval类型的任务必须指定seconds或minutes")
        elif schedule_type == 'cron':
            if 'cron_expression' not in schedule_config:
                raise ValueError("cron类型的任务必须指定cron_expression")
    
    async def get_scheduled_tasks(
        self,
        page: int = 1,
        page_size: int = 20,
        search: Optional[str] = None,
        is_active: Optional[bool] = None,
        filters: Optional[List[Dict]] = None,
        time_range: Optional[str] = None,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取定时任务列表
        
        Args:
            page: 页码
            page_size: 每页大小
            search: 搜索关键字
            is_active: 是否激活
            filters: 筛选条件
            time_range: 时间范围
            start_time: 开始时间
            end_time: 结束时间
            
        Returns:
            任务列表和总数
        """
        async with self.data_access.get_session() as session:
            tasks, total = await self.data_access.fetch_scheduled_tasks(
                session=session,
                page=page,
                page_size=page_size,
                search=search,
                is_active=is_active,
                filters=filters,
                time_range=time_range,
                start_time=start_time,
                end_time=end_time
            )
        
        return {
            "success": True,
            "data": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    
    async def create_scheduled_task(
        self,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        创建定时任务
        
        Args:
            task_data: 任务数据
            
        Returns:
            创建的任务信息
        """
        # 验证调度配置
        self.validate_schedule_config(
            task_data['schedule_type'],
            task_data['schedule_config']
        )
        
        async with self.data_access.get_session() as session:
            task = await self.data_access.create_scheduled_task(session, task_data)
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务创建成功"
        }
    
    async def update_scheduled_task(
        self,
        task_id: str,
        task_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        更新定时任务
        
        Args:
            task_id: 任务ID
            task_data: 任务数据
            
        Returns:
            更新后的任务信息
        """
        # 验证调度配置
        self.validate_schedule_config(
            task_data['schedule_type'],
            task_data['schedule_config']
        )
        
        async with self.data_access.get_session() as session:
            task = await self.data_access.update_scheduled_task(
                session, task_id, task_data
            )
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务更新成功"
        }
    
    async def delete_scheduled_task(self, task_id: str) -> Dict[str, Any]:
        """
        删除定时任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            操作结果
        """
        async with self.data_access.get_session() as session:
            success = await self.data_access.delete_scheduled_task(session, task_id)
        
        if success:
            return {
                "success": True,
                "message": f"定时任务 {task_id} 已删除"
            }
        else:
            raise ValueError("定时任务不存在")
    
    async def toggle_scheduled_task(self, task_id: str) -> Dict[str, Any]:
        """
        启用/禁用定时任务
        
        Args:
            task_id: 任务ID
            
        Returns:
            更新后的状态
        """
        async with self.data_access.get_session() as session:
            task = await self.data_access.toggle_scheduled_task(session, task_id)
        
        if task:
            return {
                "success": True,
                "data": {
                    "id": task["id"],
                    "is_active": task["enabled"]
                },
                "message": "定时任务状态已更新"
            }
        else:
            raise ValueError("定时任务不存在")