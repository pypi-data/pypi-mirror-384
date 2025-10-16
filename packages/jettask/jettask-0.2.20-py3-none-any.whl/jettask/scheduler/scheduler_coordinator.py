"""
统一的定时任务调度管理器
自动识别单命名空间和多命名空间模式
"""
import asyncio
import logging
import multiprocessing
from typing import Dict, Optional, Set
from jettask.core.unified_manager_base import UnifiedManagerBase
from jettask import Jettask
from jettask.task.task_center.client import TaskCenter
from .scheduler import TaskScheduler
from .task_crud import ScheduledTaskManager

logger = logging.getLogger(__name__)


class UnifiedSchedulerManager(UnifiedManagerBase):
    """
    统一的调度器管理器
    继承自 UnifiedManagerBase，实现调度器特定的逻辑
    """
    
    def __init__(self, 
                 task_center_url: str,
                 scan_interval: float = 0.1,
                 batch_size: int = 100,
                 check_interval: int = 30,
                 debug: bool = False):
        """
        初始化调度器管理器
        
        Args:
            task_center_url: 任务中心URL
            scan_interval: 调度器扫描间隔（秒）
            batch_size: 每批处理的最大任务数
            check_interval: 命名空间检测间隔（秒）
            debug: 是否启用调试模式
        """
        super().__init__(task_center_url, check_interval, debug)
        
        self.scan_interval = scan_interval
        self.batch_size = batch_size
        
        # 调度器管理
        self.scheduler_instance: Optional[TaskScheduler] = None  # 单命名空间模式
        self.scheduler_processes: Dict[str, multiprocessing.Process] = {}  # 多命名空间模式
        self.known_namespaces: Set[str] = set()
    
    async def run_single_namespace(self, namespace_name: str):
        """
        运行单命名空间模式
        
        Args:
            namespace_name: 命名空间名称
        """
        logger.info(f"启动单命名空间调度器: {namespace_name}")
        logger.info(f"扫描间隔: {self.scan_interval}秒")
        logger.info(f"批处理大小: {self.batch_size}")
        
        try:
            # 创建任务中心连接
            tc = TaskCenter(self.task_center_url)
            if not tc._connect_sync():
                raise Exception(f"无法连接到任务中心: {self.task_center_url}")
            
            # 创建 Jettask 应用
            app = Jettask(task_center=tc)

            # 创建调度器管理器（不需要传递namespace参数）
            manager = ScheduledTaskManager(app)

            # 创建并启动调度器
            self.scheduler_instance = TaskScheduler(
                app=app,
                db_manager=manager,
                scan_interval=self.scan_interval,
                batch_size=self.batch_size
            )

            # 运行调度器
            await self.scheduler_instance.run()
            
        except Exception as e:
            logger.error(f"单命名空间调度器运行失败: {e}", exc_info=self.debug)
            raise
    
    async def run_multi_namespace(self, namespace_names: Optional[Set[str]]):
        """
        运行多命名空间模式
        
        Args:
            namespace_names: 目标命名空间集合，None表示所有命名空间
        """
        logger.info("启动多命名空间调度器管理")
        logger.info(f"扫描间隔: {self.scan_interval}秒")
        logger.info(f"批处理大小: {self.batch_size}")
        
        # 获取初始命名空间
        namespaces = await self.fetch_namespaces_info(namespace_names)
        
        # 启动每个命名空间的调度器进程
        for ns_info in namespaces:
            self._start_scheduler_process(ns_info['name'])
            self.known_namespaces.add(ns_info['name'])
        
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
    
    def _start_scheduler_process(self, namespace_name: str):
        """启动单个命名空间的调度器进程"""
        
        # 如果进程已存在且存活，跳过
        if namespace_name in self.scheduler_processes:
            process = self.scheduler_processes[namespace_name]
            if process.is_alive():
                logger.debug(f"命名空间 {namespace_name} 的调度器进程已在运行")
                return
            else:
                # 清理已停止的进程
                process.terminate()
                process.join(timeout=5)
        
        # 创建新进程
        process = multiprocessing.Process(
            target=self._run_scheduler_for_namespace,
            args=(namespace_name, self.task_center_url, self.scan_interval, self.batch_size),
            name=f"scheduler_{namespace_name}"
        )
        process.daemon = False
        process.start()
        
        self.scheduler_processes[namespace_name] = process
        logger.info(f"启动命名空间 {namespace_name} 的调度器进程, PID: {process.pid}")
    
    @staticmethod
    def _run_scheduler_for_namespace(namespace_name: str, task_center_url: str, 
                                      scan_interval: float, batch_size: int):
        """在独立进程中运行单个命名空间的调度器"""
        import asyncio
        import signal
        import sys
        
        # 设置信号处理
        def signal_handler(signum, frame):
            logger.info(f"命名空间 {namespace_name} 的调度器进程收到信号 {signum}")
            sys.exit(0)
        
        signal.signal(signal.SIGTERM, signal_handler)
        signal.signal(signal.SIGINT, signal_handler)
        
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        async def run_scheduler():
            try:
                # 构建命名空间特定的URL
                # 需要处理多种格式:
                # 1. http://localhost:8001 -> http://localhost:8001/api/v1/namespaces/{name}
                # 2. http://localhost:8001/api/v1 -> http://localhost:8001/api/v1/namespaces/{name}
                # 3. http://localhost:8001/api/v1/namespaces/old -> http://localhost:8001/api/v1/namespaces/{name}

                if '/api/v1/namespaces/' in task_center_url:
                    # 替换现有的命名空间
                    base_url = task_center_url.split('/api/v1/namespaces/')[0]
                    url = f"{base_url}/api/v1/namespaces/{namespace_name}"
                elif '/api/namespaces/' in task_center_url:
                    # 兼容旧格式
                    base_url = task_center_url.split('/api/namespaces/')[0]
                    url = f"{base_url}/api/namespaces/{namespace_name}"
                elif task_center_url.endswith('/api/v1') or task_center_url.endswith('/api/v1/'):
                    # 多命名空间模式，URL 是 http://localhost:8001/api/v1
                    url = f"{task_center_url.rstrip('/')}/namespaces/{namespace_name}"
                else:
                    # 基础URL，添加完整路径
                    url = f"{task_center_url.rstrip('/')}/api/v1/namespaces/{namespace_name}"

                # 创建任务中心连接
                tc = TaskCenter(url)
                if not tc._connect_sync():
                    raise Exception(f"无法连接到任务中心: {url}")
                
                # 创建 Jettask 应用
                app = Jettask(task_center=tc)
                
                # 创建调度器管理器 - ScheduledTaskManager 只接受一个参数
                manager = ScheduledTaskManager(app)
                
                # 创建并启动调度器 - 使用正确的参数名
                scheduler = TaskScheduler(
                    app=app,
                    db_manager=manager,
                    scan_interval=scan_interval,
                    batch_size=batch_size
                )
                
                logger.info(f"命名空间 {namespace_name} 的调度器已启动")
                await scheduler.run()
                
            except Exception as e:
                logger.error(f"命名空间 {namespace_name} 的调度器启动失败: {e}")
                raise
        
        try:
            loop.run_until_complete(run_scheduler())
        except KeyboardInterrupt:
            logger.info(f"命名空间 {namespace_name} 的调度器进程收到中断信号")
        finally:
            loop.close()
    
    async def _health_check_loop(self):
        """健康检查循环"""
        while self.running:
            try:
                await asyncio.sleep(30)  # 每30秒检查一次
                
                # 检查所有调度器进程的健康状态
                for namespace_name, process in list(self.scheduler_processes.items()):
                    if not process.is_alive():
                        logger.warning(f"命名空间 {namespace_name} 的调度器进程已停止，尝试重启")
                        self._start_scheduler_process(namespace_name)
                        
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
                    self._start_scheduler_process(name)
                    self.known_namespaces.add(name)
                
                # 检测删除的命名空间
                removed_names = self.known_namespaces - current_names
                for name in removed_names:
                    logger.info(f"检测到命名空间已删除: {name}")
                    if name in self.scheduler_processes:
                        process = self.scheduler_processes[name]
                        process.terminate()
                        process.join(timeout=5)
                        del self.scheduler_processes[name]
                    self.known_namespaces.discard(name)
                    
            except Exception as e:
                logger.error(f"命名空间检测错误: {e}")
    
    async def cleanup(self):
        """清理资源"""
        if self.scheduler_instance:
            # 单命名空间模式
            logger.info("停止调度器")
            self.scheduler_instance.stop()  # stop()不是异步方法
        
        # 多命名空间模式
        logger.info("停止所有调度器进程")
        for namespace_name, process in self.scheduler_processes.items():
            try:
                process.terminate()
                process.join(timeout=5)
                if process.is_alive():
                    process.kill()
                    process.join()
                logger.info(f"停止命名空间 {namespace_name} 的调度器进程")
            except Exception as e:
                logger.error(f"停止命名空间 {namespace_name} 的调度器进程失败: {e}")
        
        self.scheduler_processes.clear()