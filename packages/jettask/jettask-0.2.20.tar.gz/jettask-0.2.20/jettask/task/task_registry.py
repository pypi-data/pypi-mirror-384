"""
任务注册器

统一管理所有任务定义
"""

from typing import Dict, Callable, Optional, Any, Set
from dataclasses import dataclass, field
import logging

logger = logging.getLogger('app')


@dataclass
class TaskDefinition:
    """任务定义"""
    name: str
    func: Callable
    queue: str = 'default'
    max_retries: int = 3
    timeout: int = 300
    retry_delay: int = 60
    priority: int = 0
    options: dict = field(default_factory=dict)

    def __post_init__(self):
        """验证任务定义"""
        if not self.name:
            raise ValueError("Task name cannot be empty")
        if not callable(self.func):
            raise ValueError("Task func must be callable")
        if self.timeout <= 0:
            raise ValueError("Task timeout must be positive")


class TaskRegistry:
    """
    任务注册器

    职责：
    1. 任务注册和注销（本地内存）
    2. 任务查找
    3. 任务元数据管理
    4. Redis 任务注册（用于分布式发现）

    整合了：
    - TaskCenter的注册功能
    - RegistryManager的任务注册功能
    """

    def __init__(self, redis_client=None, async_redis_client=None, redis_prefix: str = 'jettask'):
        """初始化任务注册器

        Args:
            redis_client: 同步 Redis 客户端（可选，用于分布式注册）
            async_redis_client: 异步 Redis 客户端（可选，用于分布式注册）
            redis_prefix: Redis 键前缀
        """
        self.tasks: Dict[str, TaskDefinition] = {}
        self.redis = redis_client
        self.async_redis = async_redis_client
        self.redis_prefix = redis_prefix
        self.tasks_registry_key = f"{redis_prefix}:REGISTRY:TASKS"
        logger.debug("TaskRegistry initialized")

    def register(self,
                 name: str,
                 func: Callable,
                 queue: str = 'default',
                 **options) -> TaskDefinition:
        """
        注册任务

        Args:
            name: 任务名称
            func: 任务函数
            queue: 队列名称
            **options: 其他选项
                - max_retries: 最大重试次数
                - timeout: 超时时间（秒）
                - retry_delay: 重试延迟（秒）
                - priority: 优先级

        Returns:
            TaskDefinition: 任务定义
        """
        task_def = TaskDefinition(
            name=name,
            func=func,
            queue=queue,
            max_retries=options.get('max_retries', 3),
            timeout=options.get('timeout', 300),
            retry_delay=options.get('retry_delay', 60),
            priority=options.get('priority', 0),
            options=options
        )

        self.tasks[name] = task_def
        logger.info(f"Task registered: {name} -> queue: {queue}")

        return task_def

    def unregister(self, name: str) -> bool:
        """
        注销任务

        Args:
            name: 任务名称

        Returns:
            bool: 是否成功注销
        """
        if name in self.tasks:
            del self.tasks[name]
            logger.info(f"Task unregistered: {name}")
            return True

        logger.warning(f"Task not found for unregister: {name}")
        return False

    def get(self, name: str) -> Optional[TaskDefinition]:
        """
        获取任务定义

        Args:
            name: 任务名称

        Returns:
            Optional[TaskDefinition]: 任务定义，不存在返回None
        """
        return self.tasks.get(name)

    def exists(self, name: str) -> bool:
        """
        检查任务是否存在

        Args:
            name: 任务名称

        Returns:
            bool: 是否存在
        """
        return name in self.tasks

    def list_all(self) -> Dict[str, TaskDefinition]:
        """
        列出所有任务

        Returns:
            Dict[str, TaskDefinition]: 任务定义字典
        """
        return self.tasks.copy()

    def list_by_queue(self, queue: str) -> Dict[str, TaskDefinition]:
        """
        列出指定队列的所有任务

        Args:
            queue: 队列名称

        Returns:
            Dict[str, TaskDefinition]: 任务定义字典
        """
        return {
            name: task_def
            for name, task_def in self.tasks.items()
            if task_def.queue == queue
        }

    def update_options(self, name: str, **options) -> bool:
        """
        更新任务选项

        Args:
            name: 任务名称
            **options: 要更新的选项

        Returns:
            bool: 是否成功更新
        """
        if name not in self.tasks:
            logger.warning(f"Task not found for update: {name}")
            return False

        task_def = self.tasks[name]

        # 更新可修改的选项
        if 'max_retries' in options:
            task_def.max_retries = options['max_retries']
        if 'timeout' in options:
            task_def.timeout = options['timeout']
        if 'retry_delay' in options:
            task_def.retry_delay = options['retry_delay']
        if 'priority' in options:
            task_def.priority = options['priority']
        if 'queue' in options:
            task_def.queue = options['queue']

        # 更新options字典
        task_def.options.update(options)

        logger.info(f"Task options updated: {name}")
        return True

    def get_task_info(self, name: str) -> Optional[Dict[str, Any]]:
        """
        获取任务信息（不包含函数对象）

        Args:
            name: 任务名称

        Returns:
            Optional[Dict]: 任务信息字典
        """
        task_def = self.get(name)
        if not task_def:
            return None

        return {
            'name': task_def.name,
            'queue': task_def.queue,
            'max_retries': task_def.max_retries,
            'timeout': task_def.timeout,
            'retry_delay': task_def.retry_delay,
            'priority': task_def.priority,
            'options': task_def.options
        }

    def count(self) -> int:
        """
        获取注册的任务数量

        Returns:
            int: 任务数量
        """
        return len(self.tasks)

    def clear(self):
        """清空所有任务注册"""
        count = len(self.tasks)
        self.tasks.clear()
        logger.info(f"TaskRegistry cleared, {count} tasks removed")

    # ========== Redis 分布式注册功能（从 registry/manager.py 迁移） ==========

    async def register_task_to_redis(self, task_name: str):
        """注册任务到 Redis（用于分布式发现）

        Args:
            task_name: 任务名称
        """
        if not self.async_redis:
            logger.warning("Redis client not configured, skipping Redis registration")
            return

        await self.async_redis.sadd(self.tasks_registry_key, task_name)
        logger.debug(f"Registered task to Redis: {task_name}")

    async def unregister_task_from_redis(self, task_name: str):
        """从 Redis 注销任务

        Args:
            task_name: 任务名称
        """
        if not self.async_redis:
            return

        await self.async_redis.srem(self.tasks_registry_key, task_name)
        logger.debug(f"Unregistered task from Redis: {task_name}")

    async def get_all_tasks_from_redis(self) -> Set[str]:
        """从 Redis 获取所有任务（不使用 SCAN）

        Returns:
            Set[str]: 任务名称集合
        """
        if not self.async_redis:
            return set()

        return await self.async_redis.smembers(self.tasks_registry_key)

    async def get_task_count_from_redis(self) -> int:
        """从 Redis 获取任务数量

        Returns:
            int: 任务数量
        """
        if not self.async_redis:
            return 0

        return await self.async_redis.scard(self.tasks_registry_key)
