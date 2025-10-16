"""
统一的数据库管理模块
提供命名空间级别的数据库连接管理
"""
import os
import logging
import asyncio
from typing import Dict, Optional, Any, AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import urlparse

import redis.asyncio as redis
import asyncpg
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text

logger = logging.getLogger(__name__)


class NamespaceConfig:
    """命名空间配置"""
    
    def __init__(self, name: str, redis_config: dict, pg_config: dict):
        self.name = name
        self.redis_config = redis_config or {}
        self.pg_config = pg_config or {}
        self._parse_configs()
    
    def _parse_configs(self):
        """解析配置，提取URL和配置模式"""
        # Redis配置
        self.redis_mode = self.redis_config.get('config_mode', 'direct')
        self.redis_url = self.redis_config.get('url')
        self.redis_nacos_key = self.redis_config.get('nacos_key')
        
        # PostgreSQL配置
        self.pg_mode = self.pg_config.get('config_mode', 'direct')
        self.pg_url = self.pg_config.get('url')
        self.pg_nacos_key = self.pg_config.get('nacos_key')
    
    def has_redis(self) -> bool:
        """是否配置了Redis"""
        return bool(self.redis_url)
    
    def has_postgres(self) -> bool:
        """是否配置了PostgreSQL"""
        return bool(self.pg_url)


class ConnectionPool:
    """单个命名空间的连接池"""
    
    def __init__(self, namespace: str, config: NamespaceConfig):
        self.namespace = namespace
        self.config = config
        
        # Redis连接池
        self._redis_client: Optional[redis.Redis] = None
        self._binary_redis_client: Optional[redis.Redis] = None
        
        # PostgreSQL连接池
        self._pg_pool: Optional[asyncpg.Pool] = None
        
        # SQLAlchemy引擎和会话工厂
        self._sa_engine: Optional[Any] = None
        self._sa_session_maker: Optional[async_sessionmaker] = None
        
        # 初始化锁
        self._init_lock = asyncio.Lock()
        self._initialized = False
    
    async def initialize(self):
        """初始化所有连接池"""
        async with self._init_lock:
            if self._initialized:
                return
            
            try:
                # 初始化Redis
                if self.config.has_redis():
                    await self._init_redis()
                
                # 初始化PostgreSQL
                if self.config.has_postgres():
                    await self._init_postgres()
                
                self._initialized = True
                logger.info(f"命名空间 '{self.namespace}' 连接池初始化成功")
                
            except Exception as e:
                logger.error(f"命名空间 '{self.namespace}' 连接池初始化失败: {e}")
                raise
    
    async def _init_redis(self):
        """初始化Redis客户端（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_async_redis_client

        url = self.config.redis_url

        # 文本客户端（decode_responses=True）
        self._redis_client = get_async_redis_client(
            redis_url=url,
            max_connections=20,
            decode_responses=True
        )

        # 二进制客户端（decode_responses=False）
        self._binary_redis_client = get_async_redis_client(
            redis_url=url,
            max_connections=20,
            decode_responses=False
        )

        logger.debug(f"Redis客户端已就绪: {self.namespace}")
    
    async def _init_postgres(self):
        """初始化PostgreSQL连接池"""
        url = self.config.pg_url
        
        # 创建asyncpg连接池
        parsed = urlparse(url)
        self._pg_pool = await asyncpg.create_pool(
            host=parsed.hostname,
            port=parsed.port or 5432,
            user=parsed.username,
            password=parsed.password,
            database=parsed.path.lstrip('/'),
            min_size=2,
            max_size=10,
            command_timeout=30
        )
        
        # 创建SQLAlchemy引擎
        sa_url = url
        if sa_url.startswith('postgresql://'):
            sa_url = sa_url.replace('postgresql://', 'postgresql+asyncpg://', 1)
        
        self._sa_engine = create_async_engine(
            sa_url,
            pool_size=5,
            max_overflow=10,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False
        )
        
        self._sa_session_maker = async_sessionmaker(
            self._sa_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        logger.debug(f"PostgreSQL连接池已创建: {self.namespace}")
    
    async def get_redis_client(self, decode: bool = True) -> redis.Redis:
        """获取Redis客户端"""
        if not self._initialized:
            await self.initialize()
        
        if not self.config.has_redis():
            raise ValueError(f"命名空间 '{self.namespace}' 未配置Redis")
        
        client = self._redis_client if decode else self._binary_redis_client
        return client
    
    @asynccontextmanager
    async def get_pg_connection(self) -> AsyncGenerator[asyncpg.Connection, None]:
        """获取PostgreSQL原生连接"""
        if not self._initialized:
            await self.initialize()
        
        if not self._pg_pool:
            raise ValueError(f"命名空间 '{self.namespace}' 未配置PostgreSQL")
        
        async with self._pg_pool.acquire() as conn:
            yield conn
    
    @asynccontextmanager
    async def get_sa_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取SQLAlchemy会话"""
        if not self._initialized:
            await self.initialize()
        
        if not self._sa_session_maker:
            raise ValueError(f"命名空间 '{self.namespace}' 未配置PostgreSQL")
        
        async with self._sa_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def close(self):
        """关闭所有连接"""
        try:
            if self._redis_client:
                await self._redis_client.aclose()

            if self._binary_redis_client:
                await self._binary_redis_client.aclose()
            
            if self._pg_pool:
                await self._pg_pool.close()
            
            if self._sa_engine:
                await self._sa_engine.dispose()
            
            self._initialized = False
            logger.info(f"命名空间 '{self.namespace}' 连接池已关闭")
            
        except Exception as e:
            logger.error(f"关闭命名空间 '{self.namespace}' 连接池失败: {e}")


