"""
多进程执行器的子进程入口

职责：
1. 清理继承的父进程状态
2. 初始化子进程环境
3. 启动任务执行器
"""
import os
import gc
import sys
import signal
import asyncio
import logging
import multiprocessing
from typing import List, Dict
import time 




    
import redis 
async def execute_single_command(client: redis.Redis, index: int):
    """
    执行单条 Redis 命令

    Args:
        client: Redis 客户端
        index: 命令索引
    """
    await client.set(f"test_key_{index}", f"value_{index}")


async def execute_commands(client: redis.Redis, num_commands: int = 10000, concurrency: int = 100):
    """
    并发执行大量 Redis 命令

    Args:
        client: Redis 客户端
        num_commands: 命令数量
        concurrency: 并发数（同时执行的任务数）
    """
    logger.info(f"开始并发执行 {num_commands} 条 Redis 命令（并发数: {concurrency}）...")

    start_time = time.time()

    # 创建信号量控制并发数
    semaphore = asyncio.Semaphore(concurrency)

    async def execute_with_semaphore(index: int):
        """使用信号量控制并发"""
        # async with semaphore:
        await execute_single_command(client, index)

        # 每 1000 条命令打印一次进度
        if (index + 1) % 1000 == 0:
            logger.info(f"已完成 {index + 1} 条命令")

    # 创建所有任务
    tasks = [
        asyncio.create_task(execute_with_semaphore(i))
        for i in range(num_commands)
    ]

    # 等待所有任务完成
    await asyncio.gather(*tasks)

    elapsed = time.time() - start_time
    logger.info(f"✅ 完成 {num_commands} 条命令，耗时: {elapsed:.2f}s，QPS: {num_commands/elapsed:.0f}")
    await asyncio.sleep(999999999999999999)
    return elapsed


# 不要在模块级别创建 logger，避免在 fork 时触发 logging 全局锁竞争
# logger 将在 subprocess_main 中创建
logger = None


def _reset_locks_after_fork():
    """
    在 fork 后立即重置所有 logging 相关的锁

    关键：不能调用任何 logging API（如 getLogger），因为这些 API 本身需要获取锁。
    必须直接访问 logging 模块的内部数据结构。
    """
    import threading
    import logging

    # 1. 暴力替换 logging 模块的全局锁（不通过 API）
    logging._lock = threading.RLock()

    # 2. 直接访问 Logger.manager 的内部字典，不调用 getLogger()
    # 这样避免触发锁的获取
    if hasattr(logging.Logger, 'manager'):
        manager = logging.Logger.manager

        # 2.1 重置 manager 的锁
        if hasattr(manager, 'lock'):
            manager.lock = threading.RLock()

        # 2.2 重置根 logger 的锁（直接访问 root 属性）
        if hasattr(manager, 'root'):
            root = manager.root
            if hasattr(root, '_lock'):
                root._lock = threading.RLock()

            # 重置根 logger 的所有 handlers 的锁
            if hasattr(root, 'handlers'):
                for handler in list(root.handlers):
                    if hasattr(handler, 'lock'):
                        handler.lock = threading.RLock()

        # 2.3 重置所有子 logger 的锁（直接访问字典，不调用 getLogger）
        if hasattr(manager, 'loggerDict'):
            for logger_obj in list(manager.loggerDict.values()):
                # loggerDict 中的值可能是 PlaceHolder 或 Logger
                if hasattr(logger_obj, '_lock'):
                    logger_obj._lock = threading.RLock()

                # 重置 handlers 的锁
                if hasattr(logger_obj, 'handlers'):
                    for handler in list(logger_obj.handlers):
                        if hasattr(handler, 'lock'):
                            handler.lock = threading.RLock()



