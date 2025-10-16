#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
配置管理模块
使用 Nacos 作为配置中心
支持定时刷新和配置变更监听
"""
import os
import json
import yaml
import threading
from datetime import datetime
from typing import Dict, Any, Callable, List, Optional
from dotenv import load_dotenv
from nacos import NacosClient
import logging
try:
    from urllib.request import Request, urlopen
    from urllib.parse import urlencode
except ImportError:
    from urllib2 import Request, urlopen
    from urllib import urlencode



logger = logging.getLogger(__name__)


class NacosConfigLoader:
    """Nacos 配置加载器类，支持定时刷新和配置监听"""
    
    def __init__(self, refresh_interval: int = 30):
        """初始化配置管理器
        
        Args:
            refresh_interval: 配置刷新间隔（秒），默认30秒
        """
        self.nacos_config = None 
        
        self.nacos_group = None
        self.nacos_data_id = None
        self.local_dev_mode = None
        # 服务注册信息
        self.service_info = None
        
        # 刷新相关
        self.refresh_interval = refresh_interval
        self.refresh_thread = None
        self.stop_refresh = threading.Event()
        self.last_refresh_time = None
        self.config_version = 0
        
        # 配置变更监听器
        self.change_listeners: List[Callable[[Dict[str, Any]], None]] = []
        
        # Nacos客户端（保持长连接）
        self.nacos_client = None
        
        # 配置锁，保证线程安全
        self._config_lock = threading.RLock()
        
        # 标记是否已初始化
        self._initialized = False
        self._config = None
    
    @property
    def config(self) -> dict:
        """获取当前配置（线程安全，延迟初始化）"""
        with self._config_lock:
            # 延迟初始化：第一次访问时才初始化并加载配置
            if not self._initialized:
                self._lazy_init()
            return self._config
    
    def _lazy_init(self):
        """延迟初始化：第一次访问配置时才执行"""
        if self._initialized:
            return
        
        logger.info("第一次访问配置，开始初始化...")
        
        # 初始化配置
        self._init_config()
        
        # 加载配置
        self._config = self._load_config()
        
        # 启动定时刷新
        if not self.local_dev_mode and self.refresh_interval > 0:
            self.start_refresh_thread()
        
        self._initialized = True
        logger.info("配置初始化完成")
    
    def _init_config(self):
        """初始化配置"""
        try:
            # 加载 .env 文件
            load_dotenv()
            self.nacos_config = {
                'server_addresses': os.getenv('NACOS_SERVER', '127.0.0.1:8848'),
                'namespace': os.getenv('NACOS_NAMESPACE', 'tamar_console_dev'),
                'username': os.getenv('NACOS_USERNAME', 'nacos'),
                'password': os.getenv('NACOS_PASSWORD', 'nacos')
            }
            
            self.nacos_group = os.getenv('NACOS_GROUP', 'DEFAULT_GROUP')
            self.nacos_data_id = os.getenv('NACOS_DATA_ID', 'tamar-console-dev')
            self.local_dev_mode = os.getenv('LOCAL_DEV_MODE', 'true').lower() == 'true'
            
            # 服务注册信息
            self.service_info = {
                'name': os.getenv('SERVICE_NAME', 'tamar-console'),
                'domain': os.getenv('SERVICE_DOMAIN', '127.0.0.1'),
                'port': int(os.getenv('SERVICE_PORT', '8002'))
            }
            
            # 创建 Nacos 客户端（保持连接）
            if not self.nacos_client:
                self.nacos_client = NacosClient(
                    self.nacos_config['server_addresses'],
                    namespace=self.nacos_config['namespace'],
                    username=self.nacos_config['username'],
                    password=self.nacos_config['password']
                )
                logger.info(f"Nacos客户端初始化成功: {self.nacos_config['server_addresses']}")
        except Exception as e:
            logger.error(f"初始化配置失败: {e}")
            raise
    
    def _load_config(self):
        """加载配置"""
        try:
            # 尝试从 Nacos 加载配置
            config = self._load_from_nacos()
            self.last_refresh_time = datetime.now()
            self.config_version += 1
            logger.info(f"配置加载成功，版本: {self.config_version}")
            return config
        except Exception as e:
            logger.error(f"从 Nacos 加载配置失败: {e}")
            # 如果是首次加载失败，抛出异常
            if not hasattr(self, '_config'):
                raise
            # 如果是刷新失败，保持现有配置
            logger.warning("配置刷新失败，保持现有配置")
            return self._config
    
    def _load_from_nacos(self):
        """从 Nacos 加载配置"""
        # if self.local_dev_mode:
        #     # 本地开发模式，使用默认配置
        #     logger.info("本地开发模式，使用默认配置")
        #     return self._get_default_config()
        
        if not self.nacos_client:
            raise ValueError("Nacos客户端未初始化")
        
        # 获取配置
        config_str = self.nacos_client.get_config(self.nacos_data_id, self.nacos_group)
        
        if not config_str:
            logger.warning(f"Nacos配置为空: {self.nacos_data_id}/{self.nacos_group}")
            return self._get_default_config()
        
        # 解析配置（支持 Properties、YAML 和 JSON）
        if self._is_properties_format(config_str):
            config = self._parse_properties(config_str)
        else:
            # 尝试 YAML 或 JSON
            try:
                config = yaml.safe_load(config_str)
            except:
                try:
                    config = json.loads(config_str)
                except:
                    logger.error(f"无法解析配置格式: {config_str[:100]}...")
                    raise
        logger.debug(f"成功加载配置，包含 {len(config)} 个配置项")
        return config
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            'PG_DB_HOST': 'localhost',
            'PG_DB_PORT': 5432,
            'PG_DB_USERNAME': 'jettask',
            'PG_DB_PASSWORD': '123456',
            'PG_DB_DATABASE': 'jettask',
            'REDIS_HOST': 'localhost',
            'REDIS_PORT': 6379,
            'REDIS_DB': 0,
            'REDIS_PASSWORD': None
        }
    
    def _is_properties_format(self, config_str):
        """判断是否为 Properties 格式"""
        lines = config_str.strip().split('\n')
        for line in lines:
            line = line.strip()
            if line and not line.startswith('#'):
                return '=' in line
        return False
    
    def _parse_properties(self, config_str):
        """解析 Properties 格式配置"""
        config = {}
        lines = config_str.strip().split('\n')
        
        for line in lines:
            line = line.strip()
            # 跳过空行和注释
            if not line or line.startswith('#'):
                continue
            
            # 解析键值对
            if '=' in line:
                key, value = line.split('=', 1)
                key = key.strip()
                value = value.strip()
                
                # 转换为嵌套字典
                parts = key.split('.')
                current = config
                for i, part in enumerate(parts[:-1]):
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                
                # 尝试转换数据类型
                final_value = value
                if value.lower() == 'true':
                    final_value = True
                elif value.lower() == 'false':
                    final_value = False
                elif value.isdigit():
                    final_value = int(value)
                elif self._is_float(value):
                    final_value = float(value)
                
                current[parts[-1]] = final_value
        
        return config
    
    def _is_float(self, value):
        """判断字符串是否为浮点数"""
        try:
            float(value)
            return '.' in value
        except:
            return False
    
    def get_database_url(self):
        """构建数据库连接字符串（FastAPI 使用）"""
        return self._get_database_uri()
    
    def _get_database_uri(self):
        """构建数据库连接字符串"""
        config = self.config
        host = config.get("PG_DB_HOST")
        port = config.get("PG_DB_PORT")
        username = config.get("PG_DB_USERNAME")
        password = config.get("PG_DB_PASSWORD")
        database = config.get("PG_DB_DATABASE")
        return f'postgresql+asyncpg://{username}:{password}@{host}:{port}/{database}'
    
    def get_redis_connection(self):
        """获取 Redis 异步连接实例"""
        config = self.config

        redis_host = config.get("REDIS_HOST", "localhost")
        redis_port = int(config.get("REDIS_PORT", "6379"))
        redis_db = int(config.get("REDIS_DB", "0"))
        redis_password = config.get("REDIS_PASSWORD") or None
        redis_user = config.get("REDIS_USER") or None

        # 构建 redis:// 或 rediss:// 的 URL（注意 password 可能为空）
        if redis_user:
            redis_url = f"redis://{redis_user}:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        elif redis_password:
            redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
        else:
            redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
        return redis_url
    
    def get(self, key, default=None):
        """获取配置项（线程安全）"""
        return self.config.get(key, default)
    
    def refresh(self) -> bool:
        """手动刷新配置
        
        Returns:
            True if config was refreshed, False otherwise
        """
        # 如果还未初始化，不执行刷新
        if not self._initialized:
            logger.debug("配置尚未初始化，跳过刷新")
            return False
        
        try:
            logger.info("手动触发配置刷新")
            old_config = self._config.copy() if self._config else {}
            
            with self._config_lock:
                new_config = self._load_config()
                self._config = new_config
            
            # 检查配置是否有变化
            if old_config != new_config:
                logger.info("配置已更新，通知监听器")
                self._notify_listeners(new_config)
                return True
            else:
                logger.debug("配置无变化")
                return False
        except Exception as e:
            logger.error(f"刷新配置失败: {e}")
            return False
    
    def start_refresh_thread(self):
        """启动定时刷新线程"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            logger.warning("刷新线程已在运行")
            return
        
        self.stop_refresh.clear()
        self.refresh_thread = threading.Thread(
            target=self._refresh_loop,
            name="NacosConfigRefresh",
            daemon=True
        )
        self.refresh_thread.start()
        logger.info(f"配置刷新线程已启动，刷新间隔: {self.refresh_interval}秒")
    
    def stop_refresh_thread(self):
        """停止定时刷新线程"""
        if self.refresh_thread and self.refresh_thread.is_alive():
            logger.info("正在停止配置刷新线程...")
            self.stop_refresh.set()
            self.refresh_thread.join(timeout=5)
            logger.info("配置刷新线程已停止")
    
    def _refresh_loop(self):
        """刷新循环"""
        logger.info("配置刷新循环已开始")
        
        while not self.stop_refresh.is_set():
            try:
                # 等待指定的刷新间隔
                if self.stop_refresh.wait(self.refresh_interval):
                    break
                
                # 执行刷新
                self.refresh()
                
            except Exception as e:
                logger.error(f"配置刷新循环异常: {e}")
                # 发生异常后等待一段时间再重试
                if self.stop_refresh.wait(10):
                    break
        
        logger.info("配置刷新循环已结束")
    
    def add_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """添加配置变更监听器
        
        Args:
            listener: 配置变更时的回调函数，接收新配置作为参数
        """
        if listener not in self.change_listeners:
            self.change_listeners.append(listener)
            logger.info(f"添加配置变更监听器: {listener.__name__}")
    
    def remove_change_listener(self, listener: Callable[[Dict[str, Any]], None]):
        """移除配置变更监听器"""
        if listener in self.change_listeners:
            self.change_listeners.remove(listener)
            logger.info(f"移除配置变更监听器: {listener.__name__}")
    
    def _notify_listeners(self, new_config: Dict[str, Any]):
        """通知所有监听器配置已变更"""
        for listener in self.change_listeners:
            try:
                listener(new_config)
            except Exception as e:
                logger.error(f"配置变更监听器执行失败 {listener.__name__}: {e}")
    
    def get_config_info(self) -> Dict[str, Any]:
        """获取配置信息"""
        return {
            'initialized': self._initialized,
            'version': self.config_version,
            'last_refresh_time': self.last_refresh_time.isoformat() if self.last_refresh_time else None,
            'refresh_interval': self.refresh_interval,
            'refresh_thread_active': self.refresh_thread.is_alive() if self.refresh_thread else False,
            'nacos_server': self.nacos_config['server_addresses'] if self.nacos_config else None,
            'nacos_namespace': self.nacos_config['namespace'] if self.nacos_config else None,
            'nacos_group': self.nacos_group,
            'nacos_data_id': self.nacos_data_id,
            'local_dev_mode': self.local_dev_mode,
            'config_items_count': len(self._config) if self._config else 0
        }

    def get_namespaces(self) -> Optional[List[Dict[str, Any]]]:
        """从 Nacos 获取所有命名空间列表

        Returns:
            命名空间列表，每个元素包含:
            - namespace: 命名空间ID
            - namespaceShowName: 命名空间显示名称
            - namespaceDesc: 命名空间描述
            - quota: 配额
            - configCount: 配置数量
            - type: 类型 (0: Global, 1: Default Private, 2: Custom)

            如果获取失败返回 None

        Example:
            >>> config = Config()
            >>> namespaces = config.get_namespaces()
            >>> for ns in namespaces:
            ...     print(f"{ns['namespaceShowName']} ({ns['namespace']})")
        """
        if not self.nacos_config:
            logger.error("Nacos配置未初始化")
            return None

        try:
            # 构建请求URL
            server_addr = self.nacos_config['server_addresses']
            if not server_addr.startswith('http'):
                server_addr = f'http://{server_addr}'

            # 使用 Nacos v2 API
            url = f"{server_addr}/nacos/v2/console/namespace/list"

            logger.info(f"正在从 Nacos 获取命名空间列表: {url}")

            # 构建认证参数
            params = {}
            if self.nacos_config.get('username') and self.nacos_config.get('password'):
                # 注意：某些 Nacos 版本可能需要先获取 accessToken
                # 这里使用基本认证
                params['username'] = self.nacos_config['username']
                params['password'] = self.nacos_config['password']

            # 添加参数到URL
            if params:
                url = f"{url}?{urlencode(params)}"

            # 发送HTTP请求
            req = Request(url)
            req.add_header('User-Agent', 'JetTask-NacosClient/1.0')

            with urlopen(req, timeout=10) as response:
                response_data = response.read().decode('utf-8')
                result = json.loads(response_data)

            # 检查响应
            if result.get('code') == 0 or result.get('code') == 200:
                namespaces = result.get('data', [])
                logger.info(f"成功获取 {len(namespaces)} 个命名空间")
                logger.debug(f"命名空间列表: {namespaces}")
                return namespaces
            else:
                logger.error(f"获取命名空间失败: {result.get('message', 'Unknown error')}")
                return None

        except Exception as e:
            logger.error(f"获取命名空间列表异常: {e}", exc_info=True)
            return None

    def get_namespace_configs(self, namespace_id: str, group: str = None) -> Optional[Dict[str, Any]]:
        """获取指定命名空间的配置

        Args:
            namespace_id: 命名空间ID
            group: 配置组，默认使用当前配置的group

        Returns:
            配置字典，失败返回 None
        """
        if not self.nacos_config:
            logger.error("Nacos配置未初始化")
            return None

        try:
            # 创建临时客户端连接到指定命名空间
            temp_client = NacosClient(
                self.nacos_config['server_addresses'],
                namespace=namespace_id,
                username=self.nacos_config['username'],
                password=self.nacos_config['password']
            )

            # 使用指定的group或默认group
            target_group = group or self.nacos_group

            # 获取配置
            config_str = temp_client.get_config(self.nacos_data_id, target_group)

            if not config_str:
                logger.warning(f"命名空间 {namespace_id} 的配置为空")
                return {}

            # 解析配置（支持 Properties、YAML 和 JSON）
            if self._is_properties_format(config_str):
                config = self._parse_properties(config_str)
            else:
                try:
                    config = yaml.safe_load(config_str)
                except:
                    try:
                        config = json.loads(config_str)
                    except:
                        logger.error(f"无法解析命名空间 {namespace_id} 的配置格式")
                        return None

            logger.info(f"成功获取命名空间 {namespace_id} 的配置，包含 {len(config)} 个配置项")
            return config

        except Exception as e:
            logger.error(f"获取命名空间 {namespace_id} 配置异常: {e}", exc_info=True)
            return None
    
    def __del__(self):
        """析构函数，确保线程正确关闭"""
        self.stop_refresh_thread()


# 创建全局配置实例（默认30秒刷新一次）
config = NacosConfigLoader(refresh_interval=30)