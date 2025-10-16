"""
命名空间管理路由
提供命名空间的增删改查和管理功能
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List
import logging
import traceback

from jettask.schemas import NamespaceCreate, NamespaceUpdate, NamespaceResponse
from jettask.webui.services.settings_service import SettingsService

logger = logging.getLogger(__name__)

# 创建独立的命名空间路由，设置 /namespaces 前缀
router = APIRouter(prefix="/namespaces", tags=["namespaces"])


@router.get("/", response_model=List[NamespaceResponse])
async def list_namespaces(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    is_active: Optional[bool] = None
):
    """
    列出所有命名空间
    
    Args:
        page: 页码（从1开始）
        page_size: 每页数量
        is_active: 是否只返回激活的命名空间
    """
    try:
        return await SettingsService.list_namespaces(page, page_size, is_active)
    except Exception as e:
        logger.error(f"获取命名空间列表失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", response_model=NamespaceResponse, status_code=201)
async def create_namespace(namespace: NamespaceCreate):
    """
    创建新的命名空间
    
    Args:
        namespace: 命名空间创建信息
    """
    try:
        return await SettingsService.create_namespace(namespace)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"创建命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{namespace_name}", response_model=NamespaceResponse)
async def get_namespace(namespace_name: str):
    """
    获取指定命名空间的详细信息
    
    Args:
        namespace_name: 命名空间名称
    """
    try:
        return await SettingsService.get_namespace(namespace_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/{namespace_name}", response_model=NamespaceResponse)
async def update_namespace(namespace_name: str, namespace: NamespaceUpdate):
    """
    更新命名空间配置
    
    Args:
        namespace_name: 命名空间名称
        namespace: 更新的配置信息
    """
    try:
        return await SettingsService.update_namespace(namespace_name, namespace)
    except ValueError as e:
        status_code = 404 if "不存在" in str(e) else 400
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"更新命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/{namespace_name}")
async def delete_namespace(namespace_name: str):
    """
    删除命名空间
    
    Args:
        namespace_name: 命名空间名称
    """
    try:
        return await SettingsService.delete_namespace(namespace_name)
    except ValueError as e:
        status_code = 400 if "默认命名空间" in str(e) else 404
        raise HTTPException(status_code=status_code, detail=str(e))
    except Exception as e:
        logger.error(f"删除命名空间失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/{namespace_name}/statistics")
async def get_namespace_statistics(namespace_name: str):
    """
    获取命名空间统计信息
    
    Args:
        namespace_name: 命名空间名称
    """
    try:
        return await SettingsService.get_namespace_statistics(namespace_name)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        logger.error(f"获取命名空间统计信息失败: {e}")
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

__all__ = ['router']