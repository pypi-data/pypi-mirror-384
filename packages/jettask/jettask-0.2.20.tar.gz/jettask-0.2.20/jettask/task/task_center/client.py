"""
任务中心客户端 - 独立的、可复用的任务中心连接器
"""
import os
import aiohttp
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class TaskCenter:
    """独立的任务中心客户端"""
    
    def __init__(self, namespace_url: str = None):
        """
        初始化任务中心客户端
        
        Args:
            namespace_url: 命名空间的URL，如 http://localhost:8001/api/v1/namespaces/{name}
        """
        self.namespace_url = namespace_url
        self._session: Optional[aiohttp.ClientSession] = None
        self._config: Optional[Dict[str, Any]] = None
        self._namespace_name: Optional[str] = None
        self._initialized = False
        
        # 从URL解析命名空间名称
        if namespace_url:
            self._parse_url(namespace_url)
    
    def _parse_url(self, url: str):
        """解析URL获取命名空间名称"""
        if url.startswith("http://") or url.startswith("https://"):
            import re
            # 匹配格式: /api/v1/namespaces/{name}
            match = re.search(r'/api/v1/namespaces/([^/]+)$', url)
            if match:
                self._namespace_name = match.group(1)
        elif url.startswith("taskcenter://"):
            # 兼容旧格式 taskcenter://namespace/{name}
            parts = url.replace("taskcenter://", "").split("/")
            if len(parts) >= 2 and parts[0] == "namespace":
                self._namespace_name = parts[1]
                base_url = os.getenv("TASK_CENTER_BASE_URL", "http://localhost:8001")
                self.namespace_url = f"{base_url}/api/v1/namespaces/{self._namespace_name}"
    
    @property
    def is_enabled(self) -> bool:
        """是否启用任务中心"""
        return self.namespace_url is not None
    
    @property
    def namespace_name(self) -> str:
        """获取命名空间名称"""
        return self._namespace_name or "jettask"
    
    @property
    def redis_prefix(self) -> str:
        """获取Redis键前缀"""
        return self.namespace_name
    
    @property
    def redis_config(self) -> Optional[Dict[str, Any]]:
        """获取Redis配置"""
        return self._config.get('redis_config') if self._config else None
    
    @property
    def pg_config(self) -> Optional[Dict[str, Any]]:
        """获取PostgreSQL配置"""
        return self._config.get('pg_config') if self._config else None
    
    @property
    def version(self) -> int:
        """获取配置版本"""
        return self._config.get('version', 1) if self._config else 1
    
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    def connect(self, asyncio: bool = False):
        """
        连接到任务中心并获取配置
        
        Args:
            asyncio: 是否使用异步模式，默认为False（同步模式）
        
        Returns:
            连接成功返回True，失败返回False（异步模式返回协程）
        """
        if asyncio:
            return self._connect_async()
        else:
            return self._connect_sync()
    
    def _connect_sync(self) -> bool:
        """同步连接到任务中心"""
        if not self.is_enabled:
            return False
        
        if self._initialized:
            logger.debug(f"任务中心已初始化，使用缓存配置")
            return True
        
        try:
            import requests
            response = requests.get(self.namespace_url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self._namespace_name = data.get('name')
                
                # 构建redis_config
                redis_config = None
                if data.get('redis_url'):
                    redis_config = {'url': data['redis_url']}
                
                # 构建pg_config
                pg_config = None
                if data.get('pg_url'):
                    pg_config = {'url': data['pg_url']}
                
                self._config = {
                    'redis_config': redis_config,
                    'pg_config': pg_config,
                    'namespace_name': data.get('name'),
                    'version': data.get('version', 1)
                }
                self._initialized = True
                logger.info(f"成功连接到任务中心命名空间: {self._namespace_name} (v{self.version})")
                return True
            else:
                logger.error(f"无法连接到任务中心: HTTP {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"连接任务中心失败: {e}")
            return False
    
    async def _connect_async(self) -> bool:
        """异步连接到任务中心"""
        if not self.is_enabled:
            return False
        
        if self._initialized:
            logger.debug(f"任务中心已初始化，使用缓存配置")
            return True
        
        try:
            session = await self._get_session()
            async with session.get(self.namespace_url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._namespace_name = data.get('name')
                    
                    # 构建redis_config
                    redis_config = None
                    if data.get('redis_url'):
                        redis_config = {'url': data['redis_url']}
                    
                    # 构建pg_config
                    pg_config = None
                    if data.get('pg_url'):
                        pg_config = {'url': data['pg_url']}
                    
                    self._config = {
                        'redis_config': redis_config,
                        'pg_config': pg_config,
                        'namespace_name': data.get('name'),
                        'version': data.get('version', 1)
                    }
                    self._initialized = True
                    logger.info(f"成功连接到任务中心命名空间: {self._namespace_name} (v{self.version})")
                    return True
                else:
                    logger.error(f"无法连接到任务中心: HTTP {resp.status}")
                    return False
        except Exception as e:
            logger.error(f"连接任务中心失败: {e}")
            return False
    
    def get_redis_url(self) -> Optional[str]:
        """
        获取Redis连接URL
        
        Returns:
            Redis连接URL字符串
        """
        if not self.redis_config:
            return None
        
        # 如果配置中直接有url字段，直接返回
        if 'url' in self.redis_config:
            return self.redis_config['url']
        
        # 否则，从分离的字段构建URL
        host = self.redis_config.get('host', 'localhost')
        port = self.redis_config.get('port', 6379)
        db = self.redis_config.get('db', 0)
        password = self.redis_config.get('password', '')
        
        if password:
            return f"redis://:{password}@{host}:{port}/{db}"
        else:
            return f"redis://{host}:{port}/{db}"
    
    def get_pg_url(self) -> Optional[str]:
        """
        获取PostgreSQL连接URL
        
        Returns:
            PostgreSQL连接URL字符串
        """
        if not self.pg_config:
            return None
        
        # 如果配置中直接有url字段，直接返回
        if 'url' in self.pg_config:
            return self.pg_config['url']
        
        # 否则，从分离的字段构建URL
        host = self.pg_config.get('host', 'localhost')
        port = self.pg_config.get('port', 5432)
        database = self.pg_config.get('database', 'jettask')
        user = self.pg_config.get('user', 'jettask')
        password = self.pg_config.get('password', '123456')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    async def close(self):
        """关闭客户端"""
        if self._session:
            await self._session.close()
            self._session = None
    
    def __repr__(self) -> str:
        return f"<TaskCenter namespace='{self.namespace_name}' version={self.version} initialized={self._initialized}>"