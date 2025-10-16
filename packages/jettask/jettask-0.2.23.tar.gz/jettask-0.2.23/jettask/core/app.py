import os

import time
from datetime import datetime
from ..utils.serializer import dumps, loads, dumps_str, loads_str
import signal

import asyncio
import logging
import contextlib
import importlib
import time 

from typing import List


import redis
from redis import asyncio as aioredis

# 导入TaskMessage
from .message import TaskMessage
from .task import Task
from .enums import TaskStatus
from jettask.messaging.event_pool import EventPool
from ..executor.orchestrator import ProcessOrchestrator
from ..utils import gen_task_name
from ..exceptions import TaskTimeoutError, TaskExecutionError, TaskNotFoundError
# 导入统一的数据库连接管理
from ..utils.db_connector import get_sync_redis_client, get_async_redis_client
# 导入Lua脚本
from ..config.lua_scripts import (
    LUA_SCRIPT_DELAYED_TASKS,
    LUA_SCRIPT_NORMAL_TASKS,
    LUA_SCRIPT_SEND_DELAYED_TASKS
)
import uvloop

logger = logging.getLogger('app')

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

UVLOOP_AVAILABLE = True
# 自动启用uvloop
asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logger.debug("Using uvloop for better performance")


class Jettask(object):
    # Lua脚本从config模块导入，统一管理
    _LUA_SCRIPT_DELAYED_TASKS = LUA_SCRIPT_DELAYED_TASKS
    _LUA_SCRIPT_NORMAL_TASKS = LUA_SCRIPT_NORMAL_TASKS

    def __init__(self, redis_url: str = None, include: list = None, max_connections: int = None,
                 consumer_strategy: str = None, consumer_config: dict = None, tasks=None,
                 redis_prefix: str = None, scheduler_config: dict = None, pg_url: str = None,
                 task_center=None, worker_id: str = None, worker_key: str = None) -> None:
        self._tasks = tasks or {}
        self._queue_tasks = {}  # 记录每个队列对应的任务列表
        self.asyncio = False
        self.include = include or []

        # 任务中心相关属性
        self.task_center = None  # 将通过mount_task_center方法挂载或初始化时指定
        self._task_center_config = None
        self._original_redis_url = redis_url
        self._original_pg_url = pg_url

        # 优先使用传入参数，其次使用环境变量
        self.redis_url = redis_url or os.environ.get('JETTASK_REDIS_URL')
        self.pg_url = pg_url or os.environ.get('JETTASK_PG_URL')
        self.max_connections = max_connections if max_connections is not None else int(os.environ.get('JETTASK_MAX_CONNECTIONS', '500'))
        self.redis_prefix = redis_prefix or os.environ.get('JETTASK_REDIS_PREFIX', 'jettask')

        # 检查必需参数：redis_url
        if not self.redis_url:
            raise ValueError(
                "必须提供 redis_url 参数！\n\n"
                "请通过以下任一方式配置:\n"
                "  1. 初始化时传参:\n"
                "     app = Jettask(redis_url='redis://localhost:6379/0')\n\n"
                "  2. 设置环境变量:\n"
                "     export JETTASK_REDIS_URL='redis://localhost:6379/0'\n\n"
                "  3. 在 .env 文件中配置:\n"
                "     JETTASK_REDIS_URL=redis://localhost:6379/0\n"
            )

        self.consumer_strategy = consumer_strategy
        self.consumer_config = consumer_config or {}
        self.scheduler_config = scheduler_config or {}

        # 如果初始化时提供了task_center，直接挂载
        if task_center:
            self.mount_task_center(task_center)

        # Update prefixes with the configured prefix using colon namespace
        self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
        self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
        
        # 预编译常用操作，减少运行时开销
        self._loads = loads
        self._dumps = dumps
        
        # 调度器相关
        self.scheduler = None
        self.scheduler_manager = None

        self._status_prefix = self.STATUS_PREFIX
        self._result_prefix = self.RESULT_PREFIX

        # Worker 状态管理器（延迟初始化）
        self.worker_state_manager = None

        # Worker 状态查询器（延迟初始化 - 需要 Redis 客户端）
        self._worker_state = None

        # Worker ID（可选，用于子进程复用主进程的 ID）
        self.worker_id = worker_id
        self.worker_key = worker_key

        # 初始化清理状态，但不注册处理器
        self._cleanup_done = False
        self._should_exit = False
        self._worker_started = False
        self._handlers_registered = False

        # 初始化队列注册表（用于获取任务名称等操作）
        from ..messaging.registry import QueueRegistry
        self.registry = QueueRegistry(
            redis_client=None,  # 延迟初始化，第一次使用时通过 self.redis 获取
            async_redis_client=None,
            redis_prefix=self.redis_prefix
        )
   
    
    def _load_config_from_task_center(self):
        """从任务中心加载配置"""
        try:
            import asyncio
            # 检查是否已经在事件循环中
            try:
                loop = asyncio.get_running_loop()
                # 已在事件循环中，无法同步加载
                return False
            except RuntimeError:
                # 不在事件循环中，可以创建新的
                loop = asyncio.new_event_loop()
                if self.task_center:
                    # 如果已经初始化，直接获取配置
                    if self.task_center._initialized:
                        config = self.task_center._config
                    else:
                        # 使用异步模式连接
                        success = loop.run_until_complete(self.task_center.connect(asyncio=True))
                        if success:
                            config = self.task_center._config
                        else:
                            config = None
                else:
                    config = None
                loop.close()
            
            if config:
                # 任务中心配置优先级高于手动配置
                redis_config = config.get('redis_config', {})
                pg_config = config.get('pg_config', {})
                # 构建Redis URL
                if redis_config:
                    redis_host = redis_config.get('host', 'localhost')
                    redis_port = redis_config.get('port', 6379)
                    redis_password = redis_config.get('password')
                    redis_db = redis_config.get('db', 0)
                    
                    if redis_password:
                        self.redis_url = f"redis://:{redis_password}@{redis_host}:{redis_port}/{redis_db}"
                    else:
                        self.redis_url = f"redis://{redis_host}:{redis_port}/{redis_db}"
                    
                    logger.debug(f"从任务中心加载Redis配置: {redis_host}:{redis_port}/{redis_db}")
                
                # 构建PostgreSQL URL
                if pg_config:
                    pg_host = pg_config.get('host', 'localhost')
                    pg_port = pg_config.get('port', 5432)
                    pg_user = pg_config.get('user', 'postgres')
                    pg_password = pg_config.get('password', '')
                    pg_database = pg_config.get('database', 'jettask')
                    
                    self.pg_url = f"postgresql://{pg_user}:{pg_password}@{pg_host}:{pg_port}/{pg_database}"
                    logger.debug(f"从任务中心加载PostgreSQL配置: {pg_host}:{pg_port}/{pg_database}")
                
                # 保存配置供后续使用
                self._task_center_config = config
                
                # 更新Redis前缀为命名空间名称
                if self.task_center and self.task_center.redis_prefix != "jettask":
                    self.redis_prefix = self.task_center.redis_prefix
                    # 更新相关前缀
                    self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
                    self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
                
                # 清理已缓存的Redis连接，强制重新创建
                if hasattr(self, '_redis'):
                    delattr(self, '_redis')
                if hasattr(self, '_async_redis'):
                    delattr(self, '_async_redis')
                if hasattr(self, '_ep'):
                    delattr(self, '_ep')
                
        except Exception as e:
            import traceback
            traceback.print_exc()
            logger.warning(f"从任务中心加载配置失败，使用手动配置: {e}")
            # 恢复原始配置
            self.redis_url = self._original_redis_url
            self.pg_url = self._original_pg_url
    
    def mount_task_center(self, task_center):
        """
        挂载任务中心到Jettask应用
        
        如果task_center已经连接，会自动应用配置到当前app。
        
        Args:
            task_center: TaskCenter实例
            
        使用示例：
            from jettask.task.task_center.client import TaskCenter
            
            # 创建任务中心客户端（可复用）
            task_center = TaskCenter("http://localhost:8001/api/namespaces/demo")
            await task_center.connect()  # 只需连接一次
            
            # 创建多个app实例，共享同一个task_center
            app1 = Jettask()
            app1.mount_task_center(task_center)  # 自动应用配置
            
            app2 = Jettask()
            app2.mount_task_center(task_center)  # 复用配置
        """
        self.task_center = task_center
        
        # 如果任务中心已连接，立即应用所有配置
        if task_center and task_center._initialized:
            # 应用Redis配置
            if task_center.redis_config:
                redis_url = task_center.get_redis_url()
                if redis_url:
                    self.redis_url = redis_url
                    
            # 应用PostgreSQL配置
            if task_center.pg_config:
                pg_url = task_center.get_pg_url()
                if pg_url:
                    self.pg_url = pg_url
            
            # 更新Redis前缀
            self.redis_prefix = task_center.redis_prefix
            # 更新相关前缀
            self.STATUS_PREFIX = f"{self.redis_prefix}:STATUS:"
            self.RESULT_PREFIX = f"{self.redis_prefix}:RESULT:"
            self.QUEUE_PREFIX = f"{self.redis_prefix}:QUEUE:"
            self.DELAYED_QUEUE_PREFIX = f"{self.redis_prefix}:DELAYED_QUEUE:"
            self.STREAM_PREFIX = f"{self.redis_prefix}:STREAM:"
            self.TASK_PREFIX = f"{self.redis_prefix}:TASK:"
            self.SCHEDULER_PREFIX = f"{self.redis_prefix}:SCHEDULED:"
            self.LOCK_PREFIX = f"{self.redis_prefix}:LOCK:"
            
            # 标记配置已加载
            self._task_center_config = {
                'redis_config': task_center.redis_config,
                'pg_config': task_center.pg_config,
                'namespace_name': task_center.namespace_name,
                'version': task_center.version
            }
    
    
    def _setup_cleanup_handlers(self):
        """设置清理处理器"""
        # 避免重复注册
        if self._handlers_registered:
            return
        
        self._handlers_registered = True
        
        def signal_cleanup_handler(signum=None, frame=None):
            """信号处理器"""
            if self._cleanup_done:
                return
            # 只有启动过worker才需要打印清理信息
            if self._worker_started:
                logger.debug("Received shutdown signal, cleaning up...")
            self.cleanup()
            if signum:
                # 设置标记表示需要退出
                self._should_exit = True
                # 对于多进程环境，不直接操作事件循环
                # 让执行器自己检测退出标志并优雅关闭
        
        def atexit_cleanup_handler():
            """atexit处理器"""
            if self._cleanup_done:
                return
            # atexit时不重复打印日志，静默清理
            self.cleanup()
        
        # 注册信号处理器
        if hasattr(signal, 'SIGTERM'):
            signal.signal(signal.SIGTERM, signal_cleanup_handler)
        if hasattr(signal, 'SIGINT'):
            signal.signal(signal.SIGINT, signal_cleanup_handler)
        
        # 注册atexit处理器
        import atexit
        atexit.register(atexit_cleanup_handler)
    
    def cleanup(self):
        """清理应用资源"""
        if self._cleanup_done:
            return
        self._cleanup_done = True
        
        # 只有真正启动过worker才打印日志
        if self._worker_started:
   
            
            # 清理EventPool
            if hasattr(self, 'ep') and self.ep:
                self.ep.cleanup()
            

        else:
            # 如果只是实例化但没有启动，静默清理
            if hasattr(self, 'ep') and self.ep:
                self.ep.cleanup()

    
    @property
    def consumer_manager(self):
        """获取消费者管理器"""
        return self.ep.consumer_manager if hasattr(self.ep, 'consumer_manager') else None

    @property
    def async_redis(self):
        """获取异步Redis客户端（全局单例）"""
        # 如果配置了任务中心且还未加载配置，先加载配置
        if self.task_center and self.task_center.is_enabled and not self._task_center_config:
            self._load_config_from_task_center()

        # 使用超长超时时间，支持 Pub/Sub 长连接（可能几天没有消息）
        return get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections,
            socket_timeout=99999999999  # 超长超时，几乎永不超时
        )

    @property
    def redis(self):
        """获取同步Redis客户端（全局单例）"""
        # 如果配置了任务中心且还未加载配置，先加载配置
        # if self.task_center and self.task_center.is_enabled and not self._task_center_config:
        #     self._load_config_from_task_center()

        return get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=True,
            max_connections=self.max_connections
        )

    @property
    def binary_redis(self):
        """获取同步二进制Redis客户端（不自动解码，用于获取msgpack数据）"""
        return get_sync_redis_client(
            redis_url=self.redis_url,
            decode_responses=False,
            max_connections=self.max_connections
        )

    @property
    def async_binary_redis(self):
        """获取异步二进制Redis客户端（不自动解码，用于获取msgpack数据）"""
        return get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=False,
            max_connections=self.max_connections,
            socket_timeout=99999999999
        )

    @property
    def worker_state(self):
        """
        获取 WorkerState 实例（单例，延迟初始化）

        WorkerState 负责 Worker 状态的查询和管理
        """
        if self._worker_state is None:
            from jettask.worker.manager import WorkerState
            self._worker_state = WorkerState(
                redis_client=self.redis,
                async_redis_client=self.async_redis,
                redis_prefix=self.redis_prefix
            )
            logger.debug("Initialized WorkerState for app")
        return self._worker_state

    @property
    def ep(self):
        name = "_ep"
        if hasattr(self, name):
            ep = getattr(self, name)
        else:
            # 传递redis_prefix到consumer_config
            consumer_config = self.consumer_config.copy() if self.consumer_config else {}
            consumer_config['redis_prefix'] = self.redis_prefix

            ep = EventPool(
                self.redis,
                self.async_redis,
                redis_url=self.redis_url,
                consumer_strategy=self.consumer_strategy,
                consumer_config=consumer_config,
                redis_prefix=self.redis_prefix,
                app=self
            )
            setattr(self, name, ep)
        return ep

    def clear(self):
        if hasattr(self, "process"):
            delattr(self, "process")
        if hasattr(self, "_ep"):
            delattr(self, "_ep")

    def get_task_by_name(self, name: str) -> Task:
        # 1. 直接查找完整名称
        task = self._tasks.get(name)
        if task:
            return task
        
        # 2. 如果是简单名称（不含.），尝试匹配所有以该名称结尾的任务
        if '.' not in name:
            for task_key, task_obj in self._tasks.items():
                # 匹配 "module.function_name" 形式，提取函数名部分
                if '.' in task_key:
                    _, func_name = task_key.rsplit('.', 1)
                    if func_name == name:
                        return task_obj
                elif task_key == name:
                    # 完全匹配（可能没有模块前缀）
                    return task_obj
        
        return None

    def include_module(self, modules: list):
        self.include += modules

    def _task_from_fun(
        self, fun, name=None, base=None, queue=None, bind=False, retry_config=None, rate_limit=None, **options
    ) -> Task:
        name = name or gen_task_name(fun.__name__, fun.__module__)
        base = base or Task

        # 不再限制队列模式，因为每个task都有独立的consumer group

        if name not in self._tasks:
            run = staticmethod(fun)
            task: Task = type(
                fun.__name__,
                (base,),
                dict(
                    {
                        "app": self,
                        "name": name,
                        "run": run,
                        "queue": queue,
                        "retry_config": retry_config,  # 存储重试配置
                        "rate_limit": rate_limit,  # 存储限流配置
                        "_decorated": True,
                        "__doc__": fun.__doc__,
                        "__module__": fun.__module__,
                        "__annotations__": fun.__annotations__,
                        "__wrapped__": run,
                    },
                    **options,
                ),
            )()
            task.bind_app(self)
            with contextlib.suppress(AttributeError):
                task.__qualname__ = fun.__qualname__
            self._tasks[task.name] = task

            # 记录队列和任务的映射（用于查找）
            if queue:
                if queue not in self._queue_tasks:
                    self._queue_tasks[queue] = []
                self._queue_tasks[queue].append(name)

            # 如果任务配置了限流，注册到Redis；否则删除旧配置
            if rate_limit:
                # 支持 int (QPS) 和 ConcurrencyLimit/QPSLimit 对象
                if isinstance(rate_limit, int) and rate_limit > 0:
                    # 简单的 int 值作为 QPS 限制
                    self._register_rate_limit(name, rate_limit)
                elif hasattr(rate_limit, 'to_dict'):
                    # RateLimitConfig 对象（ConcurrencyLimit 或 QPSLimit）
                    self._register_rate_limit_config(name, rate_limit)
            else:
                # 没有限流配置，删除 Redis 中的旧配置（如果存在）
                from jettask.utils.rate_limit.limiter import RateLimiterManager

                RateLimiterManager.unregister_rate_limit_config(
                    redis_client=self.redis,
                    task_name=name,
                    redis_prefix=self.redis_prefix
                )
        else:
            task = self._tasks[name]
        return task

    def _register_rate_limit(self, task_name: str, qps_limit: int):
        """注册任务的 QPS 限流规则到 Redis"""
        from jettask.utils.rate_limit.config import QPSLimit
        from jettask.utils.rate_limit.limiter import RateLimiterManager

        # 转换为 QPSLimit 配置对象
        config = QPSLimit(qps=qps_limit)
        # 调用 limiter.py 中的静态方法
        RateLimiterManager.register_rate_limit_config(
            redis_client=self.redis,
            task_name=task_name,
            config=config,
            redis_prefix=self.redis_prefix
        )

    def _register_rate_limit_config(self, task_name: str, config):
        """注册任务的限流配置对象到 Redis

        Args:
            task_name: 任务名称
            config: RateLimitConfig 对象（ConcurrencyLimit 或 QPSLimit）
        """
        from jettask.utils.rate_limit.limiter import RateLimiterManager

        # 调用 limiter.py 中的静态方法
        RateLimiterManager.register_rate_limit_config(
            redis_client=self.redis,
            task_name=task_name,
            config=config,
            redis_prefix=self.redis_prefix
        )

    def task(
        self,
        name: str = None,
        queue: str = None,
        base: Task = None,
        # 重试相关参数
        max_retries: int = 0,
        retry_backoff: bool = True,  # 是否使用指数退避
        retry_backoff_max: float = 60,  # 最大退避时间（秒）
        retry_on_exceptions: tuple = None,  # 可重试的异常类型
        # 限流相关参数
        rate_limit: int = None,  # QPS 限制（每秒允许执行的任务数）
        *args,
        **kwargs,
    ):
        def _create_task_cls(fun):
            # 将重试配置传递给_task_from_fun
            retry_config = None
            if max_retries > 0:
                retry_config = {
                    'max_retries': max_retries,
                    'retry_backoff': retry_backoff,
                    'retry_backoff_max': retry_backoff_max,
                }
                # 将异常类转换为类名字符串，以便序列化
                if retry_on_exceptions:
                    retry_config['retry_on_exceptions'] = [
                        exc if isinstance(exc, str) else exc.__name__
                        for exc in retry_on_exceptions
                    ]
            return self._task_from_fun(fun, name, base, queue, retry_config=retry_config, rate_limit=rate_limit, *args, **kwargs)

        return _create_task_cls
    
    def include_router(self, router, prefix: str = None):
        """
        包含一个TaskRouter，将其所有任务注册到app中
        
        Args:
            router: TaskRouter实例
            prefix: 额外的前缀（可选）
        """
        from ..task.router import TaskRouter
        
        if not isinstance(router, TaskRouter):
            raise TypeError(f"Expected TaskRouter, got {type(router)}")
        
        # 获取router中的所有任务
        tasks = router.get_tasks()
        
        for task_name, task_config in tasks.items():
            # 复制配置，避免修改原始数据
            config = task_config.copy()
            
            # 如果指定了额外前缀，添加到任务名前面
            if prefix:
                if config.get('name'):
                    config['name'] = f"{prefix}.{config['name']}"
                else:
                    config['name'] = f"{prefix}.{task_name}"
            
            # 获取任务函数和配置
            func = config.pop('func')
            name = config.pop('name', task_name)
            queue = config.pop('queue', None)
            
            # 提取重试相关参数
            retry_config = {}
            if 'max_retries' in config:
                retry_config['max_retries'] = config.pop('max_retries', 0)
            if 'retry_delay' in config:
                retry_config['retry_backoff_max'] = config.pop('retry_delay', 60)
            
            # 注册任务到app
            self._task_from_fun(
                func,
                name=name,
                queue=queue,
                retry_config=retry_config if retry_config else None,
                **config
            )
    
    def send_tasks(self, messages: list, asyncio: bool = False):
        """
        统一的任务发送接口 - 支持同步和异步

        Args:
            messages: TaskMessage对象列表（或字典列表）
            asyncio: 是否使用异步模式（默认False）

        Returns:
            同步模式: List[str] - 任务ID列表
            异步模式: 返回协程，需要使用 await

        使用示例:
            from jettask.core.message import TaskMessage

            # 同步发送
            msg = TaskMessage(
                queue="order_processing",
                args=(12345,),
                kwargs={"customer_id": "C001", "amount": 99.99}
            )
            task_ids = app.send_tasks([msg])

            # 异步发送
            task_ids = await app.send_tasks([msg], asyncio=True)

            # 批量发送
            messages = [
                TaskMessage(queue="email", kwargs={"to": "user1@example.com"}),
                TaskMessage(queue="email", kwargs={"to": "user2@example.com"}),
                TaskMessage(queue="sms", kwargs={"phone": "123456789"}),
            ]
            task_ids = app.send_tasks(messages)

            # 跨项目发送（不需要task定义）
            messages = [
                TaskMessage(queue="remote_queue", kwargs={"data": "value"})
            ]
            task_ids = await app.send_tasks(messages, asyncio=True)
        """
        if asyncio:
            return self._send_tasks_async(messages)
        else:
            return self._send_tasks_sync(messages)

    def _send_tasks_sync(self, messages: list):
        """同步发送任务"""
        if not messages:
            return []

        results = []

        # 按队列分组消息，以便批量处理
        queue_messages = {}
        for msg in messages:
            # 支持TaskMessage对象或字典
            if isinstance(msg, dict):
                msg = TaskMessage.from_dict(msg)
            elif not isinstance(msg, TaskMessage):
                raise ValueError(f"Invalid message type: {type(msg)}. Expected TaskMessage or dict")

            # 验证消息
            msg.validate()

            # 确定实际的队列名（考虑优先级）
            actual_queue = msg.queue
            if msg.priority is not None:
                # 将优先级拼接到队列名后面
                actual_queue = f"{msg.queue}:{msg.priority}"
                # 更新消息体中的queue字段，确保与实际发送的stream key一致
                msg.queue = actual_queue

            # 按队列分组
            if actual_queue not in queue_messages:
                queue_messages[actual_queue] = []
            queue_messages[actual_queue].append(msg)

        # 处理每个队列的消息
        for queue, queue_msgs in queue_messages.items():
            batch_results = self._send_batch_messages_sync(queue, queue_msgs)
            results.extend(batch_results)

        return results

    async def _send_tasks_async(self, messages: list):
        """异步发送任务"""
        if not messages:
            return []

        results = []

        # 按队列分组消息，以便批量处理
        queue_messages = {}
        for msg in messages:
            # 支持TaskMessage对象或字典
            if isinstance(msg, dict):
                msg = TaskMessage.from_dict(msg)
            elif not isinstance(msg, TaskMessage):
                raise ValueError(f"Invalid message type: {type(msg)}. Expected TaskMessage or dict")

            # 验证消息
            msg.validate()

            # 确定实际的队列名（考虑优先级）
            actual_queue = msg.queue
            if msg.priority is not None:
                # 将优先级拼接到队列名后面
                actual_queue = f"{msg.queue}:{msg.priority}"
                # 更新消息体中的queue字段，确保与实际发送的stream key一致
                msg.queue = actual_queue

            # 按队列分组
            if actual_queue not in queue_messages:
                queue_messages[actual_queue] = []
            queue_messages[actual_queue].append(msg)

        # 处理每个队列的消息
        for queue, queue_msgs in queue_messages.items():
            batch_results = await self._send_batch_messages_async(queue, queue_msgs)
            results.extend(batch_results)

        return results
    
    def _send_batch_messages_sync(self, queue: str, messages: list) -> list:
        """批量发送任务（同步）"""
        from ..utils.serializer import dumps_str

        # 分离普通任务和延迟任务
        normal_messages = []
        delayed_messages = []

        for msg in messages:
            msg_dict = msg.to_dict()

            # 处理延迟任务
            if msg.delay and msg.delay > 0:
                # 添加延迟执行标记
                current_time = time.time()
                msg_dict['execute_at'] = current_time + msg.delay
                msg_dict['is_delayed'] = 1
                delayed_messages.append((msg_dict, msg.delay))
            else:
                normal_messages.append(msg_dict)

        results = []

        # 发送普通任务（统一使用批量发送）
        if normal_messages:
            batch_results = self.ep._batch_send_event_sync(
                self.ep.get_prefixed_queue_name(queue),
                [{'data': dumps_str(msg)} for msg in normal_messages],
                self.ep.get_redis_client(asyncio=False, binary=True).pipeline()
            )
            results.extend(batch_results)

        # 发送延迟任务（需要同时添加到DELAYED_QUEUE）
        if delayed_messages:
            delayed_results = self._send_delayed_tasks_sync(queue, delayed_messages)
            results.extend(delayed_results)

        return results

    async def _send_batch_messages_async(self, queue: str, messages: list) -> list:
        """批量发送任务（异步）"""
        from ..utils.serializer import dumps_str

        # 分离普通任务和延迟任务
        normal_messages = []
        delayed_messages = []

        for msg in messages:
            msg_dict = msg.to_dict()

            # 处理延迟任务
            if msg.delay and msg.delay > 0:
                # 添加延迟执行标记
                current_time = time.time()
                msg_dict['execute_at'] = current_time + msg.delay
                msg_dict['is_delayed'] = 1
                delayed_messages.append((msg_dict, msg.delay))
            else:
                normal_messages.append(msg_dict)

        results = []

        # 发送普通任务（统一使用批量发送）
        if normal_messages:
            batch_results = await self.ep._batch_send_event(
                self.ep.get_prefixed_queue_name(queue),
                [{'data': dumps_str(msg)} for msg in normal_messages],
                self.ep.get_redis_client(asyncio=True, binary=True).pipeline()
            )
            results.extend(batch_results)

        # 发送延迟任务（需要同时添加到DELAYED_QUEUE）
        if delayed_messages:
            delayed_results = await self._send_delayed_tasks_async(queue, delayed_messages)
            results.extend(delayed_results)

        return results
    
    def _send_delayed_tasks_sync(self, queue: str, delayed_messages: list) -> list:
        """发送延迟任务到Stream并添加到延迟队列（同步）

        Args:
            queue: 队列名，可能包含优先级后缀（如 "queue_name:6"）
            delayed_messages: 延迟消息列表，每项为 (msg_dict, delay_seconds)

        Note:
            延迟队列和Stream现在完全对应（包括优先级后缀）。
            Scanner会动态发现所有优先级队列并扫描对应的延迟队列。
        """
        from ..utils.serializer import dumps_str
        from ..messaging.registry import QueueRegistry

        # 注册队列（确保队列在注册表中，Scanner才能发现它）
        registry = QueueRegistry(self.redis, self.async_redis, self.redis_prefix)

        # 如果队列包含优先级后缀，注册为优先级队列
        if ':' in queue and queue.rsplit(':', 1)[1].isdigit():
            base_queue = queue.rsplit(':', 1)[0]
            priority = int(queue.rsplit(':', 1)[1])
            registry.register_queue_sync(base_queue)
            registry.register_priority_queue_sync(base_queue, priority)
            logger.debug(f"Registered priority queue: {queue} (base: {base_queue}, priority: {priority})")
        else:
            registry.register_queue_sync(queue)
            logger.debug(f"Registered queue: {queue}")

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix]
        prefixed_queue = self.ep.get_prefixed_queue_name(queue)

        for msg_dict, _ in delayed_messages:
            stream_data = dumps_str(msg_dict)
            execute_at = msg_dict['execute_at']

            # 延迟队列名和Stream名现在完全对应
            lua_args.extend([
                prefixed_queue,        # Stream 键（包含优先级）
                stream_data,           # 消息数据
                str(execute_at)        # 执行时间
            ])

        # 执行Lua脚本
        client = self.ep.get_redis_client(asyncio=False, binary=True)

        # 注册Lua脚本（使用config模块中的脚本）
        if not hasattr(self, '_delayed_task_script_sync'):
            self._delayed_task_script_sync = client.register_script(LUA_SCRIPT_SEND_DELAYED_TASKS)

        # 执行脚本
        results = self._delayed_task_script_sync(keys=[], args=lua_args)

        # 解码结果
        decoded_results = [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]
        return decoded_results

    async def _send_delayed_tasks_async(self, queue: str, delayed_messages: list) -> list:
        """发送延迟任务到Stream并添加到延迟队列（异步）

        Args:
            queue: 队列名，可能包含优先级后缀（如 "queue_name:6"）
            delayed_messages: 延迟消息列表，每项为 (msg_dict, delay_seconds)

        Note:
            延迟队列和Stream现在完全对应（包括优先级后缀）。
            Scanner会动态发现所有优先级队列并扫描对应的延迟队列。
        """
        from ..utils.serializer import dumps_str
        from ..messaging.registry import QueueRegistry

        # 注册队列（确保队列在注册表中，Scanner才能发现它）
        registry = QueueRegistry(self.redis, self.async_redis, self.redis_prefix)

        # 如果队列包含优先级后缀，注册为优先级队列
        if ':' in queue and queue.rsplit(':', 1)[1].isdigit():
            base_queue = queue.rsplit(':', 1)[0]
            priority = int(queue.rsplit(':', 1)[1])
            await registry.register_queue(base_queue)
            await registry.register_priority_queue(base_queue, priority)
            logger.debug(f"Registered priority queue: {queue} (base: {base_queue}, priority: {priority})")
        else:
            await registry.register_queue(queue)
            logger.debug(f"Registered queue: {queue}")

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix]
        prefixed_queue = self.ep.get_prefixed_queue_name(queue)

        for msg_dict, _ in delayed_messages:
            stream_data = dumps_str(msg_dict)
            execute_at = msg_dict['execute_at']

            # 延迟队列名和Stream名现在完全对应
            lua_args.extend([
                prefixed_queue,        # Stream 键（包含优先级）
                stream_data,           # 消息数据
                str(execute_at)        # 执行时间
            ])

        # 执行Lua脚本
        client = self.ep.get_redis_client(asyncio=True, binary=True)

        # 注册Lua脚本（使用config模块中的脚本）
        if not hasattr(self, '_delayed_task_script_async'):
            self._delayed_task_script_async = client.register_script(LUA_SCRIPT_SEND_DELAYED_TASKS)

        # 执行脚本
        results = await self._delayed_task_script_async(keys=[], args=lua_args)

        # 解码结果
        decoded_results = [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]
        return decoded_results

    def _get_task_names_from_queue(self, queue: str, task_name: str = None) -> list:
        """获取队列的任务名列表

        Args:
            queue: 队列名称（可能包含优先级后缀）
            task_name: 可选的任务名，如果提供则直接返回 [task_name]

        Returns:
            任务名列表，如果 task_name 提供则返回 [task_name]，否则返回队列的所有任务名
        """
        if task_name is not None:
            return [task_name]

        # 确保 registry 有 redis_client
        if self.registry.redis is None:
            self.registry.redis = self.redis
            self.registry.async_redis = self.async_redis

        # 从 base_queue 中提取基础队列名（去掉优先级）
        base_queue = queue.split(':')[0] if ':' in queue else queue
        task_names = self.registry.get_task_names_by_queue_sync(base_queue)

        return list(task_names) if task_names else []

    def get_result(self, event_id: str, queue: str, task_name: str = None,
                   delete: bool = False, asyncio: bool = False,
                   delayed_deletion_ex: int = None, wait: bool = False,
                   timeout: int = 300, poll_interval: float = 0.5):
        """获取任务执行结果

        在任务组架构下，每个任务都有独立的执行结果存储。
        结果存储格式: {redis_prefix}:TASK:{event_id}:{group_name}

        这个方法支持完全解耦的生产者-消费者模式，生产者只需要知道：
        - event_id: 发送任务时返回的事件ID
        - queue: 队列名称
        - task_name: 任务名称（可选，不提供时会获取该队列所有任务的结果）

        Args:
            event_id: 任务事件ID（发送任务时返回的消息ID）
            queue: 队列名称
            task_name: 任务名称（可选）。如果不提供，会获取该队列所有任务的结果，返回列表
            delete: 是否删除结果（默认False）
            asyncio: 是否使用异步模式（默认False）
            delayed_deletion_ex: 延迟删除时间（秒），设置后会在指定时间后自动删除
            wait: 是否阻塞等待直到任务完成（默认False）
            timeout: 等待超时时间（秒），默认300秒
            poll_interval: 轮询间隔（秒），默认0.5秒

        Returns:
            当指定task_name时:
                同步模式: 任务结果（字符串或字节），如果任务未完成返回None
                异步模式: 返回协程，需要使用 await
            当不指定task_name时:
                返回列表，每个元素是字典: [{"task_name": "xxx", "result": ..., "status": ...}, ...]

        Raises:
            TaskTimeoutError: 等待超时
            TaskExecutionError: 任务执行失败
            TaskNotFoundError: 任务不存在

        Examples:
            # 获取单个任务结果
            result = app.get_result("1234567890-0", "my_queue", task_name="my_task")

            # 获取队列中所有任务的结果
            results = app.get_result("1234567890-0", "my_queue")
            # 返回: [{"task_name": "task1", "result": ..., "status": ...}, {"task_name": "task2", ...}]

            # 异步获取所有任务结果
            results = await app.get_result("1234567890-0", "my_queue", asyncio=True)
        """
        # 判断是否指定了 task_name，决定最终返回格式
        return_single = task_name is not None

        # 获取需要查询的任务名列表
        task_names = self._get_task_names_from_queue(queue, task_name)

        # 如果没有任务，直接返回空列表
        if not task_names:
            if asyncio:
                async def _return_empty_list():
                    return []
                return _return_empty_list()
            else:
                return []

        # 统一处理：遍历所有任务获取结果
        if asyncio:
            return self._get_results_async(event_id, queue, task_names, delete,
                                          delayed_deletion_ex, wait, timeout, poll_interval, return_single)
        else:
            return self._get_results_sync(event_id, queue, task_names, delete,
                                         delayed_deletion_ex, wait, timeout, poll_interval, return_single)

    def get_queue_position(self, event_id: str, queue: str, task_name: str = None, asyncio: bool = False):
        """获取任务在队列中的排队情况

        通过 event_id 查询任务在队列中的排队位置，包括：
        - 距离被读取还差多少任务
        - 距离被消费还差多少任务

        Args:
            event_id: 任务事件ID（发送任务时返回的消息ID）
            queue: 队列名称
            task_name: 任务名称（可选）。如果不提供，会获取该队列所有任务的排队情况
            asyncio: 是否使用异步模式（默认False）

        Returns:
            当指定task_name时:
                返回字典: {
                    "task_name": "xxx",
                    "task_offset": 12,
                    "read_offset": 14,
                    "task_ack_offset": 10,
                    "pending_read": 2,      # 距离被读取还差2个任务
                    "pending_consume": -2   # 已经被消费了（负数表示已完成）
                }
            当不指定task_name时:
                返回列表，每个元素是上述格式的字典

        Note:
            排名信息反映的是任务的发送顺序（offset），而不是执行顺序。
            在并发执行的场景下，排名靠后的任务可能先执行完成，而排名靠前的任务可能还在执行中。

            例如：
            - 任务A (offset=10) 和任务B (offset=15) 同时被读取
            - 如果任务B执行得快，可能会先完成
            - 此时任务A的 pending_consume 可能仍为正数（还未消费确认）
            - 而任务B的 pending_consume 已经变为负数（已完成）

            因此：
            - pending_read 表示有多少任务在你之前被发送到队列
            - pending_consume 表示有多少任务在你之前被消费确认（不代表执行顺序）
            - 负数的 pending_consume 只表示该任务已被确认，不表示所有前面的任务都已完成

        Examples:
            # 获取单个任务的排队情况
            position = app.get_queue_position("1234567890-0", "my_queue", task_name="my_task")

            # 获取队列中所有任务的排队情况
            positions = app.get_queue_position("1234567890-0", "my_queue")

            # 异步获取
            position = await app.get_queue_position("1234567890-0", "my_queue", asyncio=True)
        """
        # 判断是否指定了 task_name，决定最终返回格式
        return_single = task_name is not None

        # 获取需要查询的任务名列表
        task_names = self._get_task_names_from_queue(queue, task_name)

        # 如果没有任务，直接返回空列表
        if not task_names:
            if asyncio:
                async def _return_empty_list():
                    return []
                return _return_empty_list()
            else:
                return []

        # 统一处理：遍历所有任务获取排队情况
        if asyncio:
            return self._get_queue_positions_async(event_id, queue, task_names, return_single)
        else:
            return self._get_queue_positions_sync(event_id, queue, task_names, return_single)

    def _get_queue_positions_sync(self, event_id: str, queue: str, task_names: list, return_single: bool):
        """同步获取任务排队情况"""
        results = []

        # 构建 stream key
        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"

        # 从 stream 中获取任务数据
        try:
            # XRANGE 获取指定 event_id 的消息
            stream_data = self.binary_redis.xrange(prefixed_queue, min=event_id, max=event_id, count=1)

            if not stream_data:
                # 任务不存在于 stream 中
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Task not found in stream"
                    })
                if return_single:
                    return results[0] if results else None
                return results

            # 解析 stream 数据
            message_id, message_data = stream_data[0]

            # 解码字段
            task_offset = None
            for key, value in message_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if key == 'offset':
                    if isinstance(value, bytes):
                        task_offset = int(value.decode('utf-8'))
                    else:
                        task_offset = int(value)
                    break

            if task_offset is None:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Offset not found in task data"
                    })
                if return_single:
                    return results[0] if results else None
                return results

        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read from stream: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        # 获取 READ_OFFSETS 和 TASK_OFFSETS（使用 pipeline + HMGET 优化）
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"
        task_offsets_key = f"{self.redis_prefix}:TASK_OFFSETS"

        # 提取基础队列名（去掉优先级）
        base_queue = queue.split(':')[0] if ':' in queue else queue

        # 构建需要查询的字段列表
        offset_keys = [f"{base_queue}:{task_name}" for task_name in task_names]

        try:
            # 使用 pipeline 批量获取所有需要的字段
            pipeline = self.redis.pipeline()
            pipeline.hmget(read_offsets_key, offset_keys)
            pipeline.hmget(task_offsets_key, offset_keys)
            read_offsets_list, task_offsets_list = pipeline.execute()
        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read offsets: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        # 对每个任务计算排队情况
        for idx, task_name in enumerate(task_names):
            # 获取 read_offset
            read_offset = read_offsets_list[idx]
            if read_offset is not None:
                read_offset = int(read_offset)

            # 获取 task_ack_offset
            task_ack_offset = task_offsets_list[idx]
            if task_ack_offset is not None:
                task_ack_offset = int(task_ack_offset)

            # 计算排队情况
            # pending_read: 正数表示还差多少个任务才能被读取，0表示刚好被读取，负数表示已被读取
            pending_read = (task_offset - read_offset) if read_offset is not None else None
            # pending_consume: 正数表示还差多少个任务才能被消费，0表示刚好被消费，负数表示已被消费
            pending_consume = (task_offset - task_ack_offset) if task_ack_offset is not None else None

            results.append({
                "task_name": task_name,
                "task_offset": task_offset,
                "read_offset": read_offset,
                "task_ack_offset": task_ack_offset,
                "pending_read": pending_read,
                "pending_consume": pending_consume
            })

        # 根据 return_single 决定返回格式
        if return_single:
            return results[0] if results else None
        return results

    async def _get_queue_positions_async(self, event_id: str, queue: str, task_names: list, return_single: bool):
        """异步获取任务排队情况"""
        results = []

        # 构建 stream key
        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"

        # 从 stream 中获取任务数据
        try:
            # XRANGE 获取指定 event_id 的消息
            stream_data = await self.async_binary_redis.xrange(prefixed_queue, min=event_id, max=event_id, count=1)

            if not stream_data:
                # 任务不存在于 stream 中
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Task not found in stream"
                    })
                if return_single:
                    return results[0] if results else None
                return results

            # 解析 stream 数据
            message_id, message_data = stream_data[0]

            # 解码字段
            task_offset = None
            for key, value in message_data.items():
                if isinstance(key, bytes):
                    key = key.decode('utf-8')
                if key == 'offset':
                    if isinstance(value, bytes):
                        task_offset = int(value.decode('utf-8'))
                    else:
                        task_offset = int(value)
                    break

            if task_offset is None:
                for task_name in task_names:
                    results.append({
                        "task_name": task_name,
                        "error": "Offset not found in task data"
                    })
                if return_single:
                    return results[0] if results else None
                return results

        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read from stream: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        # 获取 READ_OFFSETS 和 TASK_OFFSETS（使用 pipeline + HMGET 优化）
        read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"
        task_offsets_key = f"{self.redis_prefix}:TASK_OFFSETS"

        # 提取基础队列名（去掉优先级）
        base_queue = queue.split(':')[0] if ':' in queue else queue

        # 构建需要查询的字段列表
        offset_keys = [f"{base_queue}:{task_name}" for task_name in task_names]

        try:
            # 使用 pipeline 批量获取所有需要的字段
            pipeline = self.async_redis.pipeline()
            pipeline.hmget(read_offsets_key, offset_keys)
            pipeline.hmget(task_offsets_key, offset_keys)
            read_offsets_list, task_offsets_list = await pipeline.execute()
        except Exception as e:
            for task_name in task_names:
                results.append({
                    "task_name": task_name,
                    "error": f"Failed to read offsets: {str(e)}"
                })
            if return_single:
                return results[0] if results else None
            return results

        # 对每个任务计算排队情况
        for idx, task_name in enumerate(task_names):
            # 获取 read_offset
            read_offset = read_offsets_list[idx]
            if read_offset is not None:
                read_offset = int(read_offset)

            # 获取 task_ack_offset
            task_ack_offset = task_offsets_list[idx]
            if task_ack_offset is not None:
                task_ack_offset = int(task_ack_offset)

            # 计算排队情况
            # pending_read: 正数表示还差多少个任务才能被读取，0表示刚好被读取，负数表示已被读取
            pending_read = (task_offset - read_offset) if read_offset is not None else None
            # pending_consume: 正数表示还差多少个任务才能被消费，0表示刚好被消费，负数表示已被消费
            pending_consume = (task_offset - task_ack_offset) if task_ack_offset is not None else None

            results.append({
                "task_name": task_name,
                "task_offset": task_offset,
                "read_offset": read_offset,
                "task_ack_offset": task_ack_offset,
                "pending_read": pending_read,
                "pending_consume": pending_consume
            })

        # 根据 return_single 决定返回格式
        if return_single:
            return results[0] if results else None
        return results

    def _build_task_key(self, task_name: str, queue: str, event_id: str):
        """构建任务的 key 信息

        Returns:
            tuple: (group_name, full_key)
        """
        prefixed_queue = f"{self.redis_prefix}:QUEUE:{queue}"
        group_name = f"{prefixed_queue}:{task_name}"
        status_key = f"{event_id}:{group_name}"
        full_key = f"{self.redis_prefix}:TASK:{status_key}"
        return group_name, full_key

    @staticmethod
    def _decode_bytes(value):
        """解码字节为字符串"""
        if value and isinstance(value, bytes):
            return value.decode('utf-8')
        return value

    @staticmethod
    def _is_task_completed(status):
        """检查任务是否已完成（成功）"""
        return status in [TaskStatus.COMPLETED.value, TaskStatus.SUCCESS.value]

    @staticmethod
    def _is_task_failed(status):
        """检查任务是否失败"""
        return status in [TaskStatus.ERROR.value, TaskStatus.FAILED.value, "ERROR", "FAILED", "error", "failed"]

    def _get_results_sync(self, event_id: str, queue: str, task_names: list,
                         delete: bool, delayed_deletion_ex: int, wait: bool,
                         timeout: int, poll_interval: float, return_single: bool):
        """同步获取任务结果（支持单个或批量）"""
        results = []

        for task_name in task_names:
            try:
                _, full_key = self._build_task_key(task_name, queue, event_id)

                # 统一调用 _get_result_sync，通过 wait 参数控制行为
                task_info = self._get_result_sync(full_key, event_id, delete, delayed_deletion_ex,
                                                  wait, timeout, poll_interval)

                # 如果任务不存在
                if not task_info:
                    results.append({
                        "task_name": task_name,
                        "status": None,
                        "result": None
                    })
                else:
                    # 添加 task_name 到结果中
                    task_info["task_name"] = task_name
                    results.append(task_info)

            except Exception as e:
                results.append({
                    "task_name": task_name,
                    "status": "ERROR",
                    "result": None,
                    "error_msg": str(e)
                })

        # 根据 return_single 决定返回格式
        if return_single:
            return results[0] if results else None
        return results

    async def _get_results_async(self, event_id: str, queue: str, task_names: list,
                                 delete: bool, delayed_deletion_ex: int, wait: bool,
                                 timeout: int, poll_interval: float, return_single: bool):
        """异步获取任务结果（支持单个或批量）"""
        results = []

        for task_name in task_names:
            try:
                _, full_key = self._build_task_key(task_name, queue, event_id)

                # 统一调用 _get_result_async，通过 wait 参数控制行为
                task_info = await self._get_result_async(full_key, event_id, delete, delayed_deletion_ex,
                                                         wait, timeout, poll_interval)

                # 如果任务不存在
                if not task_info:
                    results.append({
                        "task_name": task_name,
                        "status": TaskStatus.PENDING.value,
                        "result": None
                    })
                else:
                    # 添加 task_name 到结果中
                    task_info["task_name"] = task_name
                    results.append(task_info)

            except Exception as e:
                results.append({
                    "task_name": task_name,
                    "status": "ERROR",
                    "result": None,
                    "error_msg": str(e)
                })

        # 根据 return_single 决定返回格式
        if return_single:
            return results[0] if results else None
        return results

    def _get_result_sync(self, full_key: str, event_id: str, delete: bool, delayed_deletion_ex: int,
                         wait: bool = False, timeout: int = 300, poll_interval: float = 0.5):
        """同步获取任务结果（支持等待模式）"""
        from ..exceptions import TaskTimeoutError, TaskExecutionError, TaskNotFoundError

        # 使用二进制客户端，不自动解码（因为 result 是 msgpack 序列化的）
        client = self.binary_redis
        start_time = time.time()

        while True:
            # 获取整个 hash 的所有字段
            task_data = client.hgetall(full_key)

            if not task_data:
                if wait:
                    raise TaskNotFoundError(f"Task {event_id} not found")
                return None

            # 解码字节字段
            decoded_data = {}
            for key, value in task_data.items():
                # 解码 key
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                # 跳过内部标记字段
                if key.startswith('__'):
                    continue

                # 解码 value - 只有 result 字段需要 loads_str
                if isinstance(value, bytes):
                    if key == 'result':
                        try:
                            decoded_data[key] = loads_str(value)
                        except Exception:
                            decoded_data[key] = value
                    else:
                        # 其他字段尝试 UTF-8 解码
                        try:
                            decoded_data[key] = value.decode('utf-8')
                        except Exception:
                            decoded_data[key] = value
                else:
                    decoded_data[key] = value

            # 如果不需要等待，处理删除逻辑后直接返回
            if not wait:
                if delayed_deletion_ex is not None:
                    client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        client.hset(full_key, "__pending_delete", "1")
                    else:
                        client.delete(full_key)
                return decoded_data

            # 需要等待：检查任务状态
            status = decoded_data.get('status')

            # 检查任务是否完成
            if self._is_task_completed(status):
                # 任务成功完成，处理删除逻辑后返回
                if delayed_deletion_ex is not None:
                    client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        client.hset(full_key, "__pending_delete", "1")
                    else:
                        client.delete(full_key)
                return decoded_data

            elif self._is_task_failed(status):
                # 任务失败，抛出异常
                error_msg = decoded_data.get('error_msg', 'Task execution failed')
                raise TaskExecutionError(event_id, error_msg)

            # 检查超时
            if time.time() - start_time > timeout:
                raise TaskTimeoutError(f"Task {event_id} timed out after {timeout} seconds")

            # 任务仍在执行中，等待后重试
            time.sleep(poll_interval)

    async def _get_result_async(self, full_key: str, event_id: str, delete: bool, delayed_deletion_ex: int,
                                wait: bool = False, timeout: int = 300, poll_interval: float = 0.5):
        """异步获取任务结果（支持等待模式）"""

        # 使用二进制客户端，不自动解码（因为 result 是 msgpack 序列化的）
        client = self.async_binary_redis
        start_time = time.time()

        while True:
            # 获取整个 hash 的所有字段
            task_data = await client.hgetall(full_key)

            if not task_data:
                if wait:
                    raise TaskNotFoundError(f"Task {event_id} not found")
                return None

            # 解码字节字段
            decoded_data = {}
            for key, value in task_data.items():
                # 解码 key
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                # 跳过内部标记字段
                if key.startswith('__'):
                    continue

                # 解码 value - 只有 result 字段需要 loads_str
                if isinstance(value, bytes):
                    if key == 'result':
                        try:
                            decoded_data[key] = loads_str(value)
                        except Exception:
                            decoded_data[key] = value
                    else:
                        # 其他字段尝试 UTF-8 解码
                        try:
                            decoded_data[key] = value.decode('utf-8')
                        except Exception:
                            decoded_data[key] = value
                else:
                    decoded_data[key] = value

            # 如果不需要等待，处理删除逻辑后直接返回
            if not wait:
                if delayed_deletion_ex is not None:
                    await client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        await client.hset(full_key, "__pending_delete", "1")
                    else:
                        await client.delete(full_key)
                return decoded_data

            # 需要等待：检查任务状态
            status = decoded_data.get('status')

            # 检查任务是否完成
            if self._is_task_completed(status):
                # 任务成功完成，处理删除逻辑后返回
                if delayed_deletion_ex is not None:
                    await client.expire(full_key, delayed_deletion_ex)
                elif delete:
                    if self.task_center and self.task_center.is_enabled:
                        await client.hset(full_key, "__pending_delete", "1")
                    else:
                        await client.delete(full_key)
                return decoded_data

            elif self._is_task_failed(status):
                # 任务失败，抛出异常
                error_msg = decoded_data.get('error_msg', 'Task execution failed')
                raise TaskExecutionError(event_id, error_msg)

            # 检查超时
            if time.time() - start_time > timeout:
                raise TaskTimeoutError(f"Task {event_id} timed out after {timeout} seconds")

            # 等待后重试
            await asyncio.sleep(poll_interval)

    def register_router(self, router, prefix: str = None):
        """
        注册任务路由器
        
        Args:
            router: TaskRouter实例
            prefix: 额外的前缀（可选）
        
        使用示例：
            from jettask import Jettask, TaskRouter
            
            # 创建路由器
            email_router = TaskRouter(prefix="email", queue="emails")
            
            @email_router.task()
            async def send_email(to: str):
                pass
            
            # 注册到主应用
            app = Jettask(redis_url="redis://localhost:6379/0")
            app.register_router(email_router)
        """
        from ..task.router import TaskRouter
        
        if not isinstance(router, TaskRouter):
            raise TypeError("router must be a TaskRouter instance")
        
        # 注册所有任务
        for task_name, task_config in router.get_tasks().items():
            # 如果指定了额外前缀，添加到任务名
            if prefix:
                if task_config.get('name'):
                    task_config['name'] = f"{prefix}.{task_config['name']}"
                task_name = f"{prefix}.{task_name}"
            
            # 获取任务函数
            func = task_config.pop('func')
            name = task_config.pop('name', task_name)
            queue = task_config.pop('queue', None)
            
            # 注册任务
            task = self._task_from_fun(func, name, None, queue, **task_config)
            logger.debug(f"Registered task: {name} (queue: {queue or self.redis_prefix})")
        
        return self

    def _mount_module(self):
        for module in self.include:
            module = importlib.import_module(module)
            for attr_name in dir(module):
                obj = getattr(module, attr_name)
                if hasattr(obj, "app"):
                    self._tasks.update(getattr(obj, "app")._tasks)

    def _validate_tasks_for_executor(self, execute_type: str, queues: List[str]):
        """验证任务类型是否与执行器兼容"""
        if execute_type in ["asyncio", "multi_asyncio"]:
            return  # AsyncIO和MultiAsyncio可以处理异步任务
        
        # 只有Thread执行器不能处理异步任务
        incompatible_tasks = []
        for task_name, task in self._tasks.items():
            # 检查任务是否属于指定队列
            if task.queue not in queues:
                continue
                
            # 检查是否是异步任务
            if asyncio.iscoroutinefunction(task.run):
                incompatible_tasks.append({
                    'name': task_name,
                    'queue': task.queue,
                    'type': 'async'
                })
        
        if incompatible_tasks:
            error_msg = f"\n错误：{execute_type} 执行器不能处理异步任务！\n"
            error_msg += "发现以下异步任务：\n"
            for task in incompatible_tasks:
                error_msg += f"  - {task['name']} (队列: {task['queue']})\n"
            error_msg += f"\n解决方案：\n"
            error_msg += f"1. 使用 asyncio 或 process 执行器\n"
            error_msg += f"2. 或者将这些任务改为同步函数（去掉 async/await）\n"
            error_msg += f"3. 或者将这些任务的队列从监听列表中移除\n"
            raise ValueError(error_msg)
    

    def _start_with_heartbeat_thread(
        self,
        execute_type: str = "multi_asyncio",
        queues: List[str] = None,
        concurrency: int = 1,
        prefetch_multiplier: int = 1,
    ):
        """在主进程中启动执行器和心跳线程"""
        from jettask.worker.lifecycle import HeartbeatThreadManager

        # 1. 初始化 Worker ID - 复用 EventPool 中的 HeartbeatConsumerStrategy
        # 确保 EventPool 已初始化
        if not self.ep:
            raise RuntimeError("EventPool not initialized")

        # 使用 EventPool 中已创建的 HeartbeatConsumerStrategy
        if not self.consumer_manager or not self.consumer_manager._heartbeat_strategy:
            raise RuntimeError("ConsumerManager or HeartbeatConsumerStrategy not initialized")

        strategy = self.consumer_manager._heartbeat_strategy
        strategy._ensure_consumer_id()
        worker_id = strategy.consumer_id

        logger.info(f"Starting worker {worker_id} in main process (PID: {os.getpid()})")

        # 2. 启动心跳线程（在主进程中）
        heartbeat = HeartbeatThreadManager(
            redis_client=self.redis,
            worker_key=f"{self.redis_prefix}:WORKER:{worker_id}",
            worker_id=worker_id,
            redis_prefix=self.redis_prefix,
            interval=5.0
        )
        heartbeat.start()

        # 保存引用以便清理
        self._heartbeat_manager = heartbeat
        self._executor_processes = []

        try:
            # 3. 启动多进程执行器（直接调用 _start）
            self._start(
                execute_type=execute_type,
                queues=queues,
                concurrency=concurrency,
                prefetch_multiplier=prefetch_multiplier,
            )
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        finally:
            # 4. 清理
            logger.info("Shutting down worker...")

            # 停止心跳线程
            if hasattr(self, '_heartbeat_manager'):
                logger.debug("Stopping heartbeat thread...")
                self._heartbeat_manager.stop(timeout=2.0)

            # 清理资源
            self.cleanup()

    # ==================== 新的子方法：重构后的 Worker 启动逻辑 ====================

    def _generate_worker_id_lightweight(self) -> tuple:
        """
        轻量级生成 Worker ID（不初始化 EventPool）

        这个方法只生成 worker_id，不会初始化 EventPool、ConsumerManager 等重量级组件。
        用于主进程在 fork 子进程前生成 worker_id。

        Returns:
            (worker_id, worker_key) 元组
        """
        from jettask.worker.manager import WorkerNaming
        import asyncio
        import socket

        # 生成主机名前缀（与 HeartbeatConsumerStrategy 相同的逻辑）
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            prefix = hostname if hostname != 'localhost' else ip
        except:
            prefix = os.environ.get('HOSTNAME', 'unknown')

        # 创建轻量级的 worker naming
        naming = WorkerNaming()

        # 尝试复用离线的 worker ID
        reusable_id = None
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                logger.warning("Event loop is running, cannot reuse offline worker ID synchronously")
            else:
                # 直接使用 WorkerNaming 查找可复用的 ID
                reusable_id = loop.run_until_complete(
                    naming.find_reusable_worker_id(
                        prefix=prefix,
                        worker_state=self.worker_state
                    )
                )
        except RuntimeError:
            # 没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reusable_id = loop.run_until_complete(
                    naming.find_reusable_worker_id(
                        prefix=prefix,
                        worker_state=self.worker_state
                    )
                )
            finally:
                loop.close()

        # 生成或复用 worker_id
        if reusable_id:
            logger.info(f"[PID {os.getpid()}] Reusing offline worker ID: {reusable_id}")
            worker_id = reusable_id
        else:
            worker_id = naming.generate_worker_id(prefix)
            logger.info(f"[PID {os.getpid()}] Generated new worker ID: {worker_id}")

        worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"

        # 保存到实例
        self.worker_id = worker_id
        self.worker_key = worker_key

        return worker_id, worker_key

    def _initialize_worker(self, queues: List[str] = None) -> tuple:
        """
        初始化 Worker（完整版本，包含 EventPool 初始化）

        注意：这个方法会初始化 EventPool 和 ConsumerManager，会创建事件循环等状态。
        在多进程模式下，这些状态会被 fork 到子进程，需要在子进程中清理。

        Returns:
            (worker_id, worker_key) 元组
        """
        # 设置默认队列
        if not queues:
            queues = [self.redis_prefix]

        # 初始化 EventPool
        self.ep.queues = queues
        self.ep.init_routing()
        self._mount_module()

        # 收集任务列表（按队列分组）
        self._tasks_by_queue = {}
        for task_name, task in self._tasks.items():
            task_queue = task.queue or self.redis_prefix
            if task_queue in queues:
                if task_queue not in self._tasks_by_queue:
                    self._tasks_by_queue[task_queue] = []
                self._tasks_by_queue[task_queue].append(task_name)
                logger.debug(f"Task {task_name} -> queue {task_queue}")

        # 创建 Worker ID - 复用 EventPool 中的 HeartbeatConsumerStrategy
        # 确保 EventPool 已初始化
        if not self.ep:
            raise RuntimeError("EventPool not initialized")

        # 使用 EventPool 中已创建的 HeartbeatConsumerStrategy
        if not self.consumer_manager or not self.consumer_manager._heartbeat_strategy:
            raise RuntimeError("ConsumerManager or HeartbeatConsumerStrategy not initialized")

        strategy = self.consumer_manager._heartbeat_strategy

        # 尝试复用离线的 worker ID
        import asyncio
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # 如果事件循环正在运行，无法同步调用异步方法
                # 直接生成新的 ID（这种情况通常不会发生）
                logger.warning("Event loop is running, cannot reuse offline worker ID synchronously")
                strategy._ensure_consumer_id()
            else:
                # 事件循环未运行，可以使用 run_until_complete
                reusable_id = loop.run_until_complete(self._find_reusable_worker_id_async(strategy))
                if reusable_id:
                    logger.info(f"[PID {os.getpid()}] Reusing offline worker ID: {reusable_id}")
                    strategy.consumer_id = reusable_id
                    strategy._worker_key = f'{self.redis_prefix}:WORKER:{reusable_id}'
                else:
                    strategy._ensure_consumer_id()
        except RuntimeError:
            # 没有事件循环，创建新的
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                reusable_id = loop.run_until_complete(self._find_reusable_worker_id_async(strategy))
                if reusable_id:
                    logger.info(f"[PID {os.getpid()}] Reusing offline worker ID: {reusable_id}")
                    strategy.consumer_id = reusable_id
                    strategy._worker_key = f'{self.redis_prefix}:WORKER:{reusable_id}'
                else:
                    strategy._ensure_consumer_id()
            finally:
                loop.close()

        worker_id = strategy.consumer_id
        worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"

        # 保存 worker_id 到实例，供子进程使用
        self.worker_id = worker_id
        self.worker_key = worker_key

        logger.info(f"Worker initialized: {worker_id} (PID: {os.getpid()})")
        return worker_id, worker_key

    async def _find_reusable_worker_id_async(self, strategy) -> str:
        """
        异步查找可复用的离线 worker ID

        Args:
            strategy: HeartbeatConsumerStrategy 实例

        Returns:
            可复用的 worker ID，如果没有则返回 None
        """
        from jettask.worker.manager import WorkerNaming
        naming = WorkerNaming()
        return await naming.find_reusable_worker_id(
            prefix=strategy.hostname_prefix,
            worker_state=self.worker_state
        )

    def _start_heartbeat_thread_v2(self, worker_id: str, worker_key: str, queues: List[str] = None):
        """
        启动心跳线程

        Args:
            worker_id: Worker ID
            worker_key: Worker Redis key
            queues: Worker 负责的队列列表（用于消息恢复）

        Returns:
            HeartbeatThreadManager 实例
        """
        from jettask.worker.lifecycle import HeartbeatThreadManager

        heartbeat = HeartbeatThreadManager(
            redis_client=self.redis,
            worker_key=worker_key,
            worker_id=worker_id,
            redis_prefix=self.redis_prefix,
            interval=5.0
        )

        # 在启动心跳线程前设置 queues（确保第一次心跳就能写入 Redis）
        if queues:
            for queue in queues:
                heartbeat.queues.add(queue)
            logger.debug(f"Configured queues for heartbeat: {queues}")

        heartbeat.start()
        logger.info(f"Heartbeat thread started for worker {worker_id}")
        return heartbeat

    def _create_executor(self, concurrency: int):
        """
        创建进程编排器实例

        Returns:
            ProcessOrchestrator 实例
        """
        # 创建 ProcessOrchestrator（多进程管理器）
        orchestrator = ProcessOrchestrator(self, concurrency)

        # 保存 orchestrator 引用
        self._current_executor = orchestrator

        # 设置信号处理器
        def signal_handler(signum, frame):
            logger.info(f"Main process received signal {signum}, initiating shutdown...")
            self._should_exit = True
            orchestrator.shutdown_event.set()
            raise KeyboardInterrupt()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        return orchestrator

    def _cleanup_worker_v3(self, heartbeat_managers: list, executor, worker_ids: list):
        """
        清理 Worker 资源（新版本，支持多个心跳线程）
        """
        logger.info("Shutting down workers...")

        # 1. 停止所有心跳线程
        if heartbeat_managers:
            logger.info(f"Stopping {len(heartbeat_managers)} heartbeat threads...")
            for i, heartbeat in enumerate(heartbeat_managers):
                try:
                    worker_id = worker_ids[i][0] if i < len(worker_ids) else f"worker_{i}"
                    logger.debug(f"Stopping heartbeat thread for {worker_id}...")
                    heartbeat.stop(timeout=2.0)
                except Exception as e:
                    logger.error(f"Error stopping heartbeat #{i}: {e}", exc_info=True)

        # 2. 关闭执行器
        if executor:
            try:
                logger.debug("Shutting down executor...")
                executor.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down executor: {e}", exc_info=True)

        # 3. 关闭 Redis 连接
        try:
            logger.debug("Closing Redis connections...")
            self._cleanup_redis_connections_v2()
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}", exc_info=True)

        # 4. 调用通用清理
        try:
            self.cleanup()
        except Exception as e:
            logger.error(f"Error in cleanup: {e}", exc_info=True)

        logger.info(f"All {len(worker_ids)} workers shutdown complete")

    def _cleanup_redis_connections_v2(self):
        """清理 Redis 连接（异步包装）"""
        async def async_cleanup_redis():
            """异步关闭 Redis 连接"""
            try:
                logger.debug("Closing async Redis connections...")

                # 关闭 EventPool 的连接
                if hasattr(self.ep, 'async_redis_client'):
                    await self.ep.async_redis_client.aclose()

                if hasattr(self.ep, 'async_binary_redis_client'):
                    await self.ep.async_binary_redis_client.aclose()

                # 关闭 app 级别的连接
                if hasattr(self, '_async_redis'):
                    await self._async_redis.aclose()

                logger.debug("Async Redis connections closed")
            except Exception as e:
                logger.error(f"Error closing async Redis: {e}", exc_info=True)

        # 在新的事件循环中执行异步清理
        try:
            import asyncio
            cleanup_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(cleanup_loop)
            cleanup_loop.run_until_complete(async_cleanup_redis())
            cleanup_loop.close()
        except Exception as e:
            logger.error(f"Error in Redis cleanup: {e}", exc_info=True)


    def _start(self, queues: List[str] = None, concurrency: int = 1, prefetch_multiplier: int = 1):
        """
        启动 Worker 主逻辑（多进程模式，主进程调用）

        新架构流程：
        1. 为每个子进程生成独立的 Worker ID
        2. 在主进程为每个子进程启动独立的心跳线程
        3. 创建执行器
        4. Fork 并启动子进程，传递对应的 worker_id
        5. 等待退出信号（阻塞）
        6. 清理资源

        Args:
            queues: 监听的队列列表
            concurrency: 并发执行器进程数（子进程数量）
            prefetch_multiplier: 预取倍数
        """
        heartbeat_managers = []
        executor = None
        worker_ids = []

        try:
            # 1. 为每个子进程生成独立的 Worker ID 并启动心跳线程
            logger.info(f"Generating {concurrency} worker IDs and starting heartbeat threads...")
            from jettask.worker.lifecycle import HeartbeatThreadManager

            for i in range(concurrency):
                # 使用新方法：生成 worker_id 并启动心跳，等待首次心跳成功
                heartbeat = HeartbeatThreadManager.create_and_start(
                    redis_client=self.redis,
                    redis_prefix=self.redis_prefix,
                    queues=queues,
                    interval=5.0,
                    worker_state=self.worker_state
                )
                # 从心跳管理器对象中获取 worker_id 和 worker_key
                worker_ids.append((heartbeat.worker_id, heartbeat.worker_key))
                heartbeat_managers.append(heartbeat)
                logger.info(f"  Process #{i}: worker_id={heartbeat.worker_id} (heartbeat started)")

            # 2. 创建执行器
            executor = self._create_executor(concurrency)

            # 3. 启动 ProcessOrchestrator（阻塞调用，会fork多个子进程并运行）
            # 传递 worker_ids 列表，每个子进程使用对应的 worker_id
            logger.info(f"Starting {concurrency} executor processes...")

            executor.start(
                queues=queues,
                prefetch_multiplier=prefetch_multiplier,
                worker_ids=worker_ids  # 传递 worker_ids 列表
            )

        except KeyboardInterrupt:
            logger.info("Worker interrupted by keyboard")
        except Exception as e:
            logger.error(f"Error in worker main loop: {e}", exc_info=True)
        finally:
            # 5. 清理资源
            self._cleanup_worker_v3(heartbeat_managers, executor, worker_ids)

    # ==================== 旧方法（待废弃） ====================

    def _run_subprocess(self, *args, **kwargs):
        """已废弃：不再使用子进程"""
        _ = (args, kwargs)  # 避免未使用警告
        raise DeprecationWarning("_run_subprocess is deprecated, use _start_with_heartbeat_thread instead")

    def start(
        self,
        execute_type: str = "asyncio",
        queues: List[str] = None,
        concurrency: int = 1,
        prefetch_multiplier: int = 1,
        reload: bool = False,
    ):
        """启动 Worker（仅支持 multi_asyncio）"""
        _ = (reload, execute_type)  # 参数已废弃，避免未使用警告

        # 标记worker已启动
        self._worker_started = True

        # 如果配置了任务中心且配置尚未加载，从任务中心获取配置
        if self.task_center and self.task_center.is_enabled and not self._task_center_config:
            self._load_config_from_task_center()

        # 注册清理处理器（只在启动worker时注册）
        self._setup_cleanup_handlers()

        if self.consumer_strategy == "pod":
            raise ValueError("multi_asyncio模式下无法使用pod策略")

        # 使用重构后的 _start() 方法
        self._start(
            queues=queues,
            concurrency=concurrency,
            prefetch_multiplier=prefetch_multiplier,
        )


    def get_task_info(self, event_id: str, asyncio: bool = False):
        """获取任务信息（从TASK:hash）"""
        client = self.get_redis_client(asyncio)
        key = f"{self.redis_prefix}:TASK:{event_id}"
        if asyncio:
            return client.hgetall(key)
        else:
            return client.hgetall(key)
    
    def get_task_status(self, event_id: str, asyncio: bool = False):
        """获取任务状态（从TASK:hash的status字段）

        注意：这个方法使用简化的 key 格式 TASK:{event_id}
        如果需要获取带 group_name 的任务状态，请使用 _get_task_status_sync 或 _get_task_status_async
        """
        if asyncio:
            return self._get_task_status_simple_async(event_id)
        else:
            client = self.redis
            key = f"{self.redis_prefix}:TASK:{event_id}"
            return client.hget(key, "status")

    async def _get_task_status_simple_async(self, event_id: str):
        """异步获取任务状态（简化版本，不需要 task_name 和 queue）"""
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return await self.async_redis.hget(key, "status")

    def set_task_status(self, event_id: str, status: str, asyncio: bool = False):
        """设置任务状态（写入TASK:hash的status字段）"""
        if asyncio:
            return self._set_task_status_async(event_id, status)
        else:
            client = self.redis
            key = f"{self.redis_prefix}:TASK:{event_id}"
            return client.hset(key, "status", status)
    
    async def _set_task_status_async(self, event_id: str, status: str):
        """异步设置任务状态"""
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return await self.async_redis.hset(key, "status", status)

    def set_task_status_by_batch(self, mapping: dict, asyncio: bool = False):
        """批量设置任务状态（写入TASK:hash）"""
        if asyncio:
            return self._set_task_status_by_batch_async(mapping)
        else:
            pipeline = self.redis.pipeline()
            for event_id, status in mapping.items():
                key = f"{self.redis_prefix}:TASK:{event_id}"
                pipeline.hset(key, "status", status)
            return pipeline.execute()
    
    async def _set_task_status_by_batch_async(self, mapping: dict):
        """异步批量设置任务状态"""
        pipeline = self.async_redis.pipeline()
        for event_id, status in mapping.items():
            key = f"{self.redis_prefix}:TASK:{event_id}"
            pipeline.hset(key, "status", status)
        return await pipeline.execute()

    def del_task_status(self, event_id: str, asyncio: bool = False):
        """删除任务状态（删除整个TASK:hash）"""
        client = self.get_redis_client(asyncio)
        key = f"{self.redis_prefix}:TASK:{event_id}"
        return client.delete(key)

    def get_redis_client(self, asyncio: bool = False):
        return self.async_redis if asyncio else self.redis

    async def get_and_delayed_deletion(self, key: str, ex: int):
        """获取结果并延迟删除（从hash中）"""
        result = await self.async_redis.hget(key, "result")
        await self.async_redis.expire(key, ex)
        return result

    # ==================== 定时任务调度相关 ====================
    
    async def _ensure_scheduler_initialized(self, db_url: str = None):
        """确保调度器已初始化（内部方法）"""
        if not self.scheduler_manager:
            logger.debug("Auto-initializing scheduler...")
            # 优先使用传入的db_url，然后是实例化时的pg_url，最后是环境变量
            if not db_url:
                db_url = self.pg_url or os.environ.get('JETTASK_PG_URL')
            if not db_url:
                raise ValueError(
                    "Database URL not provided. Please provide pg_url when initializing Jettask, "
                    "or set JETTASK_PG_URL environment variable\n"
                    "Example: app = Jettask(redis_url='...', pg_url='postgresql://...')\n"
                    "Or: export JETTASK_PG_URL='postgresql://user:password@localhost:5432/jettask'"
                )
            
            from ..scheduler import TaskScheduler
            from ..scheduler.task_crud import ScheduledTaskManager
            
            # 创建数据库管理器
            self.scheduler_manager = ScheduledTaskManager(db_url)
            await self.scheduler_manager.connect()
            await self.scheduler_manager.init_schema()
            
            # 创建调度器
            scheduler_config = self.scheduler_config.copy()
            scheduler_config.setdefault('scan_interval', 0.1)
            scheduler_config.setdefault('batch_size', 100)
            scheduler_config.setdefault('leader_ttl', 10)
            
            self.scheduler = TaskScheduler(
                app=self,
                db_manager=self.scheduler_manager,
                **scheduler_config
            )
            
            await self.scheduler.connect()
            logger.debug("Scheduler initialized")
    
    async def start_scheduler(self):
        """启动定时任务调度器（自动初始化）"""
        # 自动初始化调度器
        await self._ensure_scheduler_initialized()
        
        try:
            await self.scheduler.run()
        except Exception as e:
            logger.error(f"Scheduler error: {e}", exc_info=True)
            raise
    
    def stop_scheduler(self):
        """停止定时任务调度器"""
        if self.scheduler:
            self.scheduler.stop()
            logger.debug("Scheduler stopped")
    
    async def add_scheduled_task(
        self,
        task_name: str,
        scheduler_id: str,  # 必填参数
        queue_name: str = None,
        task_type: str = "interval",
        interval_seconds: float = None,
        cron_expression: str = None,
        task_args: list = None,
        task_kwargs: dict = None,
        next_run_time: datetime = None,
        skip_if_exists: bool = True,
        at_once: bool = True,  # 是否立即保存到数据库
        **extra_params
    ):
        """
        添加定时任务
        
        Args:
            task_name: 要执行的函数名（必须对应已经通过@app.task注册的任务）
            scheduler_id: 任务的唯一标识符（必填，用于去重）
            queue_name: 目标队列名（可选，从task_name对应的任务自动获取）
            task_type: 任务类型 ('once', 'interval', 'cron')
            interval_seconds: 间隔秒数 (task_type='interval'时使用)
            cron_expression: Cron表达式 (task_type='cron'时使用)
            task_args: 任务参数列表
            task_kwargs: 任务关键字参数
            next_run_time: 首次执行时间 (task_type='once'时使用)
            skip_if_exists: 如果任务已存在是否跳过（默认True）
            at_once: 是否立即保存到数据库（默认True），如果False则返回任务对象用于批量写入
            **extra_params: 其他参数 (如 max_retries, timeout, description 等)
        """
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        from ..scheduler.models import ScheduledTask, TaskType
        
        # 尝试从已注册的任务中获取信息
        registered_task = None
        
        # 1. 直接匹配
        registered_task = self._tasks.get(task_name)
        
        # 2. 如果没找到，尝试查找以task_name结尾的任务（如 "module.task_name"）
        if not registered_task:
            for task_key, task_obj in self._tasks.items():
                if task_key.endswith(f".{task_name}") or task_key == task_name:
                    registered_task = task_obj
                    break
        
        if not registered_task:
            # 任务必须已注册
            available_tasks = list(self._tasks.keys())
            error_msg = f"Task '{task_name}' not found in registered tasks.\n"
            error_msg += "All scheduled tasks must be registered with @app.task decorator.\n"
            if available_tasks:
                error_msg += f"Available tasks: {', '.join(available_tasks)}"
            raise ValueError(error_msg)
        
        # 自动填充信息
        if not queue_name:
            queue_name = registered_task.queue or self.redis_prefix
        
        # 使用注册时的完整任务名称（包含模块前缀）
        # 查找任务的完整注册名称
        full_task_name = None
        for task_key, task_obj in self._tasks.items():
            if task_obj == registered_task:
                full_task_name = task_key
                break
        
        if not full_task_name:
            # 如果没找到，使用用户提供的名称
            full_task_name = task_name
        
        # 处理 next_run_time（主要用于 once 类型）
        if task_type == "once" and extra_params.get("next_run_time"):
            # 如果在 extra_params 中，移到正确位置
            next_run_time = extra_params.pop("next_run_time", None)
        
        # 移除不属于ScheduledTask的参数
        extra_params.pop("skip_if_exists", None)
        
        # scheduler_id是必填参数，必须由用户提供
        if not scheduler_id:
            raise ValueError("scheduler_id is required and must be provided")
        
        # 获取当前命名空间
        namespace = 'default'
        if self.task_center and hasattr(self.task_center, 'namespace_name'):
            namespace = self.task_center.namespace_name
        elif self.redis_prefix and self.redis_prefix != 'jettask':
            # 如果没有task_center，使用redis_prefix作为命名空间
            namespace = self.redis_prefix
        
        # 创建任务对象
        task = ScheduledTask(
            scheduler_id=scheduler_id,
            task_name=full_task_name,  # 使用完整的任务名称（包含模块前缀）
            task_type=TaskType(task_type),
            queue_name=queue_name,
            namespace=namespace,  # 设置命名空间
            task_args=task_args or [],
            task_kwargs=task_kwargs or {},
            interval_seconds=interval_seconds,
            cron_expression=cron_expression,
            next_run_time=next_run_time,
            **extra_params
        )
        
        # 如果不立即保存，返回任务对象供批量写入
        if not at_once:
            # 设置skip_if_exists标记供批量写入时使用
            task._skip_if_exists = skip_if_exists
            return task
        
        # 保存到数据库（支持去重）
        task, created = await self.scheduler_manager.create_or_get_task(task, skip_if_exists=skip_if_exists)
        
        if created:
            logger.debug(f"Scheduled task {task.id} created for function {task_name}")
        else:
            logger.debug(f"Scheduled task {task.id} already exists for function {task_name}")
        
        return task
    
    async def remove_scheduled_task(self, scheduler_id: str):
        """移除定时任务"""
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        # 先获取任务
        task = await self.scheduler_manager.get_task_by_scheduler_id(scheduler_id)
        if not task:
            return False
        
        success = await self.scheduler_manager.delete_task(task.id)
        
        if success and self.scheduler:
            # 从Redis中也移除
            await self.scheduler.loader.remove_task(task.id)
        
        return success
    
    async def batch_add_scheduled_tasks(
        self,
        tasks: list,
        skip_existing: bool = True
    ):
        """
        批量添加定时任务
        
        Args:
            tasks: 任务配置列表，每个元素是一个字典，包含add_scheduled_task的参数
            skip_existing: 是否跳过已存在的任务
            
        Returns:
            成功创建的任务列表
        """
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        from ..scheduler.models import ScheduledTask, TaskType
        
        task_objects = []
        for task_config in tasks:
            # 获取任务名称
            task_name = task_config.get('task_name')
            if not task_name:
                logger.warning("Task config missing task_name, skipping")
                continue
            
            # 查找注册的任务
            registered_task = self._tasks.get(task_name)
            if not registered_task:
                for task_key, task_obj in self._tasks.items():
                    if task_key.endswith(f".{task_name}") or task_key == task_name:
                        registered_task = task_obj
                        task_name = task_key  # 使用完整名称
                        break
            
            if not registered_task:
                logger.warning(f"Task '{task_name}' not found in registered tasks, skipping")
                continue
            
            # 准备任务参数
            queue_name = task_config.get('queue_name') or registered_task.queue or self.redis_prefix
            task_type = task_config.get('task_type', 'interval')
            
            # 处理next_run_time
            next_run_time = task_config.get('next_run_time')
            if task_type == 'once' and not next_run_time:
                next_run_time = datetime.now()
            
            # scheduler_id是必填参数
            scheduler_id = task_config.get('scheduler_id')
            if not scheduler_id:
                raise ValueError(f"Task config for '{task_name}' missing required scheduler_id")
            
            # 获取当前命名空间
            namespace = 'default'
            if self.task_center and hasattr(self.task_center, 'namespace_name'):
                namespace = self.task_center.namespace_name
            elif self.redis_prefix and self.redis_prefix != 'jettask':
                # 如果没有task_center，使用redis_prefix作为命名空间
                namespace = self.redis_prefix
            
            # 创建任务对象
            task_obj = ScheduledTask(
                scheduler_id=scheduler_id,
                task_name=task_name,
                task_type=TaskType(task_type),
                queue_name=queue_name,
                namespace=namespace,  # 设置命名空间
                task_args=task_config.get('task_args', []),
                task_kwargs=task_config.get('task_kwargs', {}),
                interval_seconds=task_config.get('interval_seconds'),
                cron_expression=task_config.get('cron_expression'),
                next_run_time=next_run_time,
                enabled=task_config.get('enabled', True),
                max_retries=task_config.get('max_retries', 3),
                retry_delay=task_config.get('retry_delay', 60),
                timeout=task_config.get('timeout', 300),
                description=task_config.get('description'),
                tags=task_config.get('tags', []),
                metadata=task_config.get('metadata', {})
            )
            task_objects.append(task_obj)
        
        # 批量创建
        created_tasks = await self.scheduler_manager.batch_create_tasks(task_objects, skip_existing)
        
        logger.debug(f"Batch created {len(created_tasks)} scheduled tasks")
        return created_tasks
    
    async def bulk_write_scheduled_tasks(self, tasks: list):
        """
        批量写入定时任务（配合at_once=False使用）
        
        使用示例：
            # 收集任务对象
            tasks = []
            for i in range(100):
                task = await app.add_scheduled_task(
                    task_name="my_task",
                    scheduler_id=f"task_{i}",
                    task_type="interval",
                    interval_seconds=30,
                    at_once=False  # 不立即保存
                )
                tasks.append(task)
            
            # 批量写入
            created_tasks = await app.bulk_write_scheduled_tasks(tasks)
        
        Args:
            tasks: 通过add_scheduled_task(at_once=False)创建的任务对象列表
        
        Returns:
            成功创建的任务列表
        """
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        if not tasks:
            return []
        
        # 准备批量创建的任务列表
        task_objects = []
        for task in tasks:
            if not hasattr(task, 'scheduler_id'):
                logger.warning("Invalid task object, skipping")
                continue
            
            
            task_objects.append(task)
        
        # 批量创建（使用第一个任务的skip_if_exists设置）
        skip_existing = getattr(tasks[0], '_skip_if_exists', True) if tasks else True
        created_tasks = await self.scheduler_manager.batch_create_tasks(task_objects, skip_existing)
        
        logger.debug(f"Bulk wrote {len(created_tasks)} scheduled tasks")
        return created_tasks
    
    async def list_scheduled_tasks(self, **filters):
        """列出定时任务"""
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        return await self.scheduler_manager.list_tasks(**filters)
    
    async def get_scheduled_task(self, scheduler_id: str):
        """获取定时任务详情"""
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        return await self.scheduler_manager.get_task_by_scheduler_id(scheduler_id)
    
    async def pause_scheduled_task(self, scheduler_id: str):
        """暂停/禁用定时任务"""
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        # 通过scheduler_id获取任务
        task = await self.scheduler_manager.get_task_by_scheduler_id(scheduler_id)
            
        if task:
            task.enabled = False
            await self.scheduler_manager.update_task(task)
            
            # 从Redis中移除
            if self.scheduler:
                await self.scheduler.loader.remove_task(task.id)
            
            logger.debug(f"Task {task.id} (scheduler_id: {task.scheduler_id}) disabled")
            return True
        return False
    
    async def resume_scheduled_task(self, scheduler_id: str):
        """恢复/启用定时任务"""
        # 自动初始化
        await self._ensure_scheduler_initialized()
        
        # 通过scheduler_id获取任务
        task = await self.scheduler_manager.get_task_by_scheduler_id(scheduler_id)
            
        if task:
            task.enabled = True
            task.next_run_time = task.calculate_next_run_time()
            await self.scheduler_manager.update_task(task)
            
            # 触发重新加载
            if self.scheduler:
                await self.scheduler.loader.load_tasks()
            
            logger.debug(f"Task {task.id} (scheduler_id: {task.scheduler_id}) enabled")
            return True
        return False
    
    # 别名，更直观
    async def disable_scheduled_task(self, scheduler_id: str):
        """禁用定时任务"""
        return await self.pause_scheduled_task(scheduler_id=scheduler_id)
    
    async def enable_scheduled_task(self, scheduler_id: str):
        """启用定时任务"""
        return await self.resume_scheduled_task(scheduler_id=scheduler_id)
    
