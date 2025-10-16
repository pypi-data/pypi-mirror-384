"""
队列模块 - 队列管理、任务处理、队列统计和监控
提供轻量级的路由入口，业务逻辑在 QueueService 中实现
"""
from fastapi import APIRouter, HTTPException, Request, Query, Depends
from typing import Optional, Dict, Any
from datetime import datetime
import logging

from jettask.schemas import (
    TimeRangeQuery, 
    TrimQueueRequest,
    TasksRequest,
    TaskActionRequest,
    BacklogTrendRequest
)
from jettask.webui.services.queue_service import QueueService
from jettask.webui.services.task_service import TaskService
from jettask.utils.redis_monitor import RedisMonitorService

router = APIRouter(prefix="/queues", tags=["queues"])
logger = logging.getLogger(__name__)


# ============ 队列基础管理 ============

@router.get("/{namespace}")
async def get_queues(request: Request, namespace: str):
    """
    获取指定命名空间的队列列表
    
    Args:
        namespace: 命名空间名称
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        return await QueueService.get_queues_by_namespace(namespace_data_access, namespace)
    except Exception as e:
        logger.error(f"获取队列列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/detail")
async def get_queues_detail(request: Request):
    """获取队列详细信息"""
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        return await QueueService.get_queues_detail(data_access)
    except Exception as e:
        logger.error(f"获取队列详细信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{queue_name}")
async def delete_queue(queue_name: str):
    """
    删除队列
    
    Args:
        queue_name: 队列名称
    """
    try:
        return await QueueService.delete_queue(queue_name)
    except Exception as e:
        logger.error(f"删除队列失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{queue_name}/trim")
async def trim_queue(queue_name: str, request: TrimQueueRequest):
    """
    裁剪队列到指定长度
    
    Args:
        queue_name: 队列名称
        request: 裁剪请求参数
    """
    try:
        return await QueueService.trim_queue(queue_name, request.max_length)
    except Exception as e:
        logger.error(f"裁剪队列失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 队列流量和统计 ============

@router.post("/flow-rates")
async def get_queue_flow_rates(request: Request):
    """
    获取单个队列的流量速率（入队、开始执行、完成）
    
    Args:
        request: FastAPI request对象，包含JSON body
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        # 解析请求体
        body = await request.json()
        
        # 创建TimeRangeQuery对象
        from jettask.schemas import TimeRangeQuery
        query = TimeRangeQuery(**body)
        
        data_access = app.state.data_access
        return await QueueService.get_queue_flow_rates(data_access, query)
    except Exception as e:
        logger.error(f"获取队列流量速率失败: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats")
async def get_global_stats(request: Request):
    """获取全局统计信息"""
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        return await QueueService.get_global_stats(data_access)
    except Exception as e:
        logger.error(f"获取全局统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stats-v2/{namespace}")
