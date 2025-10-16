#!/usr/bin/env python
"""多命名空间消费者管理器

为每个命名空间启动独立的pg_consumer进程
支持动态添加/移除命名空间
"""

import asyncio
import logging
import multiprocessing as mp
import signal
import sys
import os
from typing import Dict, Optional, Set
from datetime import datetime

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from jettask.persistence import PostgreSQLConsumer
from jettask.webui.config import PostgreSQLConfig, RedisConfig
# ConsumerStrategy 已移除，现在只使用 HEARTBEAT 策略
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(process)d - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NamespaceConsumerProcess:
    """单个命名空间的消费进程"""
    
    def __init__(self, namespace_info: dict):
        """
        Args:
            namespace_info: 命名空间配置信息，包含:
                - id: 命名空间ID
                - name: 命名空间名称
                - redis_config: Redis配置
                - pg_config: PostgreSQL配置
                - redis_prefix: Redis键前缀
        """
        self.namespace_info = namespace_info
        self.process: Optional[mp.Process] = None
        self.shutdown_event = mp.Event()  # 用于优雅退出的事件
        
    def start(self):
        """启动进程"""
        if self.process and self.process.is_alive():
            logger.warning(f"命名空间 {self.namespace_info['name']} 的消费进程已在运行")
            return
            
        self.process = mp.Process(
            target=self._run_consumer,
            name=f"consumer_{self.namespace_info['name']}"
        )
        self.process.daemon = False
        self.process.start()
        logger.info(f"启动命名空间 {self.namespace_info['name']} 的消费进程, PID: {self.process.pid}")
        
    def stop(self):
        """停止进程"""
        if self.process and self.process.is_alive():
            logger.info(f"停止命名空间 {self.namespace_info['name']} 的消费进程")
            # 先发送优雅退出信号
            self.shutdown_event.set()
            # 等待进程正常退出（7秒：5秒清理超时 + 2秒缓冲）
            self.process.join(timeout=7)
            if self.process.is_alive():
                logger.warning(f"等待优雅退出超时（7秒），发送 SIGTERM 信号")
                self.process.terminate()
                self.process.join(timeout=3)
            if self.process.is_alive():
                logger.warning(f"SIGTERM 超时（3秒），强制 SIGKILL")
                self.process.kill()
                self.process.join(timeout=2)
            if self.process.is_alive():
                logger.error(f"SIGKILL 后进程仍然存活，可能存在严重问题")
                
    def is_alive(self) -> bool:
        """检查进程是否存活"""
        return self.process and self.process.is_alive()
        
    def _run_consumer(self):
        """在子进程中运行消费者"""
        # 设置信号处理
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)

        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        consumer = None
        try:
            # 传递 consumer 引用以便在信号处理中使用
            consumer = loop.run_until_complete(self._async_run())
        except KeyboardInterrupt:
            logger.info(f"命名空间 {self.namespace_info['name']} 的消费进程收到中断信号")
        except Exception as e:
            logger.error(f"命名空间 {self.namespace_info['name']} 的消费进程异常退出: {e}", exc_info=True)
        finally:
            # 确保执行清理（带超时）
            if consumer:
                try:
                    logger.info(f"执行命名空间 {self.namespace_info['name']} 的消费者清理")
                    # 创建一个带超时的任务
                    async def cleanup_with_timeout():
                        try:
                            await asyncio.wait_for(consumer.stop(), timeout=5.0)
                        except asyncio.TimeoutError:
                            logger.warning(f"外层清理超时（5秒），强制退出")

                    loop.run_until_complete(cleanup_with_timeout())
                except Exception as e:
                    logger.error(f"清理消费者时出错: {e}")
            loop.close()
            
    async def _async_run(self):
        """异步运行消费者"""
        namespace_name = self.namespace_info.get('name', 'unknown')
        logger.info(f"开始初始化命名空间 {namespace_name} 的消费者")

        consumer = None
        try:
            # 创建配置
            pg_config_data = self.namespace_info.get('pg_config', {})
            
            # 如果包含 url 字段，使用 from_url 方法
            if 'url' in pg_config_data:
                pg_config = PostgreSQLConfig.from_url(pg_config_data['url'])
            else:
                # 移除不支持的字段
                valid_fields = {'host', 'port', 'database', 'user', 'password'}
                filtered_config = {k: v for k, v in pg_config_data.items() if k in valid_fields}
                pg_config = PostgreSQLConfig(**filtered_config)
            
            redis_config_data = self.namespace_info.get('redis_config', {})
            
            # 如果包含 url 字段，解析它
            if 'url' in redis_config_data:
                from urllib.parse import urlparse
                parsed = urlparse(redis_config_data['url'])
                redis_config = RedisConfig(
                    host=parsed.hostname or 'localhost',
                    port=parsed.port or 6379,
                    db=int(parsed.path.lstrip('/')) if parsed.path and parsed.path != '/' else 0,
                    password=parsed.password
                )
            else:
                # 移除不支持的字段
                valid_fields = {'host', 'port', 'db', 'password'}
                filtered_config = {k: v for k, v in redis_config_data.items() if k in valid_fields}
                redis_config = RedisConfig(**filtered_config)
            
            print(f'{pg_config=}')
            print(f'{redis_config=}')
            # 创建消费者实例
            consumer = PostgreSQLConsumer(
                pg_config=pg_config,
                redis_config=redis_config,
                prefix=self.namespace_info.get('redis_prefix', 'jettask'),
                namespace_id=self.namespace_info.get('id'),
                namespace_name=self.namespace_info.get('name'),
                # consumer_strategy 参数已移除，现在只使用 HEARTBEAT 策略
            )
            
            logger.info(f"命名空间 {namespace_name} 的消费者实例创建成功，准备启动")
            
            # 启动消费者
            await consumer.start()
            logger.info(f"命名空间 {namespace_name} 的消费者已启动，进入运行状态")

            # 保持运行直到收到停止信号
            try:
                while not self.shutdown_event.is_set():
                    await asyncio.sleep(1)  # 每秒检查一次退出信号
            except asyncio.CancelledError:
                logger.info(f"命名空间 {namespace_name} 的消费者收到取消信号")
            finally:
                # 确保清理（带超时）
                logger.info(f"命名空间 {namespace_name} 开始执行优雅退出")
                try:
                    # 设置 5 秒超时，避免因网络问题导致清理卡住
                    await asyncio.wait_for(consumer.stop(), timeout=5.0)
                    logger.info(f"命名空间 {namespace_name} 清理完成")
                except asyncio.TimeoutError:
                    logger.warning(f"命名空间 {namespace_name} 清理超时（5秒），强制退出")
                except Exception as e:
                    logger.error(f"命名空间 {namespace_name} 清理失败: {e}")

        except Exception as e:
            logger.error(f"命名空间 {namespace_name} 的消费者启动失败: {e}", exc_info=True)
            # 确保清理（带超时）
            if consumer:
                try:
                    await asyncio.wait_for(consumer.stop(), timeout=5.0)
                except asyncio.TimeoutError:
                    logger.warning(f"清理失败的消费者超时，跳过")
                except Exception as cleanup_error:
                    logger.error(f"清理失败的消费者时出错: {cleanup_error}")
            raise
        finally:
            # 返回 consumer 实例以便在外层 finally 中使用
            return consumer
            
    def _signal_handler(self, signum, frame):
        """信号处理器 - 触发优雅退出"""
        logger.info(f"命名空间 {self.namespace_info['name']} 的消费进程收到信号 {signum}")
        # 设置退出事件，让主循环优雅退出
        self.shutdown_event.set()


