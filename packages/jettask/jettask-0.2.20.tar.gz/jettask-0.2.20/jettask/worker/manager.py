"""
Worker 管理器

整合了 Worker 相关的所有核心功能:
- Worker 状态管理（注册、查询、统计）
- Worker ID 生成和命名
- 消费者名称管理
"""

import os
import uuid
import logging
import time
from typing import Dict, Any, Optional, List, Set

logger = logging.getLogger('app')


class WorkerState:
    """
    Worker 状态管理器

    负责 Worker 在 Redis 中的状态数据管理:
    - Worker 注册和注销
    - Worker 列表查询
    - Worker 按任务查询
    - Worker 数量统计

    注：之前叫 WorkerRegistry，现在改名为 WorkerState 更准确反映其职责
    """

    def __init__(self, redis_client, async_redis_client, redis_prefix: str = 'jettask'):
        """
        初始化 Worker 状态管理器

        Args:
            redis_client: 同步 Redis 客户端
            async_redis_client: 异步 Redis 客户端
            redis_prefix: Redis 键前缀
        """
        self.redis = redis_client
        self.async_redis = async_redis_client
        self.redis_prefix = redis_prefix
        self.workers_registry_key = f"{redis_prefix}:REGISTRY:WORKERS"

    # ========== Worker 注册管理 ==========

    async def register_worker(self, worker_id: str):
        """注册 Worker 到全局注册表"""
        await self.async_redis.sadd(self.workers_registry_key, worker_id)
        logger.debug(f"Registered worker: {worker_id}")

    async def unregister_worker(self, worker_id: str):
        """从全局注册表注销 Worker"""
        await self.async_redis.srem(self.workers_registry_key, worker_id)
        logger.debug(f"Unregistered worker: {worker_id}")

    async def get_all_workers(self) -> Set[str]:
        """获取所有已注册的 Worker ID"""
        return await self.async_redis.smembers(self.workers_registry_key)

    def get_all_workers_sync(self) -> Set[str]:
        """同步方式获取所有已注册的 Worker ID"""
        return self.redis.smembers(self.workers_registry_key)

    async def get_worker_count(self) -> int:
        """获取已注册的 Worker 总数"""
        return await self.async_redis.scard(self.workers_registry_key)

    async def get_offline_workers(self) -> Set[str]:
        """获取所有离线的 Worker ID

        离线 Worker 是指已注册但 is_alive=false 的 Worker
        """
        all_workers = await self.get_all_workers()
        offline_workers = set()

        for worker_id in all_workers:
            if isinstance(worker_id, bytes):
                worker_id = worker_id.decode('utf-8')

            worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"
            is_alive = await self.async_redis.hget(worker_key, 'is_alive')

            if is_alive:
                is_alive = is_alive.decode('utf-8') if isinstance(is_alive, bytes) else is_alive
                if is_alive != 'true':
                    offline_workers.add(worker_id)
            else:
                # Worker key 不存在或没有 is_alive 字段，认为离线
                offline_workers.add(worker_id)

        return offline_workers

    async def get_workers_for_task(self, task_name: str, only_alive: bool = True) -> Set[str]:
        """获取执行特定任务的 Worker 列表

        通过检查 WORKER:* hash 中的 group_info 字段来判断哪些 Worker 在处理该任务

        Args:
            task_name: 任务名称
            only_alive: 是否只返回在线的 Worker（默认 True）

        Returns:
            处理该任务的 Worker ID 集合
        """
        all_worker_ids = await self.get_all_workers()
        matched_workers = set()
        group_info_prefix = f"group_info:{self.redis_prefix}:QUEUE:"

        for worker_id in all_worker_ids:
            if isinstance(worker_id, bytes):
                worker_id = worker_id.decode('utf-8')

            worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"
            worker_info = await self.async_redis.hgetall(worker_key)

            if not worker_info:
                continue

            # 解码 bytes keys
            decoded_info = {}
            for k, v in worker_info.items():
                key = k.decode('utf-8') if isinstance(k, bytes) else k
                val = v.decode('utf-8') if isinstance(v, bytes) else v
                decoded_info[key] = val

            # 检查 is_alive 状态
            if only_alive:
                is_alive = decoded_info.get('is_alive', 'false')
                if is_alive != 'true':
                    continue

            # 检查是否包含该任务的 group_info
            # 格式: group_info:test5:QUEUE:robust_bench2:benchmark_task
            for key in decoded_info.keys():
                if key.startswith(group_info_prefix):
                    parts = key.split(':')
                    if len(parts) >= 5:
                        worker_task_name = parts[-1]  # 最后一部分是 task_name
                        if worker_task_name == task_name:
                            matched_workers.add(worker_id)
                            break

        return matched_workers

    async def get_active_worker_count_for_task(self, task_name: str) -> int:
        """获取执行特定任务的在线 Worker 数量

        Args:
            task_name: 任务名称

        Returns:
            在线 Worker 数量
        """
        workers = await self.get_workers_for_task(task_name, only_alive=True)
        return len(workers)

    async def find_offline_workers_for_queue(
        self,
        queue: str,
        worker_prefix: str = 'WORKER',
        worker_state_manager=None
    ) -> List[tuple]:
        """查找指定队列的离线 Worker

        查找条件：
        1. Worker 已离线（is_alive=false）
        2. 消息未转移（messages_transferred=false）
        3. Worker 负责该队列

        Args:
            queue: 队列名称（支持优先级队列格式：queue:priority）
            worker_prefix: Worker 键前缀（默认 'WORKER'）
            worker_state_manager: WorkerStateManager 实例（可选，用于读取 worker 信息）

        Returns:
            离线 Worker 列表，每项为 (worker_key, worker_data) 元组
        """
        offline_workers = []

        try:
            # 获取所有 worker ID
            worker_ids = await self.get_all_workers()
            logger.debug(f"[Recovery] Found {len(worker_ids)} workers in registry for queue {queue}")

            for worker_id in worker_ids:
                # 解码 worker_id（可能是 bytes）
                if isinstance(worker_id, bytes):
                    worker_id = worker_id.decode('utf-8')

                # 构建 worker key
                worker_key = f"{self.redis_prefix}:{worker_prefix}:{worker_id}"

                try:
                    # 读取 worker 信息
                    if worker_state_manager:
                        decoded_worker_data = await worker_state_manager.get_worker_info(worker_id)
                    else:
                        worker_data = await self.async_redis.hgetall(worker_key)
                        if not worker_data:
                            continue

                        # 解码二进制数据
                        decoded_worker_data = {}
                        for k, v in worker_data.items():
                            key = k.decode('utf-8') if isinstance(k, bytes) else k
                            value = v.decode('utf-8') if isinstance(v, bytes) else v
                            decoded_worker_data[key] = value

                    if not decoded_worker_data:
                        continue

                    # 检查 worker 是否离线且消息未转移
                    is_alive = decoded_worker_data.get('is_alive', 'false') == 'true'
                    messages_transferred = decoded_worker_data.get('messages_transferred', 'false') == 'true'

                    # 找到离线且消息未转移的 worker
                    if not is_alive and not messages_transferred:
                        queues_str = decoded_worker_data.get('queues', '')
                        worker_queues = queues_str.split(',') if queues_str else []

                        # 检查这个 worker 是否负责当前队列
                        # 支持优先级队列：如果 queue 是 "base:priority" 格式，检查 worker 是否负责 base 队列
                        queue_matched = False
                        if ':' in queue and queue.rsplit(':', 1)[-1].isdigit():
                            # 这是优先级队列，提取基础队列名
                            base_queue = queue.rsplit(':', 1)[0]
                            queue_matched = base_queue in worker_queues
                        else:
                            # 普通队列
                            queue_matched = queue in worker_queues

                        if queue_matched:
                            logger.info(
                                f"Found offline worker needing recovery: {worker_id}, "
                                f"queues={worker_queues}, is_alive={is_alive}, "
                                f"messages_transferred={messages_transferred}"
                            )
                            offline_workers.append((worker_key, decoded_worker_data))
                        else:
                            logger.debug(
                                f"Worker {worker_id} is offline but not responsible for queue {queue} "
                                f"(worker_queues={worker_queues})"
                            )

                except Exception as e:
                    logger.error(f"Error processing worker key {worker_key}: {e}")
                    continue

        except Exception as e:
            logger.error(f"Error finding offline workers: {e}")

        return offline_workers