async def get_queue_stats_v2(
    request: Request,
    namespace: str,
    queue: Optional[str] = Query(None, description="队列名称"),
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
    time_range: Optional[str] = None
):
    """
    获取队列统计信息v2 - 支持消费者组详情和优先级队列
    
    Args:
        namespace: 命名空间
        queue: 可选，筛选特定队列
        start_time: 开始时间
        end_time: 结束时间
        time_range: 时间范围
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        return await QueueService.get_queue_stats_v2(
            namespace_data_access, namespace, queue, start_time, end_time, time_range
        )
    except Exception as e:
        logger.error(f"获取队列统计v2失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 消费者组统计 ============

@router.get("/consumer-groups/{namespace}/{group_name}/stats")
async def get_consumer_group_stats(request: Request, namespace: str, group_name: str):
    """
    获取特定消费者组的详细统计
    
    Args:
        namespace: 命名空间
        group_name: 消费者组名称
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        return await QueueService.get_consumer_group_stats(namespace_data_access, namespace, group_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取消费者组统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Stream积压监控 ============

@router.get("/stream-backlog/{namespace}")
async def get_stream_backlog(
    request: Request,
    namespace: str,
    stream_name: Optional[str] = Query(None, description="Stream名称"),
    hours: int = Query(24, description="查询最近多少小时的数据")
):
    """
    获取Stream积压监控数据
    
    Args:
        namespace: 命名空间
        stream_name: 可选，指定stream名称
        hours: 查询最近多少小时的数据
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        return await QueueService.get_stream_backlog(data_access, namespace, stream_name, hours)
    except Exception as e:
        logger.error(f"获取Stream积压监控数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/stream-backlog/{namespace}/summary")
async def get_stream_backlog_summary(request: Request, namespace: str):
    """
    获取Stream积压监控汇总数据
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        return await QueueService.get_stream_backlog_summary(data_access, namespace)
    except Exception as e:
        logger.error(f"获取Stream积压监控汇总失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 队列积压监控 ============

@router.post("/backlog/latest/{namespace}")
async def get_latest_backlog(request: Request, namespace: str):
    """
    获取最新的队列积压数据快照
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        data_access = app.state.data_access
        body = await request.json() if await request.body() else {}
        queues = body.get('queues', [])
        
        # TODO: 调用QueueService的积压监控方法
        return {
            "success": True,
            "namespace": namespace,
            "queues": queues,
            "data": [],
            "timestamp": datetime.now().isoformat(),
            "message": "Backlog monitoring endpoint placeholder"
        }
    except Exception as e:
        logger.error(f"获取最新积压数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/backlog/trend/{namespace}")
async def get_backlog_trend(request: Request, namespace: str):
    """
    获取队列积压趋势数据
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'data_access'):
            raise HTTPException(status_code=500, detail="Data access not initialized")
        
        # 解析请求体
        body = await request.json() if await request.body() else {}
        
        # 从请求体中获取参数，namespace从路径参数获取
        time_range = body.get('time_range', '1h')
        queue_name = body.get('queue_name')
        interval = body.get('interval', '5m')
        metrics = body.get('metrics', ["pending", "processing", "completed", "failed"])
        
        # TODO: 调用QueueService的积压趋势方法
        return {
            "success": True,
            "namespace": namespace,
            "time_range": time_range,
            "queue_name": queue_name,
            "interval": interval,
            "data": [],
            "statistics": {},
            "granularity": "minute"
        }
    except Exception as e:
        logger.error(f"获取积压趋势失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 任务管理 ============

def get_task_service(request: Request) -> TaskService:
    """获取任务服务实例"""
    if not hasattr(request.app.state, 'data_access'):
        raise HTTPException(status_code=500, detail="Data access not initialized")
    return TaskService(request.app.state.data_access)


@router.post("/tasks")
async def get_tasks(
    request: TasksRequest,
    service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """
    获取队列的任务列表
    
    支持灵活筛选和时间范围查询
    """
    try:
        return await service.get_tasks_with_filters(
            queue_name=request.queue_name,
            page=request.page,
            page_size=request.page_size,
            filters=request.filters,
            time_range=request.time_range,
            start_time=request.start_time,
            end_time=request.end_time
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/tasks")
async def get_tasks_legacy(
    queue_name: str,
    page: int = 1,
    page_size: int = 20,
    status: Optional[str] = None,
    task_id: Optional[str] = None,
    worker_id: Optional[str] = None,
    service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """
    获取队列的任务列表（向后兼容旧版本）
    """
    # 构建筛选条件
    filters = []
    if status:
        filters.append({'field': 'status', 'operator': 'eq', 'value': status})
    if task_id:
        filters.append({'field': 'id', 'operator': 'eq', 'value': task_id})
    if worker_id:
        filters.append({'field': 'worker_id', 'operator': 'eq', 'value': worker_id})
    
    try:
        return await service.get_tasks_with_filters(
            queue_name=queue_name,
            page=page,
            page_size=page_size,
            filters=filters
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/task/{task_id}/details")
async def get_task_details(
    task_id: str,
    consumer_group: Optional[str] = None,
    service: TaskService = Depends(get_task_service)
) -> Dict[str, Any]:
    """
    获取单个任务的详细数据
    
    包括task_data和result
    """
    try:
        task_details = await service.get_task_details(task_id, consumer_group)
        return {
            "success": True,
            "data": task_details
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/tasks-v2/{namespace}")
async def get_tasks_v2(request: Request, namespace: str):
    """
    获取任务列表v2 - 支持tasks和task_runs表连表查询
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        
        # 解析请求体
        body = await request.json()
        
        return await QueueService.get_tasks_v2(namespace_data_access, namespace, body)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取任务列表v2失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ Redis监控 ============

@router.get("/redis/monitor/{namespace}")
async def get_redis_monitor(request: Request, namespace: str):
    """
    获取Redis性能监控数据
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_redis_monitor_data(namespace)
    except Exception as e:
        logger.error(f"获取Redis监控数据失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/slow-log/{namespace}")
async def get_redis_slow_log(
    request: Request,
    namespace: str,
    limit: int = Query(10, description="返回记录数")
):
    """
    获取Redis慢查询日志
    
    Args:
        namespace: 命名空间
        limit: 返回记录数
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_slow_log(namespace, limit)
    except Exception as e:
        logger.error(f"获取Redis慢查询日志失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/command-stats/{namespace}")
async def get_redis_command_stats(request: Request, namespace: str):
    """
    获取Redis命令统计
    
    Args:
        namespace: 命名空间
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_command_stats(namespace)
    except Exception as e:
        logger.error(f"获取Redis命令统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/redis/stream-stats/{namespace}")
async def get_redis_stream_stats(
    request: Request,
    namespace: str,
    stream_name: Optional[str] = Query(None, description="Stream名称")
):
    """
    获取Redis Stream统计
    
    Args:
        namespace: 命名空间
        stream_name: 可选，指定stream名称
    """
    try:
        app = request.app
        if not app or not hasattr(app.state, 'namespace_data_access'):
            raise HTTPException(status_code=500, detail="Namespace data access not initialized")
        
        namespace_data_access = app.state.namespace_data_access
        redis_monitor_service = RedisMonitorService(namespace_data_access)
        return await redis_monitor_service.get_stream_stats(namespace, stream_name)
    except Exception as e:
        logger.error(f"获取Redis Stream统计失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']