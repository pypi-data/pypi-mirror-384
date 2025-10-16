"""
统一的多命名空间管理器基类
提供单/多命名空间模式的通用功能
"""
import re
import logging
import aiohttp
from typing import Optional, Set, Dict, Any
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class UnifiedManagerBase(ABC):
    """
    统一管理器基类
    根据task_center_url自动判断是单命名空间还是多命名空间模式
    """
    
    def __init__(self, 
                 task_center_url: str,
                 check_interval: int = 30,
                 debug: bool = False):
        """
        初始化基础管理器
        
        Args:
            task_center_url: 任务中心URL
                - 单命名空间: http://localhost:8001/api/namespaces/{name}
                - 多命名空间: http://localhost:8001 或 http://localhost:8001/api
            check_interval: 命名空间检测间隔（秒）
            debug: 是否启用调试模式
        """
        self.task_center_url = task_center_url.rstrip('/')
        self.check_interval = check_interval
        self.debug = debug
        
        # 判断模式
        self.namespace_name: Optional[str] = None
        self.is_single_namespace = self._detect_mode()
        
        # 运行状态
        self.running = False
        
        # 设置日志
        if debug:
            logging.basicConfig(level=logging.DEBUG)
        else:
            logging.basicConfig(level=logging.INFO)
    
    def _detect_mode(self) -> bool:
        """
        检测是单命名空间还是多命名空间模式
        
        Returns:
            True: 单命名空间模式
            False: 多命名空间模式
        """
        # 检查URL格式
        # 单命名空间: /api/v1/namespaces/{name} 或 /api/namespaces/{name}
        # 多命名空间: 不包含这些路径或以 /api 结尾
        
        # 检查新格式
        if '/api/v1/namespaces/' in self.task_center_url:
            # 提取命名空间名称
            match = re.search(r'/api/v1/namespaces/([^/]+)/?$', self.task_center_url)
            if match:
                self.namespace_name = match.group(1)
                logger.info(f"检测到单命名空间模式: {self.namespace_name}")
                return True
        
        # 兼容旧格式
        elif '/api/namespaces/' in self.task_center_url:
            # 提取命名空间名称
            match = re.search(r'/api/namespaces/([^/]+)/?$', self.task_center_url)
            if match:
                self.namespace_name = match.group(1)
                logger.info(f"检测到单命名空间模式: {self.namespace_name}")
                return True
        
        # 多命名空间模式
        logger.info("检测到多命名空间模式")
        return False
    
    def get_base_url(self) -> str:
        """
        获取任务中心的基础URL
        
        Returns:
            基础URL（去除命名空间路径）
        """
        # 支持新旧两种API路径格式
        if self.is_single_namespace:
            if '/api/v1/namespaces/' in self.task_center_url:
                # 从 http://localhost:8001/api/v1/namespaces/default 提取 http://localhost:8001
                return self.task_center_url.split('/api/v1/namespaces/')[0]
            elif '/api/namespaces/' in self.task_center_url:
                # 兼容旧格式
                return self.task_center_url.split('/api/namespaces/')[0]
        
        # 多命名空间模式，如果URL以 /api/v1/ 结尾，去掉 /api/v1/ 部分
        if self.task_center_url.endswith('/api/v1/') or self.task_center_url.endswith('/api/v1'):
            # 从 http://localhost:8001/api/v1/ 提取 http://localhost:8001
            return self.task_center_url.rstrip('/').rsplit('/api/v1', 1)[0]
        
        return self.task_center_url
    
    def get_target_namespaces(self) -> Optional[Set[str]]:
        """
        获取目标命名空间集合
        
        Returns:
            单命名空间模式: 返回包含单个命名空间的集合
            多命名空间模式: 返回 None（表示所有命名空间）
        """
        if self.is_single_namespace and self.namespace_name:
            return {self.namespace_name}
        return None
    
    async def fetch_namespaces_info(self, namespace_names: Optional[Set[str]] = None) -> list:
        """
        从任务中心API获取命名空间配置
        
        Args:
            namespace_names: 要获取的命名空间名称集合，None表示获取所有
            
        Returns:
            命名空间配置列表
        """
        namespaces = []
        
        try:
            # 获取基础URL
            base_url = self.get_base_url()
            
            if namespace_names:
                # 获取指定的命名空间
                for name in namespace_names:
                    try:
                        async with aiohttp.ClientSession() as session:
                            url = f"{base_url}/api/v1/namespaces/{name}"
                            logger.debug(f"请求命名空间配置: {url}")
                            
                            async with session.get(url) as response:
                                if response.status == 200:
                                    data = await response.json()
                                    # 构建redis和pg配置
                                    # 跳过没有有效配置的命名空间
                                    redis_url = data.get('redis_url', '')
                                    pg_url = data.get('pg_url', '')
                                    
                                    if not redis_url or not pg_url:
                                        # logger.warning(f"跳过命名空间 {data['name']}：缺少 Redis 或 PostgreSQL 配置")
                                        continue
                                    
                                    redis_config = {'url': redis_url}
                                    pg_config = {'url': pg_url}
                                    
                                    ns_info = {
                                        'id': data.get('id', data['name']),  # 如果没有id，使用name作为id
                                        'name': data['name'],
                                        'redis_config': redis_config,
                                        'pg_config': pg_config,
                                        'redis_prefix': data['name']  # 直接使用命名空间名称作为前缀
                                    }
                                    namespaces.append(ns_info)
                                    logger.info(f"成功获取命名空间 {name} 的配置")
                                else:
                                    logger.warning(f"获取命名空间 {name} 失败: HTTP {response.status}")
                    except Exception as e:
                        logger.error(f"获取命名空间 {name} 失败: {e}")
            else:
                # 获取所有命名空间
                async with aiohttp.ClientSession() as session:
                    url = f"{base_url}/api/v1/namespaces/"  # 添加末尾斜杠
                    logger.debug(f"请求所有命名空间配置: {url}")
                    
                    async with session.get(url) as response:
                        if response.status == 200:
                            data_list = await response.json()
                            for data in data_list:
                                # 构建redis和pg配置
                                # 跳过没有有效配置的命名空间
                                redis_url = data.get('redis_url', '')
                                pg_url = data.get('pg_url', '')
                                
                                if not redis_url or not pg_url:
                                    # logger.warning(f"跳过命名空间 {data['name']}：缺少 Redis 或 PostgreSQL 配置")
                                    continue
                                
                                redis_config = {'url': redis_url}
                                pg_config = {'url': pg_url}
                                
                                ns_info = {
                                    'id': data.get('id', data['name']),  # 如果没有id，使用name作为id
                                    'name': data['name'],
                                    'redis_config': redis_config,
                                    'pg_config': pg_config,
                                    'redis_prefix': data['name']  # 直接使用命名空间名称作为前缀
                                }
                                namespaces.append(ns_info)
                            logger.info(f"成功获取 {len(namespaces)} 个命名空间的配置")
                        else:
                            logger.error(f"获取命名空间列表失败: HTTP {response.status}")
                            
        except Exception as e:
            logger.error(f"从任务中心获取命名空间配置失败: {e}")
            # 如果API调用失败，可以使用默认配置作为回退
            if not namespaces and (not namespace_names or 'default' in namespace_names):
                logger.warning("使用默认命名空间配置作为回退")
                namespaces.append({
                    'id': 1,
                    'name': 'default',
                    'redis_config': {
                        'host': 'localhost',
                        'port': 6379,
                        'db': 0,
                        'password': None
                    },
                    'pg_config': {
                        'host': 'localhost',
                        'port': 5432,
                        'database': 'jettask',
                        'user': 'jettask',
                        'password': '123456'
                    },
                    'redis_prefix': 'default'
                })
                
        return namespaces
    
    async def run(self):
        """运行管理器（统一处理单/多命名空间）"""
        self.running = True
        
        logger.info(f"启动 {self.__class__.__name__}")
        logger.info(f"任务中心: {self.task_center_url}")
        logger.info(f"模式: {'单命名空间' if self.is_single_namespace else '多命名空间'}")
        
        if not self.is_single_namespace:
            logger.info(f"检测间隔: {self.check_interval}秒")
        
        # 获取目标命名空间
        target_namespaces = self.get_target_namespaces()
        
        try:
            if self.is_single_namespace:
                # 单命名空间模式
                await self.run_single_namespace(self.namespace_name)
            else:
                # 多命名空间模式
                await self.run_multi_namespace(target_namespaces)
        except KeyboardInterrupt:
            logger.info("收到中断信号")
        except Exception as e:
            logger.error(f"运行错误: {e}", exc_info=self.debug)
        finally:
            self.stop()
            await self.cleanup()
    
    @abstractmethod
    async def run_single_namespace(self, namespace_name: str):
        """
        运行单命名空间模式
        
        Args:
            namespace_name: 命名空间名称
        """
        pass
    
    @abstractmethod
    async def run_multi_namespace(self, namespace_names: Optional[Set[str]]):
        """
        运行多命名空间模式
        
        Args:
            namespace_names: 目标命名空间集合，None表示所有命名空间
        """
        pass
    
    def stop(self):
        """停止管理器"""
        self.running = False
        logger.info(f"停止 {self.__class__.__name__}")
    
    async def cleanup(self):
        """清理资源（子类可重写）"""
        pass