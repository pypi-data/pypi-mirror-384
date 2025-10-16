"""
设置模块 - 系统配置
提供轻量级的路由入口，业务逻辑在 SettingsService 中实现
"""
from fastapi import APIRouter, HTTPException
import logging
import traceback

from jettask.webui.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

# 创建设置模块路由，添加 /settings 前缀
router = APIRouter(prefix="/settings", tags=["settings"])


# ============ 系统配置接口 ============

@router.get("/system")
async def get_system_settings():
    """
    获取系统配置信息
    返回系统级别的配置，如数据库连接信息、API配置等
    """
    try:
        return SettingsService.get_system_settings()
    except Exception as e:
        logger.error(f"获取系统配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/database-status")
async def check_database_status():
    """
    检查数据库连接状态
    """
    try:
        return await SettingsService.check_database_status()
    except Exception as e:
        logger.error(f"数据库状态检查失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = ['router']