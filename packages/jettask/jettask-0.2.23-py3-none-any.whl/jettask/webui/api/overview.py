"""
概览模块 - 系统总览、健康检查和仪表板统计
提供轻量级的路由入口，业务逻辑在 OverviewService 中实现
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
import traceback

from jettask.schemas import TimeRangeQuery
from jettask.webui.services.overview_service import OverviewService

logger = logging.getLogger(__name__)

# 创建概览路由，添加 /overview 前缀
router = APIRouter(prefix="/overview", tags=["overview"])


# ============ 健康检查和根路径 ============

@router.get("/")
async def root():
    """根路径"""
    return OverviewService.get_root_info()


@router.get("/health")
async def health_check():
    """健康检查"""
    return OverviewService.get_health_status()


# ============ 系统统计 ============

@router.get("/system-stats/{namespace}")
async def get_system_stats(namespace: str):
    """
    获取指定命名空间的系统统计信息
    
    Args:
        namespace: 命名空间名称
    """
    try:
        return await OverviewService.get_system_stats(namespace)
    except Exception as e:
        logger.error(f"获取系统统计信息失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============ 仪表板统计 ============

@router.get("/dashboard-stats/{namespace}")
async def get_dashboard_stats(
    namespace: str,
    time_range: str = "24h",
    queues: Optional[str] = Query(None, description="逗号分隔的队列名称列表")
):
    """
    获取仪表板统计数据（任务总数、成功数、失败数、成功率、吞吐量等）
    
    Args:
        namespace: 命名空间名称
        time_range: 时间范围（如'1h', '24h', '7d'）
        queues: 逗号分隔的队列名称列表
    """
    try:
        return await OverviewService.get_dashboard_stats(namespace, time_range, queues)
    except Exception as e:
        logger.error(f"获取仪表板统计数据失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# ============ 队列排行榜 ============

@router.get("/top-queues/{namespace}")
async def get_top_queues(
    namespace: str,
    metric: str = Query("backlog", description="指标类型: backlog(积压) 或 error(错误率)"),
    limit: int = 10,
    time_range: str = "24h",
    queues: Optional[str] = Query(None, description="逗号分隔的队列名称列表")
):
    """
    获取队列排行榜 - 支持积压和错误率两种指标
    
    Args:
        namespace: 命名空间名称
        metric: 指标类型 (backlog/error)
        limit: 返回的队列数量限制
        time_range: 时间范围
        queues: 逗号分隔的队列名称列表
    """
    try:
        return await OverviewService.get_top_queues(namespace, metric, limit, time_range, queues)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"获取队列排行榜失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



# ============ 概览统计数据 ============

@router.post("/dashboard-overview-stats/{namespace}")
async def get_dashboard_overview_stats(namespace: str, query: TimeRangeQuery):
    """
    获取概览页面的统一统计数据
    包含：任务处理趋势、任务并发数量、任务处理时间、任务执行延时
    
    Args:
        namespace: 命名空间名称
        query: 时间范围查询参数
    
    Returns:
        统一的时间序列数据，包含所有概览图表需要的指标和granularity字段
    """
    try:
        return await OverviewService.get_dashboard_overview_stats(namespace, query)
    except Exception as e:
        logger.error(f"获取概览统计数据失败: {e}")
        traceback.print_exc()
        # 返回空数据而不是抛出异常
        return {
            "task_trend": [],
            "concurrency": [],
            "processing_time": [],
            "creation_latency": [],
            "granularity": "minute"
        }


__all__ = ['router']