class WorkerNaming:
    """
    Worker ID 生成和复用

    职责：
    - 生成唯一的 Worker ID
    - 查找可复用的离线 Worker ID
    """

    def generate_worker_id(self, prefix: str) -> str:
        """
        生成新的 Worker ID

        格式: {prefix}-{uuid}-{pid}
        例如: YYDG-a1b2c3d4-12345

        Args:
            prefix: Worker ID 前缀（通常是主机名）

        Returns:
            生成的 Worker ID
        """
        return f"{prefix}-{uuid.uuid4().hex[:8]}-{os.getpid()}"

    async def find_reusable_worker_id(
        self,
        prefix: str,
        worker_state: 'WorkerState'
    ) -> Optional[str]:
        """
        查找可复用的离线 Worker ID

        Args:
            prefix: Worker ID 前缀
            worker_state: Worker 状态管理器实例

        Returns:
            可复用的 Worker ID，如果没有则返回 None
        """
        try:
            offline_workers = await worker_state.get_offline_workers()

            for worker_id in offline_workers:
                if isinstance(worker_id, bytes):
                    worker_id = worker_id.decode('utf-8')
                if worker_id.startswith(prefix):
                    logger.debug(f"Found reusable worker ID: {worker_id}")
                    return worker_id
        except Exception as e:
            logger.warning(f"Error finding reusable worker ID: {e}")

        return None


