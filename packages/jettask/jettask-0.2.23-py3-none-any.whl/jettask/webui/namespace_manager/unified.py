"""
统一的数据消费者管理器
自动识别单命名空间和多命名空间模式
"""
import asyncio
import logging
import multiprocessing
from typing import Dict, Optional, Set
from jettask.core.unified_manager_base import UnifiedManagerBase
from .multi import NamespaceConsumerProcess

logger = logging.getLogger(__name__)


class UnifiedConsumerManager(UnifiedManagerBase):
    """
    统一的消费者管理器
    继承自 UnifiedManagerBase，实现消费者特定的逻辑
    """
    
    def __init__(self, 
                 task_center_url: str,
                 check_interval: int = 30,
                 debug: bool = False):
        """
        初始化消费者管理器
        
        Args:
            task_center_url: 任务中心URL
            check_interval: 命名空间检测间隔（秒）
            debug: 是否启用调试模式
        """
        super().__init__(task_center_url, check_interval, debug)
        
        # 消费者进程管理
        self.consumer_processes: Dict[str, NamespaceConsumerProcess] = {}
        self.known_namespaces: Set[str] = set()
        
    @property
    def processes(self):
        """提供对外的进程访问接口"""
        return self.consumer_processes
    
    async def run_single_namespace(self, namespace_name: str):
        """
        运行单命名空间模式
        
        Args:
            namespace_name: 命名空间名称
        """
        logger.info(f"启动单命名空间消费者: {namespace_name}")
        
        # 获取命名空间配置
        namespaces = await self.fetch_namespaces_info({namespace_name})
        
        if not namespaces:
            logger.error(f"未找到命名空间配置: {namespace_name}")
            return
        
        ns_info = namespaces[0]
        
        # 创建并启动消费进程
        consumer = NamespaceConsumerProcess(ns_info)
        consumer.start()
        self.consumer_processes[namespace_name] = consumer
        
        try:
            # 保持运行，定期检查进程状态
            while self.running:
                await asyncio.sleep(10)
                
                # 检查进程是否存活
                if not consumer.is_alive():
                    logger.warning(f"命名空间 {namespace_name} 的消费进程已停止，尝试重启")
                    consumer.start()
        except asyncio.CancelledError:
            logger.info("收到取消信号")
    
    async def run_multi_namespace(self, namespace_names: Optional[Set[str]]):
        """
        运行多命名空间模式
        
        Args:
            namespace_names: 目标命名空间集合，None表示所有命名空间
        """
        logger.info("启动多命名空间消费者管理")
        
        # 获取初始命名空间配置
        namespaces = await self.fetch_namespaces_info(namespace_names)
        
        # 启动每个命名空间的消费者
        for ns_info in namespaces:
            try:
                self._start_namespace_consumer(ns_info)
                self.known_namespaces.add(ns_info['name'])
            except Exception as e:
                logger.error(f"启动命名空间 {ns_info['name']} 的消费者失败: {e}")
        
        # 创建并发任务
        try:
            health_check_task = asyncio.create_task(self._health_check_loop())
            namespace_check_task = asyncio.create_task(self._namespace_check_loop())
            
            # 等待任一任务完成或出错
            done, pending = await asyncio.wait(
                [health_check_task, namespace_check_task],
                return_when=asyncio.FIRST_EXCEPTION
            )
            
            # 取消所有未完成的任务
            for task in pending:
                task.cancel()
                
        except asyncio.CancelledError:
            logger.info("收到取消信号")
    
    def _start_namespace_consumer(self, namespace_info: dict):
        """启动单个命名空间的消费者"""
        name = namespace_info['name']
        
        # 如果已存在，先停止
        if name in self.consumer_processes:
            self.consumer_processes[name].stop()
        
        # 创建并启动新进程
        consumer = NamespaceConsumerProcess(namespace_info)
        consumer.start()
        self.consumer_processes[name] = consumer
        logger.info(f"启动命名空间 {name} 的消费进程")
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查所有消费进程的健康状态
                for name, consumer in list(self.consumer_processes.items()):
                    if not consumer.is_alive():
                        logger.warning(f"命名空间 {name} 的消费进程已停止，尝试重启")
                        
                        # 重新获取配置并重启
                        namespaces = await self.fetch_namespaces_info({name})
                        if namespaces:
                            self._start_namespace_consumer(namespaces[0])
                        else:
                            logger.error(f"无法获取命名空间 {name} 的配置")
                            
            except Exception as e:
                logger.error(f"健康检查错误: {e}")
    
    async def _namespace_check_loop(self):
        """命名空间检测循环（动态添加/移除）"""
        while self.running:
            try:
                await asyncio.sleep(self.check_interval)
                
                # 获取当前所有命名空间
                current_namespaces = await self.fetch_namespaces_info()
                current_names = {ns['name'] for ns in current_namespaces}
                
                # 检测新增的命名空间
                new_names = current_names - self.known_namespaces
                for name in new_names:
                    logger.info(f"检测到新命名空间: {name}")
                    ns_info = next(ns for ns in current_namespaces if ns['name'] == name)
                    self._start_namespace_consumer(ns_info)
                    self.known_namespaces.add(name)
                
                # 检测删除的命名空间
                removed_names = self.known_namespaces - current_names
                for name in removed_names:
                    logger.info(f"检测到命名空间已删除: {name}")
                    if name in self.consumer_processes:
                        self.consumer_processes[name].stop()
                        del self.consumer_processes[name]
                    self.known_namespaces.discard(name)
                    
            except Exception as e:
                logger.error(f"命名空间检测错误: {e}")
    
    async def cleanup(self):
        """清理资源"""
        logger.info("停止所有消费进程")
        
        for name, consumer in self.consumer_processes.items():
            try:
                consumer.stop()
                logger.info(f"停止命名空间 {name} 的消费进程")
            except Exception as e:
                logger.error(f"停止命名空间 {name} 的消费进程失败: {e}")
        
        self.consumer_processes.clear()