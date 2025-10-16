"""
告警管理路由
提供轻量级的路由入口，业务逻辑在 AlertService 中实现
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging

from jettask.schemas import AlertRuleRequest
from jettask.webui.services.alert_service import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)


@router.get("/rules")
async def get_alert_rules(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None
):
    """
    获取告警规则列表
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        is_active: 是否只返回激活的规则
    """
    try:
        return AlertService.get_alert_rules(page, page_size, is_active)
    except Exception as e:
        logger.error(f"获取告警规则列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules", status_code=201)
async def create_alert_rule(request: AlertRuleRequest):
    """
    创建告警规则
    
    Args:
        request: 告警规则请求数据
    """
    try:
        return AlertService.create_alert_rule(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rules/{rule_id}")
async def update_alert_rule(rule_id: str, request: AlertRuleRequest):
    """
    更新告警规则
    
    Args:
        rule_id: 规则ID
        request: 告警规则请求数据
    """
    try:
        return AlertService.update_alert_rule(rule_id, request)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"更新告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rules/{rule_id}")
async def delete_alert_rule(rule_id: str):
    """
    删除告警规则
    
    Args:
        rule_id: 规则ID
    """
    try:
        return AlertService.delete_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"删除告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/toggle")
async def toggle_alert_rule(rule_id: str):
    """
    启用/禁用告警规则
    
    Args:
        rule_id: 规则ID
    """
    try:
        return AlertService.toggle_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"切换告警规则状态失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rules/{rule_id}/history")
async def get_alert_history(
    rule_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100)
):
    """
    获取告警触发历史
    
    Args:
        rule_id: 规则ID
        page: 页码（从1开始）
        page_size: 每页数量
    """
    try:
        return AlertService.get_alert_history(rule_id, page, page_size)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取告警历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/rules/{rule_id}/test")
async def test_alert_rule(rule_id: str):
    """
    测试告警规则（发送测试通知）
    
    Args:
        rule_id: 规则ID
    """
    try:
        return AlertService.test_alert_rule(rule_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"测试告警规则失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 告警统计接口 ============

@router.get("/statistics")
async def get_alert_statistics(
    namespace: Optional[str] = Query(None, description="命名空间名称")
):
    """
    获取告警统计信息
    
    Args:
        namespace: 命名空间名称（可选）
    """
    try:
        return AlertService.get_alert_statistics(namespace)
    except Exception as e:
        logger.error(f"获取告警统计信息失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============ 活跃告警管理 ============

@router.get("/active")
async def get_active_alerts(
    namespace: Optional[str] = Query(None, description="命名空间名称")
):
    """
    获取当前活跃的告警
    
    Args:
        namespace: 命名空间名称（可选）
    """
    try:
        return AlertService.get_active_alerts(namespace)
    except Exception as e:
        logger.error(f"获取活跃告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/active/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    user: str = Query("system", description="确认用户")
):
    """
    确认告警
    
    Args:
        alert_id: 告警ID
        user: 确认用户
    """
    try:
        return AlertService.acknowledge_alert(alert_id, user)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"确认告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/active/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    resolution_note: Optional[str] = Query(None, description="解决说明")
):
    """
    解决告警
    
    Args:
        alert_id: 告警ID
        resolution_note: 解决说明（可选）
    """
    try:
        return AlertService.resolve_alert(alert_id, resolution_note)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"解决告警失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']