class ConsumerManager:
    """消费者名称管理器

    使用 HEARTBEAT 心跳策略管理消费者名称
    """

    def __init__(
        self,
        redis_client,
        config: Dict[str, Any] = None,
        app=None
    ):
        self.redis_client = redis_client
        self.config = config or {}
        self._consumer_name = None
        self.app = app

        # Redis prefix configuration
        self.redis_prefix = config.get('redis_prefix', 'jettask')

        # 心跳策略实例 - 由外部传入 lifecycle 实例
        self._heartbeat_strategy = None

    def set_heartbeat_strategy(self, heartbeat_strategy):
        """设置心跳策略实例（由外部注入）"""
        self._heartbeat_strategy = heartbeat_strategy

    def get_prefixed_queue_name(self, queue: str) -> str:
        """为队列名称添加前缀"""
        return f"{self.redis_prefix}:QUEUE:{queue}"

    def get_consumer_name(self, queue: str) -> str:
        """获取消费者名称（使用 HEARTBEAT 策略）"""
        return self._get_heartbeat_name(queue)

    def _get_heartbeat_name(self, queue: str) -> str:
        """基于心跳策略获取消费者名称"""
        if not self._heartbeat_strategy:
            raise RuntimeError("Heartbeat strategy not initialized properly")

        return self._heartbeat_strategy.get_consumer_name(queue)

    async def record_group_info_async(self, queue: str, task_name: str, group_name: str, consumer_name: str):
        """异步记录task的group信息到worker hash表

        Args:
            queue: 队列名
            task_name: 任务名
            group_name: consumer group名称
            consumer_name: consumer名称
        """
        if not self._heartbeat_strategy:
            return

        try:
            # 确保 consumer_id 已初始化
            self._heartbeat_strategy._ensure_consumer_id()
            worker_id = self._heartbeat_strategy.consumer_id
            worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"

            # 构建group信息
            import json
            group_info = {
                'queue': queue,
                'task_name': task_name,
                'group_name': group_name,
                'consumer_name': consumer_name,
                'stream_key': f"{self.redis_prefix}:QUEUE:{queue}"
            }

            # 将group信息存储到worker的hash中
            # 使用 group_info:{group_name} 作为field
            field_name = f"group_info:{group_name}"

            # 使用app的async_redis客户端
            if self.app and hasattr(self.app, 'async_redis'):
                await self.app.async_redis.hset(
                    worker_key,
                    field_name,
                    json.dumps(group_info)
                )
                logger.debug(f"Recorded group info for task {task_name}: {group_info}")
            else:
                logger.warning("Cannot record group info: async_redis not available")

        except Exception as e:
            logger.error(f"Error recording task group info: {e}")

    async def get_workers_for_task(self, task_name: str, only_alive: bool = True) -> Set[str]:
        """获取执行特定任务的 Worker 列表

        委托给 WorkerState 来实现

        Args:
            task_name: 任务名称
            only_alive: 是否只返回在线的 Worker（默认 True）

        Returns:
            处理该任务的 Worker ID 集合
        """
        # 通过 app 获取 WorkerState 实例
        if self.app and hasattr(self.app, 'worker_state'):
            worker_state = self.app.worker_state
            return await worker_state.get_workers_for_task(task_name, only_alive)

        # 降级方案：返回空集合
        logger.debug(f"Cannot get workers for task {task_name}: WorkerState not available")
        return set()

    def cleanup(self):
        """清理资源（优雅关闭时调用）"""
        if self._heartbeat_strategy:
            self._heartbeat_strategy.cleanup()


