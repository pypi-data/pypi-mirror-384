"""
设置服务
提供系统设置、配置管理等功能
"""
import json
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy import text
from urllib.parse import urlparse

from jettask.persistence.db_manager import get_db_manager
from jettask.schemas import (
    ConfigMode,
    NamespaceCreate,
    NamespaceUpdate,
    NamespaceResponse
)

logger = logging.getLogger(__name__)


class SettingsService:
    """设置服务类"""
    
    @staticmethod
    def validate_redis_url(redis_url: str) -> bool:
        """
        验证 Redis URL 格式
        格式: redis://[password@]host:port/db
        """
        try:
            parsed = urlparse(redis_url)
            return parsed.scheme in ['redis', 'rediss']
        except:
            return False
    
    @staticmethod
    def validate_pg_url(pg_url: str) -> bool:
        """
        验证 PostgreSQL URL 格式
        支持格式: 
        - postgresql://user:password@host:port/database
        - postgresql+asyncpg://user:password@host:port/database
        - postgres://user:password@host:port/database
        """
        try:
            parsed = urlparse(pg_url)
            return parsed.scheme in ['postgresql', 'postgres', 'postgresql+asyncpg']
        except:
            return False
    
    @staticmethod
    def mask_url_password(url: str) -> str:
        """
        将URL中的密码部分替换为星号
        """
        try:
            parsed = urlparse(url)
            if parsed.password:
                # 构建脱敏后的URL
                if parsed.username:
                    netloc = f"{parsed.username}:***@{parsed.hostname}"
                else:
                    netloc = f"***@{parsed.hostname}"
                
                if parsed.port:
                    netloc += f":{parsed.port}"
                    
                masked_url = f"{parsed.scheme}://{netloc}{parsed.path}"
                if parsed.query:
                    masked_url += f"?{parsed.query}"
                if parsed.fragment:
                    masked_url += f"#{parsed.fragment}"
                    
                return masked_url
            return url
        except:
            return url
     
    @staticmethod
    async def get_config_from_nacos(key: str) -> str:
        """
        从 Nacos 获取配置值（应该返回URL格式的字符串）
        """
        try:
            from jettask.config.nacos_config import config
            value = config.config.get(key)
            if not value:
                raise ValueError(f"Nacos配置键 '{key}' 不存在或为空")
            return value
        except ImportError:
            raise ValueError("无法加载Nacos配置模块")
        except Exception as e:
            raise ValueError(f"从Nacos获取配置失败: {str(e)}")
    
    @staticmethod
    async def list_namespaces(
        page: int = 1,
        page_size: int = 20,
        is_active: Optional[bool] = None
    ) -> List[NamespaceResponse]:
        """
        列出所有命名空间
        
        Args:
            page: 页码（从1开始）
            page_size: 每页数量
            is_active: 是否只返回激活的命名空间
            
        Returns:
            命名空间列表
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            query = """
                SELECT id, name, description, redis_config, pg_config, 
                       is_active, version, created_at, updated_at
                FROM namespaces
            """
            params = {}
            
            if is_active is not None:
                query += " WHERE is_active = :is_active"
                params['is_active'] = is_active
            
            query += " ORDER BY created_at DESC"
            query += " LIMIT :limit OFFSET :offset"
            params['limit'] = page_size
            params['offset'] = (page - 1) * page_size
            
            result = await session.execute(text(query), params)
            rows = result.fetchall()
            
            namespaces = []
            for row in rows:
                # 构建响应
                redis_config_dict = row.redis_config if row.redis_config else {}
                pg_config_dict = row.pg_config if row.pg_config else {}
                
                # 根据配置模式获取实际的URL
                config_mode = redis_config_dict.get('config_mode', 'direct')
                
                # 获取Redis URL
                if config_mode == 'nacos' and redis_config_dict.get('nacos_key'):
                    try:
                        redis_url = await SettingsService.get_config_from_nacos(redis_config_dict['nacos_key'])
                    except Exception as e:
                        logger.error(f"从Nacos获取Redis URL失败: {e} {row.name}")
                        redis_url = redis_config_dict.get('url', '')
                else:
                    redis_url = redis_config_dict.get('url', '')
                
                # 获取PostgreSQL URL
                pg_url = None
                if config_mode == 'nacos' and pg_config_dict.get('nacos_key'):
                    try:
                        pg_url = await SettingsService.get_config_from_nacos(pg_config_dict['nacos_key'])
                    except Exception as e:
                        logger.error(f"从Nacos获取PostgreSQL URL失败: {e} {row.name}")
                        pg_url = pg_config_dict.get('url')
                else:
                    pg_url = pg_config_dict.get('url')
                
                response = NamespaceResponse(
                    name=row.name,
                    description=row.description,
                    redis_url=redis_url,
                    pg_url=pg_url,
                    connection_url=f"/api/v1/namespaces/{row.name}",
                    version=row.version or 1,
                    enabled=row.is_active,
                    created_at=row.created_at,
                    updated_at=row.updated_at
                )
                namespaces.append(response)
            
            return namespaces
    
    @staticmethod
    async def create_namespace(namespace: NamespaceCreate) -> NamespaceResponse:
        """
        创建新的命名空间
        
        Args:
            namespace: 命名空间创建信息
            
        Returns:
            创建的命名空间信息
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 检查命名空间是否已存在
            check_query = text("SELECT COUNT(*) FROM namespaces WHERE name = :name")
            result = await session.execute(check_query, {'name': namespace.name})
            if result.scalar() > 0:
                raise ValueError(f"命名空间 '{namespace.name}' 已存在")
            
            # 准备配置
            redis_config = {'config_mode': namespace.config_mode.value}
            pg_config = {'config_mode': namespace.config_mode.value}
            
            # 根据配置模式处理
            if namespace.config_mode == ConfigMode.DIRECT:
                # 直接配置模式
                if not namespace.redis_url:
                    raise ValueError("直接配置模式下，redis_url是必需的")
                if namespace.redis_nacos_key:
                    raise ValueError("直接配置模式下不应提供redis_nacos_key")
                
                # 验证URL格式
                if not SettingsService.validate_redis_url(namespace.redis_url):
                    raise ValueError("无效的Redis URL格式")
                
                redis_config['url'] = namespace.redis_url
                
                # 处理PostgreSQL配置（可选）
                if namespace.pg_url:
                    if not SettingsService.validate_pg_url(namespace.pg_url):
                        raise ValueError("无效的PostgreSQL URL格式")
                    pg_config['url'] = namespace.pg_url
                if namespace.pg_nacos_key:
                    raise ValueError("直接配置模式下不应提供pg_nacos_key")
                    
            elif namespace.config_mode == ConfigMode.NACOS:
                # Nacos配置模式
                if not namespace.redis_nacos_key:
                    raise ValueError("Nacos配置模式下，redis_nacos_key是必需的")
                if namespace.redis_url:
                    raise ValueError("Nacos配置模式下不应提供redis_url")
                
                # 从Nacos获取Redis URL并验证
                redis_url = await SettingsService.get_config_from_nacos(namespace.redis_nacos_key)
                if not SettingsService.validate_redis_url(redis_url):
                    raise ValueError(f"从Nacos获取的Redis URL格式无效: {redis_url}")
                
                redis_config['url'] = redis_url
                redis_config['nacos_key'] = namespace.redis_nacos_key
                
                # 从Nacos获取PostgreSQL URL（可选）
                if namespace.pg_nacos_key:
                    pg_url = await SettingsService.get_config_from_nacos(namespace.pg_nacos_key)
                    if not SettingsService.validate_pg_url(pg_url):
                        raise ValueError(f"从Nacos获取的PostgreSQL URL格式无效: {pg_url}")
                    pg_config['url'] = pg_url
                    pg_config['nacos_key'] = namespace.pg_nacos_key
                if namespace.pg_url:
                    raise ValueError("Nacos配置模式下不应提供pg_url")
            
            # 创建命名空间
            insert_query = text("""
                INSERT INTO namespaces (name, description, redis_config, pg_config, version)
                VALUES (:name, :description, :redis_config, :pg_config, 1)
                RETURNING id, name, description, redis_config, pg_config, 
                          is_active, version, created_at, updated_at
            """)
            
            result = await session.execute(insert_query, {
                'name': namespace.name,
                'description': namespace.description,
                'redis_config': json.dumps(redis_config),
                'pg_config': json.dumps(pg_config)
            })
            
            row = result.fetchone()
            await session.commit()
            
            # 构建响应 - 只返回最终的URL，不返回配置细节
            response = NamespaceResponse(
                name=row.name,
                description=row.description,
                redis_url=redis_config['url'],  # 这里已经是最终的URL
                pg_url=pg_config.get('url', '') if pg_config.get('url') else None,
                connection_url=f"/api/v1/namespaces/{row.name}",
                version=row.version or 1,
                enabled=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
            logger.info(f"成功创建命名空间: {namespace.name}")
            return response
    
    @staticmethod
    async def get_namespace(namespace_name: str) -> NamespaceResponse:
        """
        获取指定命名空间的详细信息
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            命名空间信息
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            query = text("""
                SELECT id, name, description, redis_config, pg_config, 
                       is_active, version, created_at, updated_at
                FROM namespaces
                WHERE name = :name
            """)
            
            result = await session.execute(query, {'name': namespace_name})
            row = result.fetchone()
            
            if not row:
                raise ValueError(f"命名空间 '{namespace_name}' 不存在")
            
            # 构建响应
            redis_config_dict = row.redis_config if row.redis_config else {}
            pg_config_dict = row.pg_config if row.pg_config else {}
            
            # 根据配置模式获取实际的URL
            config_mode = redis_config_dict.get('config_mode', 'direct')
            
            # 获取Redis URL
            if config_mode == 'nacos' and redis_config_dict.get('nacos_key'):
                try:
                    redis_url = await SettingsService.get_config_from_nacos(redis_config_dict['nacos_key'])
                except Exception as e:
                    logger.error(f"从Nacos获取Redis URL失败: {e}")
                    redis_url = redis_config_dict.get('url', '')
            else:
                redis_url = redis_config_dict.get('url', '')
            
            # 获取PostgreSQL URL  
            pg_url = None
            if config_mode == 'nacos' and pg_config_dict.get('nacos_key'):
                try:
                    pg_url = await SettingsService.get_config_from_nacos(pg_config_dict['nacos_key'])
                except Exception as e:
                    logger.error(f"从Nacos获取PostgreSQL URL失败: {e}")
                    pg_url = pg_config_dict.get('url')
            else:
                pg_url = pg_config_dict.get('url')
            
            response = NamespaceResponse(
                name=row.name,
                description=row.description,
                redis_url=redis_url,
                pg_url=pg_url,
                connection_url=f"/api/v1/namespaces/{row.name}",
                version=row.version or 1,
                enabled=row.is_active,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
            
            return response
    
    @staticmethod
    async def update_namespace(namespace_name: str, namespace: NamespaceUpdate) -> NamespaceResponse:
        """
        更新命名空间配置
        
        Args:
            namespace_name: 命名空间名称
            namespace: 更新的配置信息
            
        Returns:
            更新后的命名空间信息
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 检查命名空间是否存在
            check_query = text("""
                SELECT id, redis_config, pg_config FROM namespaces WHERE name = :name
            """)
            result = await session.execute(check_query, {'name': namespace_name})
            row = result.fetchone()
            
            if not row:
                raise ValueError(f"命名空间 '{namespace_name}' 不存在")
            
            # 获取当前配置
            current_redis_config = row.redis_config if row.redis_config else {}
            current_pg_config = row.pg_config if row.pg_config else {}
            
            # 更新配置
            updates = []
            params = {'name': namespace_name}
            
            if namespace.description is not None:
                updates.append("description = :description")
                params['description'] = namespace.description
            
            # 如果提供了config_mode，根据新模式处理配置
            if namespace.config_mode is not None:
                redis_config = {'config_mode': namespace.config_mode.value}
                pg_config = {'config_mode': namespace.config_mode.value}
                
                if namespace.config_mode == ConfigMode.DIRECT:
                    # 直接配置模式
                    if namespace.redis_nacos_key or namespace.pg_nacos_key:
                        raise ValueError("直接配置模式下不应提供nacos_key")
                    
                    if namespace.redis_url:
                        if not SettingsService.validate_redis_url(namespace.redis_url):
                            raise ValueError("无效的Redis URL格式")
                        redis_config['url'] = namespace.redis_url
                    else:
                        # 保留原有URL
                        redis_config['url'] = current_redis_config.get('url', '')
                        
                    if namespace.pg_url:
                        if not SettingsService.validate_pg_url(namespace.pg_url):
                            raise ValueError("无效的PostgreSQL URL格式")
                        pg_config['url'] = namespace.pg_url
                    elif current_pg_config.get('url'):
                        pg_config['url'] = current_pg_config.get('url')
                        
                elif namespace.config_mode == ConfigMode.NACOS:
                    # Nacos配置模式
                    if namespace.redis_url or namespace.pg_url:
                        raise ValueError("Nacos配置模式下不应提供直接URL")
                    
                    if namespace.redis_nacos_key:
                        redis_url = await SettingsService.get_config_from_nacos(namespace.redis_nacos_key)
                        if not SettingsService.validate_redis_url(redis_url):
                            raise ValueError(f"从Nacos获取的Redis URL格式无效: {redis_url}")
                        redis_config['url'] = redis_url
                        redis_config['nacos_key'] = namespace.redis_nacos_key
                    else:
                        # 保留原有配置
                        redis_config['url'] = current_redis_config.get('url', '')
                        if current_redis_config.get('nacos_key'):
                            redis_config['nacos_key'] = current_redis_config.get('nacos_key')
                        
                    if namespace.pg_nacos_key:
                        pg_url = await SettingsService.get_config_from_nacos(namespace.pg_nacos_key)
                        if not SettingsService.validate_pg_url(pg_url):
                            raise ValueError(f"从Nacos获取的PostgreSQL URL格式无效: {pg_url}")
                        pg_config['url'] = pg_url
                        pg_config['nacos_key'] = namespace.pg_nacos_key
                    elif current_pg_config.get('url'):
                        pg_config['url'] = current_pg_config.get('url')
                        if current_pg_config.get('nacos_key'):
                            pg_config['nacos_key'] = current_pg_config.get('nacos_key')
                
                updates.append("redis_config = :redis_config")
                params['redis_config'] = json.dumps(redis_config)
                updates.append("pg_config = :pg_config")
                params['pg_config'] = json.dumps(pg_config)
                
            else:
                # 没有提供config_mode，保持当前模式并更新相应字段
                current_mode = current_redis_config.get('config_mode', 'direct')
                
                if current_mode == 'direct':
                    if namespace.redis_nacos_key or namespace.pg_nacos_key:
                        raise ValueError("当前为直接配置模式，不能提供nacos_key，请先切换到nacos模式")
                    
                    if namespace.redis_url:
                        if not SettingsService.validate_redis_url(namespace.redis_url):
                            raise ValueError("无效的Redis URL格式")
                        current_redis_config['url'] = namespace.redis_url
                        updates.append("redis_config = :redis_config")
                        params['redis_config'] = json.dumps(current_redis_config)
                        
                    if namespace.pg_url:
                        if not SettingsService.validate_pg_url(namespace.pg_url):
                            raise ValueError("无效的PostgreSQL URL格式")
                        current_pg_config['url'] = namespace.pg_url
                        updates.append("pg_config = :pg_config")
                        params['pg_config'] = json.dumps(current_pg_config)
                        
                else:  # nacos mode
                    if namespace.redis_url or namespace.pg_url:
                        raise ValueError("当前为nacos配置模式，不能提供直接URL，请先切换到direct模式")
                    
                    if namespace.redis_nacos_key:
                        redis_url = await SettingsService.get_config_from_nacos(namespace.redis_nacos_key)
                        if not SettingsService.validate_redis_url(redis_url):
                            raise ValueError(f"从Nacos获取的Redis URL格式无效: {redis_url}")
                        current_redis_config['url'] = redis_url
                        current_redis_config['nacos_key'] = namespace.redis_nacos_key
                        updates.append("redis_config = :redis_config")
                        params['redis_config'] = json.dumps(current_redis_config)
                        
                    if namespace.pg_nacos_key:
                        pg_url = await SettingsService.get_config_from_nacos(namespace.pg_nacos_key)
                        if not SettingsService.validate_pg_url(pg_url):
                            raise ValueError(f"从Nacos获取的PostgreSQL URL格式无效: {pg_url}")
                        current_pg_config['url'] = pg_url
                        current_pg_config['nacos_key'] = namespace.pg_nacos_key
                        updates.append("pg_config = :pg_config")
                        params['pg_config'] = json.dumps(current_pg_config)
            
            if namespace.enabled is not None:
                updates.append("is_active = :is_active")
                params['is_active'] = namespace.enabled
            
            if not updates:
                raise ValueError("没有提供要更新的字段")
            
            # 更新版本号和时间戳
            updates.append("version = version + 1")
            updates.append("updated_at = CURRENT_TIMESTAMP")
            
            # 执行更新
            update_query = text(f"""
                UPDATE namespaces 
                SET {', '.join(updates)}
                WHERE name = :name
                RETURNING id, name, description, redis_config, pg_config, 
                          is_active, version, created_at, updated_at
            """)
            
            result = await session.execute(update_query, params)
            updated_row = result.fetchone()
            await session.commit()
            
            # 构建响应
            redis_config_dict = updated_row.redis_config
            pg_config_dict = updated_row.pg_config if updated_row.pg_config else {}
            
            # 根据配置模式获取实际的URL
            config_mode = redis_config_dict.get('config_mode', 'direct')
            
            # 获取Redis URL
            if config_mode == 'nacos' and redis_config_dict.get('nacos_key'):
                try:
                    redis_url = await SettingsService.get_config_from_nacos(redis_config_dict['nacos_key'])
                except Exception as e:
                    logger.error(f"从Nacos获取Redis URL失败: {e}")
                    redis_url = redis_config_dict.get('url', '')
            else:
                redis_url = redis_config_dict.get('url', '')
            
            # 获取PostgreSQL URL
            pg_url = None
            if config_mode == 'nacos' and pg_config_dict.get('nacos_key'):
                try:
                    pg_url = await SettingsService.get_config_from_nacos(pg_config_dict['nacos_key'])
                except Exception as e:
                    logger.error(f"从Nacos获取PostgreSQL URL失败: {e}")
                    pg_url = pg_config_dict.get('url')
            else:
                pg_url = pg_config_dict.get('url')
            
            response = NamespaceResponse(
                name=updated_row.name,
                description=updated_row.description,
                redis_url=redis_url,
                pg_url=pg_url,
                connection_url=f"/api/v1/namespaces/{updated_row.name}",
                version=updated_row.version or 1,
                enabled=updated_row.is_active,
                created_at=updated_row.created_at,
                updated_at=updated_row.updated_at
            )
            
            logger.info(f"成功更新命名空间: {namespace_name}")
            return response
    
    @staticmethod
    async def delete_namespace(namespace_name: str) -> Dict[str, str]:
        """
        删除命名空间
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            删除结果
        """
        if namespace_name == 'default':
            raise ValueError("不能删除默认命名空间")
        
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 检查命名空间是否存在
            check_query = text("SELECT id FROM namespaces WHERE name = :name")
            result = await session.execute(check_query, {'name': namespace_name})
            
            if not result.fetchone():
                raise ValueError(f"命名空间 '{namespace_name}' 不存在")
            
            # 删除命名空间
            delete_query = text("DELETE FROM namespaces WHERE name = :name")
            await session.execute(delete_query, {'name': namespace_name})
            await session.commit()
            
            logger.info(f"成功删除命名空间: {namespace_name}")
            return {"message": f"命名空间 '{namespace_name}' 已删除"}
    
    @staticmethod
    async def activate_namespace(namespace_name: str) -> Dict[str, str]:
        """
        激活命名空间
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            激活结果
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 检查并激活命名空间
            update_query = text("""
                UPDATE namespaces 
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE name = :name
            """)
            
            result = await session.execute(update_query, {'name': namespace_name})
            
            if result.rowcount == 0:
                raise ValueError(f"命名空间 '{namespace_name}' 不存在")
            
            await session.commit()
            
            logger.info(f"成功激活命名空间: {namespace_name}")
            return {"message": f"命名空间 '{namespace_name}' 已激活"}
    
    @staticmethod
    async def deactivate_namespace(namespace_name: str) -> Dict[str, str]:
        """
        停用命名空间
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            停用结果
        """
        if namespace_name == 'default':
            raise ValueError("不能停用默认命名空间")
        
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 检查并停用命名空间
            update_query = text("""
                UPDATE namespaces 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE name = :name
            """)
            
            result = await session.execute(update_query, {'name': namespace_name})
            
            if result.rowcount == 0:
                raise ValueError(f"命名空间 '{namespace_name}' 不存在")
            
            await session.commit()
            
            logger.info(f"成功停用命名空间: {namespace_name}")
            return {"message": f"命名空间 '{namespace_name}' 已停用"}
    
    @staticmethod
    async def get_namespace_statistics(namespace_name: str) -> Dict[str, Any]:
        """
        获取命名空间统计信息
        
        Args:
            namespace_name: 命名空间名称
            
        Returns:
            统计信息
        """
        # 这里可以根据实际需求实现统计逻辑
        # 暂时返回模拟数据
        return {
            "namespace": namespace_name,
            "statistics": {
                "total_queues": 0,
                "total_tasks": 0,
                "active_workers": 0,
                "pending_tasks": 0,
                "processing_tasks": 0,
                "completed_tasks": 0,
                "failed_tasks": 0
            },
            "timestamp": datetime.now().isoformat()
        }
    
    @staticmethod
    async def batch_activate_namespaces(namespace_names: List[str]) -> Dict[str, Any]:
        """
        批量激活命名空间
        
        Args:
            namespace_names: 命名空间名称列表
            
        Returns:
            激活结果
        """
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 批量激活
            update_query = text("""
                UPDATE namespaces 
                SET is_active = true, updated_at = CURRENT_TIMESTAMP
                WHERE name = ANY(:names)
            """)
            
            result = await session.execute(update_query, {'names': namespace_names})
            await session.commit()
            
            activated_count = result.rowcount
            logger.info(f"批量激活了 {activated_count} 个命名空间")
            
            return {
                "activated": activated_count,
                "namespaces": namespace_names[:activated_count]
            }
    
    @staticmethod
    async def batch_deactivate_namespaces(namespace_names: List[str]) -> Dict[str, Any]:
        """
        批量停用命名空间
        
        Args:
            namespace_names: 命名空间名称列表
            
        Returns:
            停用结果
        """
        # 过滤掉默认命名空间
        filtered_names = [name for name in namespace_names if name != 'default']
        
        if not filtered_names:
            return {
                "deactivated": 0,
                "namespaces": [],
                "skipped": ["default"]
            }
        
        db_manager = get_db_manager()
        async with db_manager.get_master_session() as session:
            # 批量停用
            update_query = text("""
                UPDATE namespaces 
                SET is_active = false, updated_at = CURRENT_TIMESTAMP
                WHERE name = ANY(:names)
            """)
            
            result = await session.execute(update_query, {'names': filtered_names})
            await session.commit()
            
            deactivated_count = result.rowcount
            logger.info(f"批量停用了 {deactivated_count} 个命名空间")
            
            response = {
                "deactivated": deactivated_count,
                "namespaces": filtered_names[:deactivated_count]
            }
            
            # 如果有被跳过的
            skipped = [name for name in namespace_names if name not in filtered_names]
            if skipped:
                response["skipped"] = skipped
            
            return response


__all__ = ['SettingsService']