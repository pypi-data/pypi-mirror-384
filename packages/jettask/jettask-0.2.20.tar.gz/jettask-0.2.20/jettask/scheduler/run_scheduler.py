#!/usr/bin/env python
"""
定时任务调度器启动脚本
"""
import asyncio
import os
import sys
import signal
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from jettask import Jettask
from jettask.scheduler.scheduler import TaskScheduler
from jettask.scheduler.task_crud import ScheduledTaskManager
from jettask.utils.task_logger import get_task_logger

logger = get_task_logger(__name__)


class SchedulerRunner:
    """调度器运行器"""
    
    def __init__(self):
        self.scheduler = None
        self.app = None
        self.running = False
    
    async def setup(self):
        """初始化设置"""
        # 从环境变量获取配置
        redis_url = os.getenv('JETTASK_REDIS_URL', 'redis://localhost:6379/0')
        db_url = os.getenv('JETTASK_PG_URL', 'postgresql://jettask:123456@localhost:5432/jettask')
        
        # 创建Jettask应用实例
        self.app = Jettask(
            redis_url=redis_url,
            pg_url=db_url
        )
        
        # 导入任务模块（确保任务被注册）
        try:
            # 尝试导入用户定义的任务模块
            import importlib
            import importlib.util
            
            # 先尝试加载示例模块
            example_paths = [
                'examples.scheduler_auto_demo',
                'scheduler_auto_demo'
            ]
            
            for path in example_paths:
                try:
                    example_module = importlib.import_module(path)
                    if hasattr(example_module, 'app'):
                        # 将任务模块中的任务复制到调度器的app中
                        for task_name, task_obj in example_module.app._tasks.items():
                            self.app._tasks[task_name] = task_obj
                            # 也注册带模块名的任务
                            full_name = f"scheduler_auto_demo.{task_name}"
                            self.app._tasks[full_name] = task_obj
                            logger.info(f"Registered task: {task_name} and {full_name}")
                        logger.info(f"Loaded example tasks from module: {path}")
                        break
                except ImportError:
                    continue
            
            # 然后加载用户指定的任务模块
            task_module = os.getenv('JETTASK_TASKS_MODULE', 'tasks')
            if task_module:
                try:
                    module = importlib.import_module(task_module)
                    # 获取模块中的app对象的任务
                    if hasattr(module, 'app'):
                        # 将任务模块中的任务复制到调度器的app中
                        for task_name, task_obj in module.app._tasks.items():
                            self.app._tasks[task_name] = task_obj
                            logger.info(f"Registered task: {task_name}")
                    
                    # 注册别名任务（scheduler_auto_demo.send_notification）
                    if hasattr(module, 'send_notification'):
                        self.app._tasks['scheduler_auto_demo.send_notification'] = module.send_notification
                        logger.info("Registered task: scheduler_auto_demo.send_notification")
                    
                    logger.info(f"Loaded tasks from module: {task_module}")
                except ImportError as e:
                    logger.warning(f"Could not import tasks module '{task_module}': {e}")
        except Exception as e:
            logger.warning(f"Error loading tasks: {e}")
        
        # 创建数据库管理器
        db_manager = ScheduledTaskManager(db_url)
        await db_manager.connect()
        
        # 确保数据库表存在
        await db_manager.init_schema()
        
        # 创建调度器
        self.scheduler = TaskScheduler(
            app=self.app,
            redis_url=redis_url,
            db_manager=db_manager,
            redis_prefix="jettask:scheduled",
            scan_interval=0.5,  # 每0.5秒扫描一次
            batch_size=100,      # 每批处理100个任务
            leader_ttl=30        # Leader锁30秒过期
        )
        
        await self.scheduler.connect()
        logger.info("Scheduler setup completed")
    
    async def run(self):
        """运行调度器"""
        self.running = True
        logger.info("Starting scheduler...")
        
        try:
            # 运行调度器
            await self.scheduler.run()
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
        finally:
            self.running = False
            logger.info("Scheduler stopped")
    
    async def shutdown(self):
        """关闭调度器"""
        logger.info("Shutting down scheduler...")
        
        if self.scheduler:
            self.scheduler.stop()
            await self.scheduler.disconnect()
        
        if self.app:
            # 关闭应用连接
            pass
        
        logger.info("Scheduler shutdown completed")
    
    def handle_signal(self, signum, frame):
        """处理终止信号"""
        logger.info(f"Received signal {signum}, initiating shutdown...")
        self.running = False
        
        # 创建关闭任务
        if self.scheduler:
            self.scheduler.stop()


async def main():
    """主函数"""
    runner = SchedulerRunner()
    
    # 设置信号处理
    signal.signal(signal.SIGINT, runner.handle_signal)
    signal.signal(signal.SIGTERM, runner.handle_signal)
    
    try:
        # 初始化
        await runner.setup()
        
        # 运行调度器
        await runner.run()
        
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        # 清理
        await runner.shutdown()


if __name__ == '__main__':
    # 设置日志级别
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # 运行主函数
    asyncio.run(main())