class UnifiedDatabaseManager:
    """
    统一的数据库管理器
    负责管理所有命名空间的数据库连接
    支持从环境变量或Nacos读取配置
    """
    
    def __init__(self, use_nacos: bool = False):
        """
        初始化数据库管理器
        
        Args:
            use_nacos: 是否从Nacos读取配置
        """
        # 连接池缓存
        self._pools: Dict[str, ConnectionPool] = {}
        
        # 配置缓存
        self._configs: Dict[str, NamespaceConfig] = {}
        
        # 是否使用Nacos配置
        self.use_nacos = use_nacos
        
        # 主数据库URL（用于读取命名空间配置）
        if use_nacos:
            # 从Nacos配置读取
            self._load_master_url_from_nacos()
        else:
            # 从环境变量读取
            self.master_pg_url = os.getenv(
                'JETTASK_PG_URL',
                'postgresql+asyncpg://jettask:123456@localhost:5432/jettask'
            )
        
        # 主数据库连接
        self._master_engine = None
        self._master_session_maker = None
        
        # 初始化锁
        self._init_lock = asyncio.Lock()
        
        # Nacos配置（如果需要）
        self._nacos_client = None
    
    def _load_master_url_from_nacos(self):
        """从Nacos配置加载主数据库URL"""
        try:
            from jettask.config.nacos_config import config
            
            # 从Nacos配置获取数据库连接信息
            pg_config = config.config
            
            # 构建数据库URL
            jettask_pg_url = pg_config.get('JETTASK_PG_URL')
            self.master_pg_url = jettask_pg_url
            logger.info(f"从Nacos加载数据库配置: {jettask_pg_url=}")
            
        except Exception as e:
            logger.error(f"从Nacos加载数据库配置失败: {e}")
            # 失败时使用默认值
            self.master_pg_url = os.getenv(
                'JETTASK_PG_URL',
                'postgresql+asyncpg://jettask:123456@localhost:5432/jettask'
            )
            logger.warning("使用默认数据库配置")
    
    async def initialize(self):
        """初始化管理器"""
        async with self._init_lock:
            if self._master_engine:
                return
            print(f'{self.master_pg_url=}')
            # 创建主数据库连接
            self._master_engine = create_async_engine(
                self.master_pg_url,
                pool_size=3,
                max_overflow=5,
                pool_pre_ping=True,
                echo=False
            )
            
            self._master_session_maker = async_sessionmaker(
                self._master_engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            logger.info("数据库管理器初始化完成")
    
    async def _fetch_namespace_config(self, namespace: str) -> NamespaceConfig:
        """从数据库获取命名空间配置"""
        if not self._master_session_maker:
            await self.initialize()
        
        async with self._master_session_maker() as session:
            query = text("""
                SELECT name, redis_config, pg_config, is_active
                FROM namespaces
                WHERE name = :name
            """)
            
            result = await session.execute(query, {'name': namespace})
            row = result.fetchone()
            
            if not row:
                raise ValueError(f"命名空间 '{namespace}' 不存在")
            
            if not row.is_active:
                raise ValueError(f"命名空间 '{namespace}' 未激活")
            
            # 处理Nacos配置
            redis_config = row.redis_config or {}
            pg_config = row.pg_config or {}
            
            # 如果是Nacos模式，需要从Nacos获取实际的URL
            if redis_config.get('config_mode') == 'nacos':
                redis_url = await self._get_from_nacos(redis_config.get('nacos_key'))
                redis_config['url'] = redis_url
            
            if pg_config.get('config_mode') == 'nacos':
                pg_url = await self._get_from_nacos(pg_config.get('nacos_key'))
                pg_config['url'] = pg_url
            
            return NamespaceConfig(row.name, redis_config, pg_config)
    
    async def _get_from_nacos(self, key: str) -> str:
        """从Nacos获取配置（需要实现）"""
        try:
            from jettask.config.nacos_config import Config
            if not self._nacos_client:
                self._nacos_client = Config()
            value = self._nacos_client.config.get(key)
            if not value:
                raise ValueError(f"Nacos配置键 '{key}' 不存在")
            return value
        except ImportError:
            logger.warning("Nacos客户端未安装，返回占位URL")
            return f"redis://nacos-placeholder/{key}"
    
    async def get_pool(self, namespace: str) -> ConnectionPool:
        """获取命名空间的连接池"""
        # 检查缓存
        if namespace in self._pools:
            return self._pools[namespace]
        
        # 从数据库获取配置（而不是通过HTTP）
        if namespace not in self._configs:
            config = await self._fetch_namespace_config(namespace)
            self._configs[namespace] = config
        
        # 创建新的连接池
        pool = ConnectionPool(namespace, self._configs[namespace])
        await pool.initialize()
        
        # 缓存连接池
        self._pools[namespace] = pool
        
        return pool
    
    async def get_redis_client(self, namespace: str, decode: bool = True) -> redis.Redis:
        """便捷方法：获取Redis客户端"""
        pool = await self.get_pool(namespace)
        return await pool.get_redis_client(decode)
    
    @asynccontextmanager
    async def get_pg_connection(self, namespace: str) -> AsyncGenerator[asyncpg.Connection, None]:
        """便捷方法：获取PostgreSQL连接"""
        pool = await self.get_pool(namespace)
        async with pool.get_pg_connection() as conn:
            yield conn
    
    @asynccontextmanager
    async def get_session(self, namespace: str) -> AsyncGenerator[AsyncSession, None]:
        """便捷方法：获取SQLAlchemy会话"""
        pool = await self.get_pool(namespace)
        async with pool.get_sa_session() as session:
            yield session
    
    @asynccontextmanager
    async def get_master_session(self) -> AsyncGenerator[AsyncSession, None]:
        """获取主数据库会话（用于管理命名空间）"""
        if not self._master_session_maker:
            await self.initialize()
        
        async with self._master_session_maker() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
            finally:
                await session.close()
    
    async def refresh_config(self, namespace: str):
        """刷新命名空间配置"""
        # 关闭旧连接
        if namespace in self._pools:
            await self._pools[namespace].close()
            del self._pools[namespace]
        
        # 清除配置缓存
        if namespace in self._configs:
            del self._configs[namespace]
        
        logger.info(f"已刷新命名空间 '{namespace}' 的配置")
    
    async def list_namespaces(self) -> list:
        """列出所有命名空间"""
        async with self.get_master_session() as session:
            query = text("""
                SELECT name, description, is_active, created_at, updated_at
                FROM namespaces
                ORDER BY name
            """)
            
            result = await session.execute(query)
            rows = result.fetchall()
            
            return [
                {
                    'name': row.name,
                    'description': row.description,
                    'is_active': row.is_active,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                    'updated_at': row.updated_at.isoformat() if row.updated_at else None
                }
                for row in rows
            ]
    
    async def close_all(self):
        """关闭所有连接"""
        # 关闭所有命名空间连接池
        for namespace, pool in list(self._pools.items()):
            await pool.close()
        
        self._pools.clear()
        self._configs.clear()
        
        # 关闭主数据库连接
        if self._master_engine:
            await self._master_engine.dispose()
        
        logger.info("数据库管理器已关闭所有连接")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        await self.initialize()
        return self
    
    async def __aexit__(self, exc_type=None, exc_val=None, exc_tb=None):
        """异步上下文管理器出口"""
        await self.close_all()


# 全局实例
_db_manager: Optional[UnifiedDatabaseManager] = None


def get_db_manager(use_nacos: bool = None) -> UnifiedDatabaseManager:
    """
    获取全局数据库管理器实例
    
    Args:
        use_nacos: 是否使用Nacos配置，None表示使用已有实例的设置
    """
    global _db_manager
    if _db_manager is None:
        # 如果没有指定，检查环境变量或默认值
        if use_nacos is None:
            use_nacos = os.getenv('USE_NACOS', 'false').lower() == 'true'
        _db_manager = UnifiedDatabaseManager(use_nacos=use_nacos)
    elif use_nacos is not None and _db_manager.use_nacos != use_nacos:
        # 如果配置模式改变了，重新创建实例
        logger.info(f"配置模式改变，重新创建数据库管理器 (use_nacos={use_nacos})")
        _db_manager = UnifiedDatabaseManager(use_nacos=use_nacos)
    return _db_manager


async def init_db_manager(use_nacos: bool = None):
    """
    初始化全局数据库管理器
    
    Args:
        use_nacos: 是否使用Nacos配置
    """
    manager = get_db_manager(use_nacos=use_nacos)
    await manager.initialize()
    return manager


async def close_db_manager():
    """关闭全局数据库管理器"""
    global _db_manager
    if _db_manager:
        await _db_manager.close_all()
        _db_manager = None