class SubprocessInitializer:
    """子进程初始化器 - 负责清理和准备环境"""

    @staticmethod
    def cleanup_inherited_state():
        """
        清理从父进程继承的状态（fork模式）

        在 fork 模式下，子进程继承父进程的内存状态，包括：
        - Redis连接池和客户端
        - 事件循环对象
        - 线程对象和锁
        - 信号处理器

        我们需要正确清理这些资源，避免：
        - 子进程复用父进程的连接（会导致数据混乱）
        - 访问父进程的任务/线程（会导致死锁）
        - 信号处理器冲突
        """
        # 1. 重置信号处理器
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        signal.signal(signal.SIGTERM, signal.SIG_DFL)

        # 2. 重置事件循环策略
        # 不要尝试访问或关闭旧循环，直接设置新的策略
        # 这样子进程在首次使用asyncio时会创建全新的循环
        try:
            asyncio.set_event_loop_policy(None)
            asyncio.set_event_loop(None)
        except Exception:
            pass

        # 3. 清空Redis连接池和客户端缓存
        # 这非常重要！防止子进程复用父进程的连接
        from jettask.utils.db_connector import clear_all_cache
        clear_all_cache()

        # 4. 强制垃圾回收
        gc.collect()

    @staticmethod
    def setup_logging(process_id: int, redis_prefix: str):
        """配置子进程日志

        注意：在 fork 模式下，子进程会继承父进程的 logging handlers。
        这些 handlers 可能持有父进程的锁或文件描述符，导致死锁。
        因此需要先清除所有继承的 handlers，再手动创建全新的 handler。
        """
        # 0. 重置 logging 模块的全局锁（关键！）
        # 在 fork 后，logging 模块的全局锁可能处于被父进程持有的状态
        # 需要手动重新创建这些锁，避免死锁
        import threading
        logging._lock = threading.RLock()

        # 1. 清除根 logger 的所有 handlers
        root_logger = logging.getLogger()

        # 重置根logger的锁
        if hasattr(root_logger, '_lock'):
            root_logger._lock = threading.RLock()

        for handler in root_logger.handlers[:]:
            try:
                # 重置handler的锁
                if hasattr(handler, 'lock'):
                    handler.lock = threading.RLock()
                handler.close()
            except:
                pass
            root_logger.removeHandler(handler)

        # 2. 清除所有已存在的 logger 的 handlers，并重置 propagate
        for logger_name in list(logging.Logger.manager.loggerDict.keys()):
            logger_obj = logging.getLogger(logger_name)

            # 重置logger的锁
            if hasattr(logger_obj, '_lock'):
                logger_obj._lock = threading.RLock()

            if hasattr(logger_obj, 'handlers'):
                for handler in logger_obj.handlers[:]:
                    try:
                        # 重置handler的锁
                        if hasattr(handler, 'lock'):
                            handler.lock = threading.RLock()
                        handler.close()
                    except:
                        pass
                    logger_obj.removeHandler(handler)

                # 确保所有子 logger 的日志都能传播到根 logger
                logger_obj.propagate = True

        # 3. 手动创建全新的 handler
        # 不使用 logging.basicConfig()，因为它可能会复用某些全局状态
        # 而是手动创建一个全新的 StreamHandler
        formatter = logging.Formatter(
            fmt=f"%(asctime)s - %(levelname)s - [{redis_prefix}-P{process_id}] - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        handler = logging.StreamHandler(sys.stderr)
        handler.setFormatter(formatter)
        handler.setLevel(logging.INFO)
        # 确保新handler有正确的锁
        handler.createLock()

        root_logger.setLevel(logging.INFO)
        root_logger.addHandler(handler)

    @staticmethod
    def create_event_loop() -> asyncio.AbstractEventLoop:
        """创建全新的事件循环"""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop


class MinimalApp:
    """
    最小化的 App 接口

    为子进程提供必要的接口，而不需要完整的 App 实例
    """
    def __init__(
        self,
        redis_client,
        async_redis_client,
        redis_url: str,
        redis_prefix: str,
        tasks: Dict,
        worker_id: str,
        worker_key: str
    ):
        self.redis = redis_client
        self.async_redis = async_redis_client
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix
        self._tasks = tasks
        self.worker_id = worker_id
        self.worker_key = worker_key
        self._should_exit = False

        # ExecutorCore 需要的属性
        self._status_prefix = f"{redis_prefix}:STATUS:"
        self._result_prefix = f"{redis_prefix}:RESULT:"

        # EventPool 需要的属性
        self._tasks_by_queue = {}
        for task_name, task in tasks.items():
            task_queue = task.queue or redis_prefix
            if task_queue not in self._tasks_by_queue:
                self._tasks_by_queue[task_queue] = []
            self._tasks_by_queue[task_queue].append(task_name)

        # 这些属性会在初始化时设置
        self.ep = None
        self.consumer_manager = None
        self.worker_state_manager = None
        self.worker_state = None  # EventPool 的恢复机制需要这个属性

    def get_task_by_name(self, task_name: str):
        """根据任务名称获取任务对象"""
        return self._tasks.get(task_name)

    def cleanup(self):
        """清理资源"""
        pass


class SubprocessRunner:
    """子进程运行器 - 负责实际执行任务"""

    def __init__(
        self,
        process_id: int,
        redis_url: str,
        redis_prefix: str,
        queues: List[str],
        tasks: Dict,
        concurrency: int,
        prefetch_multiplier: int,
        max_connections: int,
        consumer_strategy: str,
        consumer_config: Dict,
        worker_id: str,
        worker_key: str
    ):
        self.process_id = process_id
        self.redis_url = redis_url
        self.redis_prefix = redis_prefix
        self.queues = queues
        self.tasks = tasks
        self.concurrency = concurrency
        self.prefetch_multiplier = prefetch_multiplier
        self.max_connections = max_connections
        self.consumer_strategy = consumer_strategy
        self.consumer_config = consumer_config or {}
        self.worker_id = worker_id
        self.worker_key = worker_key

        # 子进程内部状态
        self.redis_client = None
        self.async_redis_client = None
        self.minimal_app = None
        self.event_pool = None
        self.executors = []
        self._should_exit = False

    def setup_signal_handlers(self):
        """设置信号处理器"""
        def signal_handler(signum, _frame):
            logger.info(f"Process #{self.process_id} received signal {signum}")
            self._should_exit = True
            if self.minimal_app:
                self.minimal_app._should_exit = True
            if self.event_pool:
                self.event_pool._stop_reading = True

        # signal.signal(signal.SIGINT, signal_handler)
        # signal.signal(signal.SIGTERM, signal_handler)

    def create_redis_connections(self):
        """创建独立的Redis连接（使用全局客户端实例）"""
        from jettask.utils.db_connector import get_sync_redis_client, get_async_redis_client

        # logger.info(f"Process #{self.process_id}: Creating Redis connections")

        # 同步连接（使用全局客户端实例）
        self.redis_client = get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

        # 异步连接（使用全局客户端实例）
        self.async_redis_client = get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

    async def initialize_components(self):
        """初始化执行器组件"""
        from jettask.messaging.event_pool import EventPool
        from jettask.executor.task_executor import TaskExecutor

        logger.info(f"Process #{self.process_id}: Initializing components")

        # 创建 MinimalApp
        self.minimal_app = MinimalApp(
            redis_client=self.redis_client,
            async_redis_client=self.async_redis_client,
            redis_url=self.redis_url,
            redis_prefix=self.redis_prefix,
            tasks=self.tasks,
            worker_id=self.worker_id,
            worker_key=self.worker_key
        )

        # 创建 EventPool
        consumer_config = self.consumer_config.copy()
        consumer_config['redis_prefix'] = self.redis_prefix
        consumer_config['disable_heartbeat_process'] = True

        self.event_pool = EventPool(
            self.redis_client,
            self.async_redis_client,
            redis_url=self.redis_url,
            consumer_strategy=self.consumer_strategy,
            consumer_config=consumer_config,
            redis_prefix=self.redis_prefix,
            app=self.minimal_app
        )
        
  
        # logger.info('准备进入测试流程')
        # await execute_commands(self.event_pool.async_redis_client, num_commands=100000)

        # 将 EventPool 设置到 MinimalApp
        self.minimal_app.ep = self.event_pool
        self.minimal_app.consumer_manager = self.event_pool.consumer_manager

        # 初始化 WorkerState
        from jettask.worker.manager import WorkerState
        self.minimal_app.worker_state = WorkerState(
            redis_client=self.redis_client,
            async_redis_client=self.async_redis_client,
            redis_prefix=self.redis_prefix
        )

        # 初始化路由
        self.event_pool.queues = self.queues
        self.event_pool.init_routing()

        # 收集任务（按队列分组）
        tasks_by_queue = {}
        for task_name, task in self.tasks.items():
            task_queue = task.queue or self.redis_prefix
            if task_queue in self.queues:
                if task_queue not in tasks_by_queue:
                    tasks_by_queue[task_queue] = []
                tasks_by_queue[task_queue].append(task_name)

        # 收集所有需要监听的任务
        all_tasks = set()
        for queue in self.queues:
            task_names = tasks_by_queue.get(queue, [])
            all_tasks.update(task_names)

        # 为每个任务创建独立的 asyncio.Queue
        task_event_queues = {task_name: asyncio.Queue() for task_name in all_tasks}
        logger.info(f"Process #{self.process_id}: Created event queues for tasks: {list(task_event_queues.keys())}")

        # 启动异步事件监听
        listening_task = asyncio.create_task(
            self.event_pool.listening_event(task_event_queues, self.prefetch_multiplier)
        )

        # 为每个任务创建独立的 TaskExecutor
        for task_name, task_queue in task_event_queues.items():
            executor = TaskExecutor(
                event_queue=task_queue,
                app=self.minimal_app,
                task_name=task_name,
                concurrency=self.concurrency
            )

            # 初始化执行器
            await executor.initialize()

            # 启动执行器
            executor_task = asyncio.create_task(executor.run())
            self.executors.append((task_name, executor_task))
            logger.info(f"Process #{self.process_id}: Started TaskExecutor for task '{task_name}'")

        # 返回所有任务
        return listening_task, [t for _, t in self.executors]

    async def run(self):
        """运行执行器主循环"""
        logger.info(f"Process #{self.process_id} starting (PID: {os.getpid()})")

        listening_task = None
        executor_tasks = []

        try:
            listening_task, executor_tasks = await self.initialize_components()

            # 等待所有任务完成
            await asyncio.gather(listening_task, *executor_tasks)

        except asyncio.CancelledError:
            logger.info(f"Process #{self.process_id} cancelled")
        except Exception as e:
            logger.error(f"Process #{self.process_id} error: {e}", exc_info=True)
        finally:
            # 清理
            logger.info(f"Process #{self.process_id} cleaning up")

            if listening_task and not listening_task.done():
                listening_task.cancel()

            for _task_name, task in self.executors:
                if not task.done():
                    task.cancel()

            # 等待取消完成
            try:
                all_tasks = [listening_task] + executor_tasks if listening_task else executor_tasks
                await asyncio.wait_for(
                    asyncio.gather(*all_tasks, return_exceptions=True),
                    timeout=0.5
                )
            except asyncio.TimeoutError:
                pass

            # 清理 EventPool
            if self.event_pool and hasattr(self.event_pool, 'cleanup'):
                try:
                    self.event_pool.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up EventPool: {e}")

            # 清理 ConsumerManager
            if self.minimal_app and self.minimal_app.consumer_manager:
                try:
                    self.minimal_app.consumer_manager.cleanup()
                except Exception as e:
                    logger.error(f"Error cleaning up ConsumerManager: {e}")

            # 关闭 WorkerStateManager
            if self.minimal_app and self.minimal_app.worker_state_manager:
                try:
                    await self.minimal_app.worker_state_manager.stop_listener()
                except Exception as e:
                    logger.error(f"Error stopping WorkerStateManager: {e}")

            # 关闭 Redis 连接
            if self.async_redis_client:
                try:
                    await self.async_redis_client.aclose()
                except Exception as e:
                    logger.error(f"Error closing async Redis client: {e}")

            logger.info(f"Process #{self.process_id} stopped")


def subprocess_main(
    process_id: int,
    redis_url: str,
    redis_prefix: str,
    queues: List[str],
    tasks: Dict,
    concurrency: int,
    prefetch_multiplier: int,
    max_connections: int,
    consumer_strategy: str,
    consumer_config: Dict,
    worker_id: str,
    worker_key: str,
    shutdown_event
):
    """
    子进程主函数 - 这是子进程的真正入口点

    职责：
    1. 调用初始化器清理环境
    2. 创建运行器并执行
    3. 确保资源正确清理
    """
    
    try:
        # 设置进程名
        # multiprocessing.current_process().name = f"JetTask-Worker-{process_id}"
        print(f"Starting subprocess #{process_id} with PID {os.getpid()}", flush=True)
        # ========== 阶段1：清理和初始化 ==========
        initializer = SubprocessInitializer()
        initializer.cleanup_inherited_state()
        print(f"Process #{process_id} cleaned up inherited state")
        initializer.setup_logging(process_id, redis_prefix)

        # 在清理和配置logging后，创建一个新的logger实例
        global logger
        print("Creating new logger instance in subprocess")
        logger = logging.getLogger()
        logger.info(f"Process #{process_id} starting in PID {os.getpid()}")
        print(f"Process #{process_id} setting up logging")
        # ========== 阶段2：创建运行器 ==========
        runner = SubprocessRunner(
            process_id=process_id,
            redis_url=redis_url,
            redis_prefix=redis_prefix,
            queues=queues,
            tasks=tasks,
            concurrency=concurrency,
            prefetch_multiplier=prefetch_multiplier,
            max_connections=max_connections,
            consumer_strategy=consumer_strategy,
            consumer_config=consumer_config,
            worker_id=worker_id,
            worker_key=worker_key
        )
        print(f"Process #{process_id} created SubprocessRunner")
        # 设置信号处理
        runner.setup_signal_handlers()
        print(f"Process #{process_id} set up signal handlers")
        # 创建 Redis 连接
        runner.create_redis_connections()
        print(f"Process #{process_id} created Redis connections")
        # ========== 阶段3：运行 ==========
        loop = initializer.create_event_loop()

        try:
            if not shutdown_event.is_set():
                loop.run_until_complete(runner.run())
        except KeyboardInterrupt:
            logger.info(f"Process #{process_id} received interrupt")
        except Exception as e:
            logger.error(f"Process #{process_id} fatal error: {e}", exc_info=True)
        finally:
            # 清理并发锁
            try:
                if worker_id:
                    from jettask.utils.rate_limit.concurrency_limiter import ConcurrencyRateLimiter
                    task_names = list(tasks.keys()) if tasks else []
                    ConcurrencyRateLimiter.cleanup_worker_locks(
                        redis_url=redis_url,
                        redis_prefix=redis_prefix,
                        worker_id=worker_id,
                        task_names=task_names
                    )
            except Exception as e:
                logger.error(f"Error during lock cleanup: {e}")

            # 关闭事件循环
            try:
                loop.close()
            except:
                pass

            logger.info(f"Process #{process_id} exited")
            sys.exit(0)
    except Exception as e:
        import traceback 
        traceback.print_exc()
        print(f"Subprocess #{process_id} fatal error during initialization: {e}", file=sys.stderr)
        sys.exit(1)

__all__ = ['subprocess_main']