class MultiNamespaceConsumerManager:
    """多命名空间消费者管理器"""
    
    def __init__(self, 
                 task_center_url: str,
                 namespace_check_interval: int = 60):
        """
        初始化管理器
        
        Args:
            task_center_url: 任务中心的URL（必需，从中获取数据库配置）
            namespace_check_interval: 命名空间检测间隔（秒）
        """
        self.consumers: Dict[str, NamespaceConsumerProcess] = {}
        self.running = False
        self.task_center_url = task_center_url.rstrip('/')
        self.namespace_check_interval = namespace_check_interval
        self.task_center_db_url = None
        
        logger.info(f"命名空间检测间隔设置为: {self.namespace_check_interval} 秒")
        self.known_namespaces: Set[str] = set()  # 已知的命名空间集合
            
    async def start(self, namespace_names: Optional[Set[str]] = None):
        """启动管理器
        
        Args:
            namespace_names: 要启动的命名空间名称集合，None表示启动所有命名空间
        """
        self.running = True
        logger.info("启动多命名空间消费者管理器")
        
        # 从任务中心获取数据库配置
        await self._init_database_config()
        
        # 获取命名空间配置
        namespaces = await self._fetch_namespaces(namespace_names)
        
        # 启动每个命名空间的消费者
        for ns_info in namespaces:
            try:
                self._start_namespace_consumer(ns_info)
                self.known_namespaces.add(ns_info['name'])
            except Exception as e:
                logger.error(f"启动命名空间 {ns_info['name']} 的消费者失败: {e}")
                
        # 创建并发任务：健康检查和命名空间检测
        try:
            health_check_task = asyncio.create_task(self._health_check_loop())
            namespace_check_task = asyncio.create_task(self._namespace_check_loop())
            
            # 等待任一任务完成（或出错）
            done, pending = await asyncio.wait(
                [health_check_task, namespace_check_task],
                return_when=asyncio.FIRST_EXCEPTION
            )
            
            # 取消所有未完成的任务
            for task in pending:
                task.cancel()
                
        except KeyboardInterrupt:
            logger.info("收到中断信号，停止管理器")
        finally:
            await self.stop()
            
    async def stop(self):
        """停止所有消费者"""
        self.running = False
        logger.info("停止所有命名空间消费者")
        
        for name, consumer in self.consumers.items():
            consumer.stop()
            
        self.consumers.clear()
        
    def _start_namespace_consumer(self, namespace_info: dict):
        """启动单个命名空间的消费者"""
        name = namespace_info['name']
        
        # 如果已存在，先停止
        if name in self.consumers:
            self.consumers[name].stop()
            
        # 创建并启动新进程
        consumer = NamespaceConsumerProcess(namespace_info)
        consumer.start()
        self.consumers[name] = consumer
        
    async def _init_database_config(self):
        """从任务中心获取数据库配置"""
        import aiohttp
        import json
        
        # 根据 URL 格式判断如何获取配置
        base_url = self.task_center_url
        
        # 如果是单命名空间URL，提取基础URL
        if '/api/namespaces/' in base_url:
            # 从 http://localhost:8001/api/namespaces/default 提取 http://localhost:8001
            base_url = base_url.split('/api/namespaces/')[0]
        elif '/api/v1/namespaces/' in base_url:
            # 从 http://localhost:8001/api/v1/namespaces/default 提取 http://localhost:8001
            base_url = base_url.split('/api/v1/namespaces/')[0]
        
        # 获取API服务的配置端点
        config_url = f"{base_url}/api/config"
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(config_url) as response:
                    if response.status == 200:
                        config = await response.json()
                        # 从配置中提取数据库URL
                        if 'database' in config:
                            db_config = config['database']
                            host = db_config.get('host', 'localhost')
                            port = db_config.get('port', 5432)
                            user = db_config.get('user', 'jettask')
                            password = db_config.get('password', '123456')
                            database = db_config.get('database', 'jettask')
                            self.task_center_db_url = f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{database}"
                        else:
                            # 如果没有配置端点，使用默认值
                            logger.warning(f"无法从任务中心获取数据库配置，使用默认配置")
                            self.task_center_db_url = "postgresql+asyncpg://jettask:123456@localhost:5432/jettask"
                    else:
                        # API端点不存在，使用默认值
                        logger.warning(f"任务中心配置端点返回错误: {response.status}，使用默认配置")
                        self.task_center_db_url = "postgresql+asyncpg://jettask:123456@localhost:5432/jettask"
        except Exception as e:
            logger.warning(f"无法连接到任务中心获取配置: {e}，使用默认配置")
            # 使用默认配置
            self.task_center_db_url = "postgresql+asyncpg://jettask:123456@localhost:5432/jettask"
        
        logger.info(f"数据库配置已初始化")
        
    async def _fetch_namespaces(self, namespace_names: Optional[Set[str]] = None) -> list:
        """从任务中心数据库获取命名空间配置"""
        engine = create_async_engine(self.task_center_db_url, echo=False)
        AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
        
        namespaces = []
        
        async with AsyncSessionLocal() as session:
            try:
                # 查询命名空间
                if namespace_names:
                    query = text("""
                        SELECT id, name, redis_config, pg_config 
                        FROM namespaces 
                        WHERE name = ANY(:names)
                    """)
                    result = await session.execute(query, {'names': list(namespace_names)})
                else:
                    query = text("""
                        SELECT id, name, redis_config, pg_config 
                        FROM namespaces
                    """)
                    result = await session.execute(query)
                    
                for row in result:
                    # 直接使用 redis_config 和 pg_config
                    redis_cfg = row.redis_config if row.redis_config else {}
                    pg_cfg = row.pg_config if row.pg_config else {}
                    
                    # 处理 Redis 密码：如果为空字符串或 "None"，设置为 None
                    redis_password = redis_cfg.get('password')
                    if redis_password in ['', 'None', 'null']:
                        redis_password = None
                    
                    # 确定 Redis 前缀：
                    # 1. 优先使用配置中的 prefix
                    # 2. 其次使用命名空间名
                    # 3. 最后使用 'jettask' 作为默认值
                    redis_prefix = redis_cfg.get('prefix')
                    if not redis_prefix:
                        # 使用命名空间名作为前缀，这样不同命名空间的数据在 Redis 中是隔离的
                        redis_prefix = row.name
                    
                    logger.info(f"命名空间 {row.name} 使用 Redis 前缀: {redis_prefix}")
                    
                    namespaces.append({
                        'id': row.id,
                        'name': row.name,
                        'redis_config': {
                            'host': redis_cfg.get('host', 'localhost'),
                            'port': redis_cfg.get('port', 6379),
                            'db': redis_cfg.get('db', 0),
                            'password': redis_password
                        },
                        'pg_config': {
                            'host': pg_cfg.get('host', 'localhost'),
                            'port': pg_cfg.get('port', 5432),
                            'database': pg_cfg.get('database', 'jettask'),
                            'user': pg_cfg.get('user', 'jettask'),
                            'password': pg_cfg.get('password', '123456')
                        },
                        'redis_prefix': redis_prefix
                    })
                        
            except Exception as e:
                logger.error(f"查询命名空间失败: {e}")
                # 如果查询失败，使用默认配置
                if not namespace_names or 'default' in namespace_names:
                    namespaces.append(self._get_default_namespace())
                    
        await engine.dispose()
        return namespaces
        
    def _parse_connection_config(self, connection_url: str) -> Optional[dict]:
        """解析连接配置字符串"""
        try:
            import json
            config = json.loads(connection_url)
            
            # 提取Redis配置
            redis_config = {}
            if 'redis' in config:
                redis_info = config['redis']
                redis_config = {
                    'host': redis_info.get('host', 'localhost'),
                    'port': redis_info.get('port', 6379),
                    'db': redis_info.get('db', 0),
                    'password': redis_info.get('password')
                }
                
            # 提取PostgreSQL配置
            pg_config = {}
            if 'postgres' in config:
                pg_info = config['postgres']
                pg_config = {
                    'host': pg_info.get('host', 'localhost'),
                    'port': pg_info.get('port', 5432),
                    'database': pg_info.get('database', 'jettask'),
                    'user': pg_info.get('user', 'jettask'),
                    'password': pg_info.get('password', '123456')
                }
                
            return {
                'redis_config': redis_config,
                'pg_config': pg_config,
                'redis_prefix': config.get('prefix', 'jettask')
            }
            
        except Exception as e:
            logger.error(f"解析连接配置失败: {e}")
            return None
            
    def _get_default_namespace(self) -> dict:
        """获取默认命名空间配置"""
        return {
            'id': 'default',
            'name': 'default',
            'redis_config': {
                'host': os.environ.get('REDIS_HOST', 'localhost'),
                'port': int(os.environ.get('REDIS_PORT', 6379)),
                'db': int(os.environ.get('REDIS_DB', 0)),
                'password': os.environ.get('REDIS_PASSWORD')
            },
            'pg_config': {
                'host': os.environ.get('POSTGRES_HOST', 'localhost'),
                'port': int(os.environ.get('POSTGRES_PORT', 5432)),
                'database': os.environ.get('POSTGRES_DB', 'jettask'),
                'user': os.environ.get('POSTGRES_USER', 'jettask'),
                'password': os.environ.get('POSTGRES_PASSWORD', '123456')
            },
            'redis_prefix': os.environ.get('REDIS_PREFIX', 'default')  # 使用 'default' 作为默认命名空间的前缀
        }
        
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                await self._health_check()
                await asyncio.sleep(30)  # 每30秒检查一次
            except Exception as e:
                logger.error(f"健康检查出错: {e}", exc_info=True)
                await asyncio.sleep(30)
                
    async def _namespace_check_loop(self):
        """命名空间检测循环"""
        # 首次启动后快速检测一次（5秒后）
        first_check_delay = min(5, self.namespace_check_interval)
        await asyncio.sleep(first_check_delay)
        
        while self.running:
            try:
                await self._check_new_namespaces()
                await asyncio.sleep(self.namespace_check_interval)
            except Exception as e:
                logger.error(f"命名空间检测出错: {e}", exc_info=True)
                await asyncio.sleep(self.namespace_check_interval)
                
    async def _check_new_namespaces(self):
        """检查是否有新的命名空间"""
        logger.debug("开始检查新命名空间...")
        
        # 获取所有活跃的命名空间
        current_namespaces = await self._fetch_namespaces()
        current_names = {ns['name'] for ns in current_namespaces}
        
        # 找出新增的命名空间
        new_names = current_names - self.known_namespaces
        if new_names:
            logger.info(f"发现新的命名空间: {new_names}")
            
            # 为新命名空间启动消费者
            for ns_info in current_namespaces:
                if ns_info['name'] in new_names:
                    try:
                        logger.info(f"为新命名空间 {ns_info['name']} 启动消费者")
                        self._start_namespace_consumer(ns_info)
                        self.known_namespaces.add(ns_info['name'])
                    except Exception as e:
                        logger.error(f"启动新命名空间 {ns_info['name']} 的消费者失败: {e}")
        
        # 找出被删除的命名空间
        removed_names = self.known_namespaces - current_names
        if removed_names:
            logger.info(f"发现被删除的命名空间: {removed_names}")
            
            # 停止被删除命名空间的消费者
            for name in removed_names:
                if name in self.consumers:
                    logger.info(f"停止已删除命名空间 {name} 的消费者")
                    self.consumers[name].stop()
                    del self.consumers[name]
                self.known_namespaces.discard(name)
                
    async def _health_check(self):
        """检查消费进程健康状态"""
        for name, consumer in list(self.consumers.items()):
            if not consumer.is_alive():
                logger.warning(f"命名空间 {name} 的消费进程已停止，尝试重启")
                
                # 重新获取配置并重启
                namespaces = await self._fetch_namespaces({name})
                if namespaces:
                    self._start_namespace_consumer(namespaces[0])
                else:
                    logger.error(f"无法获取命名空间 {name} 的配置，移除该消费者")
                    del self.consumers[name]
                    self.known_namespaces.discard(name)


async def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='多命名空间PostgreSQL消费者')
    parser.add_argument(
        '--namespaces',
        nargs='*',
        help='要启动的命名空间列表，不指定则启动所有命名空间'
    )
    
    args = parser.parse_args()
    
    # 创建管理器
    manager = MultiNamespaceConsumerManager()
    
    # 设置信号处理
    def signal_handler(signum, frame):
        logger.info(f"收到信号 {signum}，准备退出")
        asyncio.create_task(manager.stop())
        
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)
    
    # 启动管理器
    namespace_set = set(args.namespaces) if args.namespaces else None
    await manager.start(namespace_set)


if __name__ == '__main__':
    asyncio.run(main())