class WorkerManager:
    """
    Worker 管理器 - 统一入口

    这是推荐的 Worker 管理方式，提供:
    - 职责清晰的接口
    - 简洁的代码结构
    - 易于测试和维护

    使用示例：
        manager = WorkerManager(redis, async_redis, 'jettask')
        worker_id = await manager.start_worker('MyApp', ['queue1'])
        await manager.record_task_start(worker_id, 'queue1')
        await manager.record_task_finish(worker_id, 'queue1', True, 1.5)
        await manager.stop_worker(worker_id)
    """

    def __init__(
        self,
        redis_client,
        async_redis_client,
        redis_prefix: str = 'jettask'
    ):
        """
        初始化 Worker 管理器

        Args:
            redis_client: 同步 Redis 客户端
            async_redis_client: 异步 Redis 客户端
            redis_prefix: Redis 键前缀
        """
        self.redis_client = redis_client
        self.async_redis_client = async_redis_client
        self.redis_prefix = redis_prefix

        # 初始化各个组件
        self.worker_state = WorkerState(
            redis_client=redis_client,
            async_redis_client=async_redis_client,
            redis_prefix=redis_prefix
        )

        self.naming = WorkerNaming()

        # lifecycle 组件将在下一步创建
        self.lifecycle = None

        # 为了兼容性，保留 registry 别名（指向 worker_state）
        self.registry = self.worker_state

        logger.debug("WorkerManager initialized")

    async def start_worker(
        self,
        prefix: str,
        queues: List[str],
        reuse_offline: bool = True
    ) -> str:
        """
        启动一个 Worker

        Args:
            prefix: Worker ID 前缀（推荐使用应用名或主机名）
            queues: Worker 负责的队列列表
            reuse_offline: 是否复用离线的 Worker ID（默认True）

        Returns:
            启动的 Worker ID

        Example:
            worker_id = await manager.start_worker('MyApp', ['queue1', 'queue2'])
        """
        if not self.lifecycle:
            raise RuntimeError("Lifecycle manager not initialized")

        return await self.lifecycle.initialize_worker(prefix, queues, reuse_offline)

    async def stop_worker(self, worker_id: str):
        """
        停止一个 Worker

        Args:
            worker_id: 要停止的 Worker ID

        Example:
            await manager.stop_worker(worker_id)
        """
        if not self.lifecycle:
            raise RuntimeError("Lifecycle manager not initialized")

        await self.lifecycle.cleanup_worker(worker_id)

    async def record_task_start(self, worker_id: str, queue: str):
        """
        记录任务开始

        Args:
            worker_id: Worker ID
            queue: 队列名称

        Example:
            await manager.record_task_start(worker_id, 'queue1')
        """
        if not self.lifecycle:
            raise RuntimeError("Lifecycle manager not initialized")

        await self.lifecycle.record_task_start(worker_id, queue)

    async def record_task_finish(
        self,
        worker_id: str,
        queue: str,
        success: bool,
        duration: float
    ):
        """
        记录任务完成

        Args:
            worker_id: Worker ID
            queue: 队列名称
            success: 是否成功
            duration: 处理耗时（秒）

        Example:
            await manager.record_task_finish(worker_id, 'queue1', True, 1.5)
        """
        if not self.lifecycle:
            raise RuntimeError("Lifecycle manager not initialized")

        await self.lifecycle.record_task_finish(worker_id, queue, success, duration)

    async def get_worker_info(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """
        获取 Worker 信息

        Args:
            worker_id: Worker ID

        Returns:
            Worker 信息字典，如果不存在则返回 None

        Example:
            info = await manager.get_worker_info(worker_id)
            print(f"Worker {worker_id} is {'online' if info['is_alive']=='true' else 'offline'}")
        """
        if not self.lifecycle:
            raise RuntimeError("Lifecycle manager not initialized")

        return await self.lifecycle.get_worker_info(worker_id)


__all__ = [
    'WorkerState',      # Worker 状态管理（之前叫 WorkerRegistry）
    'WorkerNaming',     # Worker ID 生成
    'ConsumerManager',  # 消费者名称管理
    'WorkerManager',    # 统一管理器
]
