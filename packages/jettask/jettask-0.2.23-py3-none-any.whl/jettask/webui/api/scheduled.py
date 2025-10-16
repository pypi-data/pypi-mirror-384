"""
定时任务模块 - 定时任务管理、执行和监控
提供轻量级的路由入口，业务逻辑在 ScheduledTaskService 中实现
"""
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
import logging

from jettask.schemas import ScheduledTaskRequest
from jettask.webui.services.scheduled_task_service import ScheduledTaskService

router = APIRouter(prefix="/scheduled", tags=["scheduled"])
logger = logging.getLogger(__name__)


# ============ 定时任务管理 ============

@router.get("/")
async def get_scheduled_tasks(
    request: Request,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = Query(None, description="搜索关键字"),
    is_active: Optional[bool] = Query(None, description="是否激活")
):
    """
    获取定时任务列表
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        search: 搜索关键字
        is_active: 是否激活
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            tasks, total = await data_access.fetch_scheduled_tasks(
                session=session,
                page=page,
                page_size=page_size,
                search=search,
                is_active=is_active
            )
        
        return {
            "success": True,
            "data": tasks,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/filter")
async def get_scheduled_tasks_with_filters(request: Request):
    """
    获取定时任务列表（支持高级筛选）
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        # 解析请求体
        body = await request.json()
        
        page = body.get('page', 1)
        page_size = body.get('page_size', 20)
        search = body.get('search')
        is_active = body.get('is_active')
        filters = body.get('filters', [])
        time_range = body.get('time_range')
        start_time = body.get('start_time')
        end_time = body.get('end_time')
        
        async with data_access.get_session() as session:
            tasks, total = await data_access.fetch_scheduled_tasks(
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
    except Exception as e:
        logger.error(f"获取定时任务列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", status_code=201)
async def create_scheduled_task(request: Request, task_request: ScheduledTaskRequest):
    """
    创建定时任务
    
    Args:
        task_request: 定时任务创建请求
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        # 验证调度配置
        ScheduledTaskService.validate_schedule_config(
            task_request.schedule_type, 
            task_request.schedule_config
        )
        
        task_data = {
            "namespace": task_request.namespace,
            "name": task_request.name,
            "queue_name": task_request.queue_name,
            "task_data": task_request.task_data,
            "schedule_type": task_request.schedule_type,
            "schedule_config": task_request.schedule_config,
            "is_active": task_request.is_active,
            "description": task_request.description,
            "max_retry": task_request.max_retry,
            "timeout": task_request.timeout
        }
        
        async with data_access.get_session() as session:
            task = await data_access.create_scheduled_task(session, task_data)
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务创建成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{task_id}")
async def update_scheduled_task(request: Request, task_id: str, task_request: ScheduledTaskRequest):
    """
    更新定时任务
    
    Args:
        task_id: 任务ID
        task_request: 定时任务更新请求
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        # 验证调度配置
        ScheduledTaskService.validate_schedule_config(
            task_request.schedule_type,
            task_request.schedule_config
        )
        
        task_data = {
            "namespace": task_request.namespace,
            "name": task_request.name,
            "queue_name": task_request.queue_name,
            "task_data": task_request.task_data,
            "schedule_type": task_request.schedule_type,
            "schedule_config": task_request.schedule_config,
            "is_active": task_request.is_active,
            "description": task_request.description,
            "max_retry": task_request.max_retry,
            "timeout": task_request.timeout
        }
        
        async with data_access.get_session() as session:
            task = await data_access.update_scheduled_task(session, task_id, task_data)
        
        return {
            "success": True,
            "data": task,
            "message": "定时任务更新成功"
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{task_id}")
async def delete_scheduled_task(request: Request, task_id: str):
    """
    删除定时任务
    
    Args:
        task_id: 任务ID
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            success = await data_access.delete_scheduled_task(session, task_id)
        
        if success:
            return {
                "success": True,
                "message": f"定时任务 {task_id} 已删除"
            }
        else:
            raise HTTPException(status_code=404, detail="定时任务不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/toggle")
async def toggle_scheduled_task(request: Request, task_id: str):
    """
    启用/禁用定时任务
    
    Args:
        task_id: 任务ID
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            task = await data_access.toggle_scheduled_task(session, task_id)
        
        if task:
            return {
                "success": True,
                "data": {
                    "id": task["id"],
                    "is_active": task["enabled"]  # 映射 enabled 到 is_active
                },
                "message": "定时任务状态已更新"
            }
        else:
            raise HTTPException(status_code=404, detail="定时任务不存在")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"切换定时任务状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{task_id}/execute")
async def execute_scheduled_task_now(request: Request, task_id: str):
    """
    立即执行定时任务
    
    Args:
        task_id: 任务ID
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        if not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        data_access = app.state.data_access
        namespace_data_access = app.state.namespace_data_access
        
        # 调用服务层执行任务
        result = await ScheduledTaskService.execute_task_now(
            data_access,
            namespace_data_access,
            task_id
        )
        
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"执行定时任务失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 执行历史和统计 ============

@router.get("/{task_id}/history")
async def get_scheduled_task_history(
    request: Request,
    task_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    获取定时任务执行历史
    
    Args:
        task_id: 任务ID
        page: 页码
        page_size: 每页数量
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            history, total = await data_access.fetch_task_execution_history(
                session=session,
                task_id=task_id,
                page=page,
                page_size=page_size
            )
        
        return {
            "success": True,
            "data": history,
            "total": total,
            "page": page,
            "page_size": page_size
        }
    except Exception as e:
        logger.error(f"获取定时任务执行历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{task_id}/trend")
async def get_scheduled_task_execution_trend(
    request: Request,
    task_id: str,
    time_range: str = Query("7d", description="时间范围")
):
    """
    获取定时任务执行趋势
    
    Args:
        task_id: 任务ID
        time_range: 时间范围
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.get_session() as session:
            data = await data_access.fetch_task_execution_trend(
                session=session,
                task_id=task_id,
                time_range=time_range
            )
        
        return {
            "success": True,
            "data": data,
            "time_range": time_range
        }
    except Exception as e:
        logger.error(f"获取定时任务执行趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/statistics/{namespace}")
async def get_scheduled_tasks_statistics(request: Request, namespace: str):
    """
    获取定时任务统计数据
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        
        async with data_access.AsyncSessionLocal() as session:
            # 获取统计数据，传递命名空间参数
            stats = await data_access.get_scheduled_tasks_statistics(session, namespace)
            return stats
    except Exception as e:
        logger.error(f"获取定时任务统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']