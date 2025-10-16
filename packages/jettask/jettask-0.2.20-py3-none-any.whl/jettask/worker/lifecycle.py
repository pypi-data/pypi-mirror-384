"""
Worker 生命周期管理

整合了以下模块的功能:
- state_manager.py: Worker 状态管理
- heartbeat_thread.py: 心跳线程管理
- scanner.py: Worker 超时扫描
- core.py: WorkerLifecycle, WorkerStatistics
- consumer_manager.py: HeartbeatConsumerStrategy 的心跳和统计逻辑
"""

import os
import socket
import uuid
import time
import asyncio
import logging
import threading
import json
from typing import Dict, List, Optional, Set, Callable, Any
from collections import defaultdict, namedtuple
from redis.asyncio.lock import Lock as AsyncLock
import redis
import redis.asyncio as aioredis

logger = logging.getLogger(__name__)


# ============================================================================
# Worker 状态管理
# ============================================================================

class WorkerStateManager:
    """Worker状态管理器 - Worker状态的唯一管理入口

    ⚠️ 重要：所有Worker状态的修改都必须通过这个类进行，不要直接操作Redis！

    职责:
    1. 统一管理worker所有状态字段的读写
    2. 当关键状态变更时，通过Redis Pub/Sub发送信号
    3. 提供状态变更监听机制
    4. 维护worker在ACTIVE_WORKERS sorted set中的记录
    """

    def __init__(self, redis_client: aioredis.Redis, redis_prefix: str = "jettask", event_pool=None):
        """初始化Worker状态管理器

        Args:
            redis_client: 异步Redis客户端
            redis_prefix: Redis key前缀
            event_pool: EventPool实例（可选），用于事件驱动的消息恢复
        """
        self.redis = redis_client
        self.redis_prefix = redis_prefix
        self.active_workers_key = f"{redis_prefix}:ACTIVE_WORKERS"
        self.event_pool = event_pool

        # Pub/Sub通道名称
        self.worker_state_channel = f"{redis_prefix}:WORKER_STATE_CHANGE"

        # 监听器订阅
        self._pubsub = None
        self._listener_task: Optional[asyncio.Task] = None
        self._running = False
        self._callbacks: Set[Callable] = set()

        # Pub/Sub 配置
        self._health_check_interval = 60
        self._health_check_task: Optional[asyncio.Task] = None

    def _get_worker_key(self, worker_id: str) -> str:
        """获取worker的Redis key"""
        return f"{self.redis_prefix}:WORKER:{worker_id}"

    async def initialize_worker(self, worker_id: str, worker_info: Dict[str, Any]):
        """初始化worker（首次创建）"""
        worker_key = self._get_worker_key(worker_id)
        current_time = time.time()

        worker_info.setdefault('is_alive', 'true')
        worker_info.setdefault('messages_transferred', 'false')
        worker_info.setdefault('created_at', str(current_time))
        worker_info.setdefault('last_heartbeat', str(current_time))

        pipeline = self.redis.pipeline()
        pipeline.hset(worker_key, mapping=worker_info)
        pipeline.zadd(self.active_workers_key, {worker_id: current_time})
        await pipeline.execute()

        logger.debug(f"Initialized worker {worker_id}")

    async def set_worker_online(self, worker_id: str, worker_data: dict = None):
        """设置worker为在线状态"""
        worker_key = self._get_worker_key(worker_id)
        old_alive = await self.redis.hget(worker_key, 'is_alive')
        old_alive = old_alive.decode('utf-8') if isinstance(old_alive, bytes) else old_alive

        current_time = time.time()
        pipeline = self.redis.pipeline()
        pipeline.hset(worker_key, 'is_alive', 'true')
        pipeline.hset(worker_key, 'last_heartbeat', str(current_time))

        # 当 worker 从离线变为在线时，重置 messages_transferred
        # 这表示是一个新的 worker 实例，还没有进行消息转移
        if old_alive != 'true':
            pipeline.hset(worker_key, 'messages_transferred', 'false')

        if worker_data:
            pipeline.hset(worker_key, mapping=worker_data)

        pipeline.zadd(self.active_workers_key, {worker_id: current_time})
        await pipeline.execute()

        if old_alive != 'true':
            await self._publish_state_change(worker_id, 'online')
            logger.debug(f"Worker {worker_id} is now ONLINE")

    async def set_worker_offline(self, worker_id: str, reason: str = "unknown"):
        """设置worker为离线状态"""
        worker_key = self._get_worker_key(worker_id)
        old_alive = await self.redis.hget(worker_key, 'is_alive')
        old_alive = old_alive.decode('utf-8') if isinstance(old_alive, bytes) else old_alive

        current_time = time.time()
        pipeline = self.redis.pipeline()
        pipeline.hset(worker_key, 'messages_transferred', 'false')  # 重置消息转移标记，允许其他worker接管消息
        pipeline.hset(worker_key, 'is_alive', 'false')
        pipeline.hset(worker_key, 'offline_reason', reason)
        pipeline.hset(worker_key, 'offline_time', str(current_time))
        pipeline.zrem(self.active_workers_key, worker_id)
        await pipeline.execute()

        if old_alive == 'true':
            await self._publish_state_change(worker_id, 'offline', reason)
            logger.debug(f"Worker {worker_id} is now OFFLINE (reason: {reason})")

    async def update_worker_heartbeat(self, worker_id: str, heartbeat_data: dict = None):
        """更新worker心跳（确保在线状态）"""
        worker_key = self._get_worker_key(worker_id)
        current_time = time.time()

        pipeline = self.redis.pipeline()
        pipeline.hset(worker_key, 'is_alive', 'true')
        pipeline.hset(worker_key, 'last_heartbeat', str(current_time))

        if heartbeat_data:
            pipeline.hset(worker_key, mapping=heartbeat_data)

        pipeline.zadd(self.active_workers_key, {worker_id: current_time})
        await pipeline.execute()

    async def update_worker_field(self, worker_id: str, field: str, value: str):
        """更新worker的单个字段"""
        worker_key = self._get_worker_key(worker_id)
        await self.redis.hset(worker_key, field, value)

    async def update_worker_fields(self, worker_id: str, fields: Dict[str, Any]):
        """批量更新worker的多个字段"""
        worker_key = self._get_worker_key(worker_id)
        await self.redis.hset(worker_key, mapping=fields)

    async def increment_queue_stats(self, worker_id: str, queue: str,
                                   running_tasks_delta: int = None,
                                   success_count_increment: int = None,
                                   failed_count_increment: int = None,
                                   total_count_increment: int = None,
                                   processing_time_increment: float = None,
                                   latency_time_increment: float = None):
        """增量更新worker在特定队列上的累积统计信息"""
        worker_key = self._get_worker_key(worker_id)
        pipeline = self.redis.pipeline()

        if running_tasks_delta is not None and running_tasks_delta != 0:
            pipeline.hincrby(worker_key, f'{queue}:running_tasks', running_tasks_delta)

        if success_count_increment is not None:
            pipeline.hincrby(worker_key, f'{queue}:success_count', success_count_increment)

        if failed_count_increment is not None:
            pipeline.hincrby(worker_key, f'{queue}:failed_count', failed_count_increment)

        if total_count_increment is not None:
            pipeline.hincrby(worker_key, f'{queue}:total_count', total_count_increment)

        if processing_time_increment is not None:
            pipeline.hincrbyfloat(worker_key, f'{queue}:total_processing_time', processing_time_increment)

        if latency_time_increment is not None:
            pipeline.hincrbyfloat(worker_key, f'{queue}:total_latency_time', latency_time_increment)

        await pipeline.execute()

    async def get_queue_total_stats(self, worker_id: str, queue: str) -> dict:
        """获取队列的累积统计数据"""
        worker_key = self._get_worker_key(worker_id)
        fields = [
            f'{queue}:total_count',
            f'{queue}:total_processing_time',
            f'{queue}:total_latency_time'
        ]
        values = await self.redis.hmget(worker_key, fields)

        return {
            'total_count': int(values[0]) if values[0] else 0,
            'total_processing_time': float(values[1]) if values[1] else 0.0,
            'total_latency_time': float(values[2]) if values[2] else 0.0
        }

    async def update_queue_stats(self, worker_id: str, queue: str,
                                 running_tasks: int = None,
                                 avg_processing_time: float = None,
                                 avg_latency_time: float = None):
        """更新worker在特定队列上的统计信息"""
        worker_key = self._get_worker_key(worker_id)
        pipeline = self.redis.pipeline()

        if running_tasks is not None:
            pipeline.hset(worker_key, f'{queue}:running_tasks', str(running_tasks))

        if avg_processing_time is not None:
            pipeline.hset(worker_key, f'{queue}:avg_processing_time', f'{avg_processing_time:.3f}')

        if avg_latency_time is not None:
            pipeline.hset(worker_key, f'{queue}:avg_latency_time', f'{avg_latency_time:.3f}')

        await pipeline.execute()

    async def mark_messages_transferred(self, worker_id: str, transferred: bool = True):
        """标记worker的消息是否已转移"""
        worker_key = self._get_worker_key(worker_id)
        await self.redis.hset(worker_key, 'messages_transferred', 'true' if transferred else 'false')

    async def get_worker_info(self, worker_id: str) -> Optional[Dict[str, str]]:
        """获取worker的完整信息"""
        worker_key = self._get_worker_key(worker_id)
        data = await self.redis.hgetall(worker_key)

        if not data:
            return None

        result = {}
        for k, v in data.items():
            key = k.decode('utf-8') if isinstance(k, bytes) else k
            value = v.decode('utf-8') if isinstance(v, bytes) else v
            result[key] = value

        return result

    async def get_worker_field(self, worker_id: str, field: str) -> Optional[str]:
        """获取worker的单个字段值"""
        worker_key = self._get_worker_key(worker_id)
        value = await self.redis.hget(worker_key, field)

        if value is None:
            return None

        return value.decode('utf-8') if isinstance(value, bytes) else value

    async def is_worker_alive(self, worker_id: str) -> bool:
        """检查worker是否在线"""
        is_alive = await self.get_worker_field(worker_id, 'is_alive')
        return is_alive == 'true'

    async def get_all_workers_info(self, only_alive: bool = True) -> Dict[str, Dict[str, str]]:
        """获取所有worker的信息"""
        pattern = f"{self.redis_prefix}:WORKER:*"
        result = {}

        cursor = 0
        while True:
            cursor, keys = await self.redis.scan(cursor, match=pattern, count=100)

            for key in keys:
                if isinstance(key, bytes):
                    key = key.decode('utf-8')

                parts = key.split(":")
                if len(parts) >= 3:
                    worker_id = parts[2]
                    worker_info = await self.get_worker_info(worker_id)
                    if worker_info:
                        if only_alive and worker_info.get('is_alive') != 'true':
                            continue
                        result[worker_id] = worker_info

            if cursor == 0:
                break

        return result

    async def delete_worker(self, worker_id: str):
        """删除worker的所有数据"""
        worker_key = self._get_worker_key(worker_id)
        pipeline = self.redis.pipeline()
        pipeline.delete(worker_key)
        pipeline.zrem(self.active_workers_key, worker_id)
        await pipeline.execute()
        logger.debug(f"Deleted worker {worker_id}")

    async def _publish_state_change(self, worker_id: str, state: str, reason: str = None):
        """发布状态变更信号"""
        message = {
            'worker_id': worker_id,
            'state': state,
            'timestamp': asyncio.get_event_loop().time()
        }

        if reason:
            message['reason'] = reason

        await self.redis.publish(
            self.worker_state_channel,
            json.dumps(message)
        )

        logger.debug(f"Published state change: {message}")

    async def start_listener(self):
        """启动状态变更监听器"""
        if self._running:
            logger.warning("Worker state listener already running")
            return

        self._running = True
        self._pubsub = await self._create_and_subscribe_pubsub()
        self._listener_task = asyncio.create_task(self._listen_loop())
        self._health_check_task = asyncio.create_task(self._health_check_loop())

        logger.debug(f"Started worker state listener on channel: {self.worker_state_channel}")

    async def stop_listener(self):
        """停止状态变更监听器"""
        if not self._running:
            return

        self._running = False

        if self._listener_task:
            self._listener_task.cancel()
            try:
                await self._listener_task
            except asyncio.CancelledError:
                pass

        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass

        if self._pubsub:
            await self._pubsub.unsubscribe(self.worker_state_channel)
            await self._pubsub.close()

        logger.debug("Stopped worker state listener")

    async def _create_and_subscribe_pubsub(self):
        """创建 PubSub 连接并订阅频道"""
        if self._pubsub:
            try:
                await self._pubsub.close()
            except:
                pass

        pubsub = self.redis.pubsub()
        await pubsub.subscribe(self.worker_state_channel)

        logger.debug(f"Created and subscribed to Redis Pub/Sub channel: {self.worker_state_channel}")
        return pubsub

    async def _health_check_loop(self):
        """定期检查 Pub/Sub 连接健康状态"""
        while self._running:
            try:
                await asyncio.sleep(self._health_check_interval)

                if not self._running:
                    break

                if self._pubsub and self._pubsub.connection:
                    try:
                        await asyncio.wait_for(self._pubsub.ping(), timeout=5.0)
                        logger.debug("Pub/Sub health check: OK")
                    except Exception as e:
                        logger.warning(f"Pub/Sub health check failed: {e}")
                else:
                    logger.warning("Pub/Sub connection is None")

            except asyncio.CancelledError:
                logger.debug("Health check loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in health check loop: {e}")

    async def _listen_loop(self):
        """监听循环（支持自动重连）"""
        retry_delay = 1
        max_retry_delay = 30

        while self._running:
            try:
                async for message in self._pubsub.listen():
                    if message['type'] == 'message':
                        try:
                            data = json.loads(message['data'])

                            if data.get('state') == 'offline' and self.event_pool:
                                worker_id = data.get('worker_id')
                                if worker_id:
                                    logger.info(f"[StateManager] Worker {worker_id} offline event received")
                                    asyncio.create_task(
                                        self.event_pool.handle_worker_offline_event(worker_id)
                                    )

                            for callback in self._callbacks:
                                try:
                                    if asyncio.iscoroutinefunction(callback):
                                        await callback(data)
                                    else:
                                        callback(data)
                                except Exception as e:
                                    logger.error(f"Error in state change callback: {e}")

                        except Exception as e:
                            logger.error(f"Error processing state change message: {e}")

                retry_delay = 1

            except asyncio.CancelledError:
                logger.debug("Listen loop cancelled")
                break
            except Exception as e:
                logger.error(f"Error in listen loop: {e}")

                if not self._running:
                    break

                logger.warning(f"Attempting to reconnect to Redis Pub/Sub in {retry_delay} seconds...")
                await asyncio.sleep(retry_delay)

                try:
                    self._pubsub = await self._create_and_subscribe_pubsub()
                    logger.info(f"Successfully reconnected to Redis Pub/Sub")
                    retry_delay = 1
                except Exception as reconnect_error:
                    logger.error(f"Failed to reconnect to Redis Pub/Sub: {reconnect_error}")
                    retry_delay = min(retry_delay * 2, max_retry_delay)

        logger.debug("Listen loop exited")

    def register_callback(self, callback: Callable):
        """注册状态变更回调"""
        self._callbacks.add(callback)
        logger.debug(f"Registered state change callback: {callback.__name__}")

    def unregister_callback(self, callback: Callable):
        """注销状态变更回调"""
        self._callbacks.discard(callback)
        logger.debug(f"Unregistered state change callback: {callback.__name__}")


# ============================================================================
# 心跳管理
# ============================================================================

class HeartbeatTaskManager:
    """基于协程的心跳管理器（在主进程的独立事件循环线程中运行，轻量级）"""

    def __init__(self, redis_client, worker_key: str, worker_id: str, redis_prefix: str,
                 interval: float = 5.0, heartbeat_timeout: float = 15.0, loop: asyncio.AbstractEventLoop = None):
        """初始化心跳任务管理器

        Args:
            redis_client: 异步 Redis 客户端
            worker_key: Worker 的 Redis key
            worker_id: Worker ID
            redis_prefix: Redis 前缀
            interval: 心跳间隔（秒）
            heartbeat_timeout: 心跳超时时间（秒）
            loop: 事件循环（如果为None，会在当前线程创建新的）
        """
        self.redis_client = redis_client
        self.worker_key = worker_key
        self.worker_id = worker_id
        self.redis_prefix = redis_prefix
        self.interval = interval
        self.heartbeat_timeout = heartbeat_timeout
        self.queues: Set[str] = set()
        self._last_heartbeat_time = None
        self._loop = loop

        # 心跳任务和停止事件
        self._task: Optional[asyncio.Task] = None
        self._stop_event: Optional[asyncio.Event] = None
        self._first_heartbeat_done: Optional[asyncio.Event] = None
        self._thread: Optional[threading.Thread] = None
        self._thread_ready: Optional[threading.Event] = None

    @classmethod
    async def create_and_start(cls, redis_client, redis_prefix: str, queues: List[str] = None,
                               interval: float = 5.0, worker_state=None):
        """
        创建心跳管理器并启动，生成 worker_id 后等待首次心跳成功

        Args:
            redis_client: 异步 Redis 客户端
            redis_prefix: Redis 前缀
            queues: 队列列表
            interval: 心跳间隔
            worker_state: WorkerState 实例（用于查找可复用的 worker_id）

        Returns:
            HeartbeatTaskManager 实例（包含 worker_id 和 worker_key 属性）
        """
        from jettask.worker.manager import WorkerNaming

        # 1. 生成 worker_id
        naming = WorkerNaming()

        # 生成主机名前缀
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            prefix = hostname if hostname != 'localhost' else ip
        except:
            prefix = os.environ.get('HOSTNAME', 'unknown')

        # 尝试复用离线的 worker_id
        reusable_id = None
        if worker_state:
            reusable_id = await naming.find_reusable_worker_id(prefix=prefix, worker_state=worker_state)

        # 生成或复用 worker_id
        if reusable_id:
            worker_id = reusable_id
            logger.info(f"[PID {os.getpid()}] Reusing offline worker ID: {worker_id}")
        else:
            worker_id = naming.generate_worker_id(prefix)
            logger.info(f"[PID {os.getpid()}] Generated new worker ID: {worker_id}")

        worker_key = f"{redis_prefix}:WORKER:{worker_id}"

        # 2. 创建心跳管理器
        manager = cls(
            redis_client=redis_client,
            worker_key=worker_key,
            worker_id=worker_id,
            redis_prefix=redis_prefix,
            interval=interval
        )

        # 3. 设置队列
        if queues:
            for queue in queues:
                manager.queues.add(queue)

        # 4. 启动心跳任务
        await manager.start()

        # 5. 等待首次心跳成功（最多等待 10 秒）
        try:
            await asyncio.wait_for(manager._first_heartbeat_done.wait(), timeout=10)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout waiting for first heartbeat for worker {worker_id}")

        logger.info(f"Heartbeat task started for worker {worker_id}")
        return manager

    async def start(self):
        """启动心跳任务"""
        if self._task and not self._task.done():
            logger.warning("Heartbeat task already running")
            return

        self._stop_event = asyncio.Event()
        self._first_heartbeat_done = asyncio.Event()
        self._task = asyncio.create_task(self._heartbeat_loop())

    async def stop(self):
        """停止心跳任务"""
        if not self._task:
            return

        logger.debug(f"Stopping heartbeat task for worker {self.worker_id}")
        self._stop_event.set()

        try:
            await asyncio.wait_for(self._task, timeout=2.0)
        except asyncio.TimeoutError:
            logger.warning("Heartbeat task did not stop in time, cancelling...")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

        logger.debug("Heartbeat task stopped")

    async def _heartbeat_loop(self):
        """心跳循环（在协程中运行）"""
        hostname = socket.gethostname()
        pid = str(os.getpid())

        logger.info(f"Heartbeat task starting for worker {self.worker_id}")

        heartbeat_count = 0
        last_log_time = time.time()
        first_heartbeat = True

        while not self._stop_event.is_set():
            try:
                current_time = time.time()

                needs_full_init = False
                publish_online_signal = False

                old_alive = await self.redis_client.hget(self.worker_key, 'is_alive')
                consumer_id = await self.redis_client.hget(self.worker_key, 'consumer_id')

                if not consumer_id:
                    needs_full_init = True
                    publish_online_signal = True
                    logger.warning(f"Worker {self.worker_id} key missing critical fields, reinitializing...")
                elif first_heartbeat and old_alive != b'true' and old_alive != 'true':
                    publish_online_signal = True

                # 标记首次心跳完成
                if first_heartbeat:
                    first_heartbeat = False

                if needs_full_init:
                    worker_info = {
                        'consumer_id': self.worker_id,
                        'host': hostname,
                        'pid': pid,
                        'created_at': str(current_time),
                        'last_heartbeat': str(current_time),
                        'is_alive': 'true',
                        'messages_transferred': 'false',
                        'heartbeat_timeout': str(self.heartbeat_timeout),
                    }

                    if self.queues:
                        worker_info['queues'] = ','.join(sorted(self.queues))

                    await self.redis_client.hset(self.worker_key, mapping=worker_info)
                    logger.info(f"Reinitialized worker {self.worker_id} with full info")
                else:
                    # 构建心跳更新数据
                    heartbeat_update = {
                        'last_heartbeat': str(current_time),
                        'is_alive': 'true',
                        'host': hostname
                    }

                    # 如果是从离线变为在线（复用worker ID），重置 messages_transferred
                    if publish_online_signal:
                        heartbeat_update['messages_transferred'] = 'false'
                        logger.debug(f"Worker {self.worker_id} reused, reset messages_transferred=false")

                    await self.redis_client.hset(self.worker_key, mapping=heartbeat_update)

                await self.redis_client.zadd(
                    f"{self.redis_prefix}:ACTIVE_WORKERS",
                    {self.worker_id: current_time}
                )

                if publish_online_signal:
                    state_change_channel = f"{self.redis_prefix}:WORKER_STATE_CHANGE"
                    message = json.dumps({
                        'worker_id': self.worker_id,
                        'state': 'online',
                        'timestamp': current_time
                    })
                    result = await self.redis_client.publish(state_change_channel, message)
                    logger.info(f"Worker {self.worker_id} is now ONLINE, published to {result} subscribers")

                workers_registry_key = f"{self.redis_prefix}:REGISTRY:WORKERS"
                await self.redis_client.sadd(workers_registry_key, self.worker_id)

                self._last_heartbeat_time = current_time
                heartbeat_count += 1

                # 如果这是首次心跳，通知等待的协程
                if heartbeat_count == 1:
                    self._first_heartbeat_done.set()
                    logger.debug(f"First heartbeat completed for worker {self.worker_id}")

                if current_time - last_log_time >= 30:
                    logger.debug(f"Heartbeat task: sent {heartbeat_count} heartbeats for worker {self.worker_id}")
                    last_log_time = current_time
                    heartbeat_count = 0

            except Exception as e:
                logger.error(f"Error in heartbeat task: {e}", exc_info=True)

            # 等待下一次心跳
            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval)
                break  # 如果停止事件被设置，退出循环
            except asyncio.TimeoutError:
                pass  # 超时是正常的，继续下一次心跳

        logger.info(f"Heartbeat task stopped for worker {self.worker_id}")

    async def mark_offline(self, reason: str = "shutdown"):
        """标记 worker 为离线状态"""
        try:
            current_time = time.time()
            state_change_channel = f"{self.redis_prefix}:WORKER_STATE_CHANGE"

            pipeline = self.redis_client.pipeline()
            pipeline.hset(self.worker_key, 'is_alive', 'false')
            pipeline.hset(self.worker_key, 'offline_reason', reason)
            pipeline.hset(self.worker_key, 'offline_time', str(current_time))
            pipeline.hset(self.worker_key, 'messages_transferred', 'false')
            pipeline.zrem(f"{self.redis_prefix}:ACTIVE_WORKERS", self.worker_id)

            message = json.dumps({
                'worker_id': self.worker_id,
                'state': 'offline',
                'reason': reason,
                'timestamp': current_time
            })
            pipeline.publish(state_change_channel, message)
            await pipeline.execute()

            logger.info(f"Worker {self.worker_id} marked as offline (reason: {reason})")
        except Exception as e:
            logger.error(f"Error marking worker offline: {e}", exc_info=True)


class HeartbeatThreadManager:
    """基于线程的心跳管理器（在 CLI 主进程中运行）"""

    def __init__(self, redis_client=None, worker_key=None, worker_id=None, redis_prefix=None,
                 interval=5.0, redis_url=None, consumer_id=None, heartbeat_interval=None,
                 heartbeat_timeout=15.0):
        """初始化心跳线程管理器"""
        if redis_url is not None:
            from jettask.utils.db_connector import get_sync_redis_client
            self.redis_client = get_sync_redis_client(redis_url, decode_responses=True)
            self.redis_url = redis_url
            self.consumer_id = consumer_id
            self.heartbeat_interval = heartbeat_interval or 5.0
            self.heartbeat_timeout = heartbeat_timeout
            self.worker_key = None
            self.worker_id = None
            self.redis_prefix = redis_prefix
            self.interval = self.heartbeat_interval
            self.queues: Set[str] = set()
            self._last_heartbeat_time = None
            self._last_heartbeat_time_lock = threading.Lock()
        else:
            self.redis_client = redis_client
            self.worker_key = worker_key
            self.worker_id = worker_id
            self.redis_prefix = redis_prefix
            self.interval = interval
            self.redis_url = None
            self.consumer_id = worker_id
            self.heartbeat_interval = interval
            self.heartbeat_timeout = 15.0
            self.queues: Set[str] = set()
            self._last_heartbeat_time = None
            self._last_heartbeat_time_lock = threading.Lock()

        self._stop_event = threading.Event()
        self._thread = None
        self.heartbeat_process = self

        # 用于等待首次心跳的事件
        self._first_heartbeat_done = threading.Event()

    @classmethod
    def create_and_start(cls, redis_client, redis_prefix: str, queues: List[str] = None,
                        interval: float = 5.0, worker_state=None):
        """
        创建心跳管理器并启动，生成 worker_id 后等待首次心跳成功

        Args:
            redis_client: Redis 客户端
            redis_prefix: Redis 前缀
            queues: 队列列表
            interval: 心跳间隔
            worker_state: WorkerState 实例（用于查找可复用的 worker_id）

        Returns:
            HeartbeatThreadManager 实例（包含 worker_id 和 worker_key 属性）
        """
        from jettask.worker.manager import WorkerNaming

        # 1. 生成 worker_id
        naming = WorkerNaming()

        # 生成主机名前缀
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            prefix = hostname if hostname != 'localhost' else ip
        except:
            prefix = os.environ.get('HOSTNAME', 'unknown')

        # 尝试复用离线的 worker_id（同步方式）
        reusable_id = None
        if worker_state:
            import asyncio
            try:
                loop = asyncio.get_event_loop()
                if not loop.is_running():
                    reusable_id = loop.run_until_complete(
                        naming.find_reusable_worker_id(prefix=prefix, worker_state=worker_state)
                    )
            except RuntimeError:
                # 没有事件循环，创建新的
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    reusable_id = loop.run_until_complete(
                        naming.find_reusable_worker_id(prefix=prefix, worker_state=worker_state)
                    )
                finally:
                    loop.close()

        # 生成或复用 worker_id
        if reusable_id:
            worker_id = reusable_id
            logger.info(f"[PID {os.getpid()}] Reusing offline worker ID: {worker_id}")
        else:
            worker_id = naming.generate_worker_id(prefix)
            logger.info(f"[PID {os.getpid()}] Generated new worker ID: {worker_id}")

        worker_key = f"{redis_prefix}:WORKER:{worker_id}"

        # 2. 创建心跳管理器
        manager = cls(
            redis_client=redis_client,
            worker_key=worker_key,
            worker_id=worker_id,
            redis_prefix=redis_prefix,
            interval=interval
        )

        # 3. 设置队列
        if queues:
            for queue in queues:
                manager.queues.add(queue)

        # 4. 启动心跳线程
        manager.start()

        # 5. 等待首次心跳成功（最多等待 10 秒）
        if not manager._first_heartbeat_done.wait(timeout=10):
            logger.warning(f"Timeout waiting for first heartbeat for worker {worker_id}")

        # 返回管理器对象，调用方可以通过 manager.worker_id 和 manager.worker_key 访问
        return manager

    def start(self):
        """启动心跳线程"""
        if self._thread and self._thread.is_alive():
            logger.warning("Heartbeat thread already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            name=f"Heartbeat-{self.worker_id}",
            daemon=True
        )
        self._thread.start()
        logger.info(f"Heartbeat thread started for worker {self.worker_id}")

    def stop(self, timeout=2.0):
        """停止心跳线程"""
        if not self._thread:
            return

        logger.debug(f"Stopping heartbeat thread for worker {self.worker_id}")
        self._stop_event.set()
        self._thread.join(timeout=timeout)

        if self._thread.is_alive():
            logger.warning("Heartbeat thread did not stop in time")
        else:
            logger.debug("Heartbeat thread stopped")

    def _heartbeat_loop(self):
        """心跳循环（在线程中运行）"""
        hostname = socket.gethostname()
        pid = str(os.getpid())

        logger.info(f"Heartbeat thread starting for worker {self.worker_id}")

        heartbeat_count = 0
        last_log_time = time.time()
        first_heartbeat = True

        while not self._stop_event.is_set():
            try:
                current_time = time.time()

                needs_full_init = False
                publish_online_signal = False

                old_alive = self.redis_client.hget(self.worker_key, 'is_alive')
                consumer_id = self.redis_client.hget(self.worker_key, 'consumer_id')

                if not consumer_id:
                    needs_full_init = True
                    publish_online_signal = True
                    logger.warning(f"Worker {self.worker_id} key missing critical fields, reinitializing...")
                elif first_heartbeat and old_alive != 'true':
                    publish_online_signal = True

                # 标记首次心跳完成（在第一次心跳逻辑执行后）
                if first_heartbeat:
                    first_heartbeat = False

                if needs_full_init:
                    worker_info = {
                        'consumer_id': self.worker_id,
                        'host': hostname,
                        'pid': pid,
                        'created_at': str(current_time),
                        'last_heartbeat': str(current_time),
                        'is_alive': 'true',
                        'messages_transferred': 'false',
                        'heartbeat_timeout': str(self.heartbeat_timeout),
                    }

                    if self.queues:
                        worker_info['queues'] = ','.join(sorted(self.queues))

                    self.redis_client.hset(self.worker_key, mapping=worker_info)
                    logger.info(f"Reinitialized worker {self.worker_id} with full info")
                else:
                    # 构建心跳更新数据
                    heartbeat_update = {
                        'last_heartbeat': str(current_time),
                        'is_alive': 'true',
                        'host': hostname
                    }

                    # 如果是从离线变为在线（复用worker ID），重置 messages_transferred
                    if publish_online_signal:
                        heartbeat_update['messages_transferred'] = 'false'
                        logger.debug(f"Worker {self.worker_id} reused, reset messages_transferred=false")

                    self.redis_client.hset(self.worker_key, mapping=heartbeat_update)

                self.redis_client.zadd(
                    f"{self.redis_prefix}:ACTIVE_WORKERS",
                    {self.worker_id: current_time}
                )

                if publish_online_signal:
                    state_change_channel = f"{self.redis_prefix}:WORKER_STATE_CHANGE"
                    message = json.dumps({
                        'worker_id': self.worker_id,
                        'state': 'online',
                        'timestamp': current_time
                    })
                    result = self.redis_client.publish(state_change_channel, message)
                    logger.info(f"Worker {self.worker_id} is now ONLINE, published to {result} subscribers")

                workers_registry_key = f"{self.redis_prefix}:REGISTRY:WORKERS"
                self.redis_client.sadd(workers_registry_key, self.worker_id)

                with self._last_heartbeat_time_lock:
                    self._last_heartbeat_time = current_time

                heartbeat_count += 1

                # 如果这是首次心跳，通知等待的线程
                if heartbeat_count == 1:
                    self._first_heartbeat_done.set()
                    logger.debug(f"First heartbeat completed for worker {self.worker_id}")

                if current_time - last_log_time >= 30:
                    logger.debug(f"Heartbeat thread: sent {heartbeat_count} heartbeats for worker {self.worker_id}")
                    last_log_time = current_time
                    heartbeat_count = 0

            except Exception as e:
                logger.error(f"Error in heartbeat thread: {e}", exc_info=True)
                if "Timeout connecting" in str(e) or "Connection" in str(e):
                    try:
                        self.redis_client.close()
                    except:
                        pass
                    try:
                        if self.redis_url:
                            from jettask.utils.db_connector import get_sync_redis_client
                            self.redis_client = get_sync_redis_client(
                                redis_url=self.redis_url,
                                decode_responses=True,
                            )
                            logger.info(f"Reconnected to Redis for heartbeat thread {self.worker_id}")
                    except Exception as reconnect_error:
                        logger.error(f"Failed to reconnect Redis: {reconnect_error}")
                time.sleep(5)

            self._stop_event.wait(timeout=self.interval)

        logger.info(f"Heartbeat thread exiting for worker {self.worker_id}")
        try:
            current_time = time.time()
            pipeline = self.redis_client.pipeline()
            pipeline.hset(self.worker_key, mapping={
                'is_alive': 'false',
                'offline_time': str(current_time),
                'shutdown_reason': 'heartbeat_stopped',
                'messages_transferred': 'false'
            })

            state_change_channel = f"{self.redis_prefix}:WORKER_STATE_CHANGE"
            message = json.dumps({
                'worker_id': self.worker_id,
                'state': 'offline',
                'timestamp': current_time
            })
            pipeline.publish(state_change_channel, message)
            pipeline.execute()

            logger.info(f"Worker {self.worker_id} marked as offline")
        except Exception as e:
            logger.error(f"Error marking worker offline: {e}", exc_info=True)

    def add_queue(self, queue: str, worker_key: str):
        """添加队列"""
        self.queues.add(queue)

        if self.worker_key is None:
            self.worker_key = worker_key
            parts = worker_key.split(':')
            if len(parts) >= 3:
                self.redis_prefix = parts[0]
                self.worker_id = parts[2]
            else:
                logger.error(f"Invalid worker_key format: {worker_key}")
                raise ValueError(f"Invalid worker_key format: {worker_key}")

        if self._thread is not None and self._thread.is_alive():
            logger.debug(f"Heartbeat thread already running, added queue {queue}")
            return

        self.start()
        logger.debug(f"Started single heartbeat thread for worker {self.worker_id}")

    def remove_queue(self, queue: str):
        """移除队列"""
        if queue in self.queues:
            self.queues.remove(queue)
            logger.debug(f"Removed queue {queue} from heartbeat monitoring")

            if not self.queues:
                self.stop()
                logger.debug("No more queues, stopped heartbeat thread")

    def stop_all(self):
        """停止心跳线程"""
        self.stop()
        self.queues.clear()

    def is_healthy(self) -> bool:
        """检查心跳线程是否健康"""
        if not self._thread:
            return len(self.queues) == 0

        if not self._thread.is_alive():
            logger.error(f"Heartbeat thread for worker {self.worker_id} is not alive")
            return False
        return True

    def get_last_heartbeat_time(self) -> Optional[float]:
        """获取最后一次心跳时间"""
        with self._last_heartbeat_time_lock:
            return self._last_heartbeat_time

    def is_heartbeat_timeout(self) -> bool:
        """检查心跳是否已超时"""
        last_heartbeat = self.get_last_heartbeat_time()
        if last_heartbeat is None:
            return False

        current_time = time.time()
        return (current_time - last_heartbeat) > self.heartbeat_timeout


# ============================================================================
# Worker 扫描器
# ============================================================================

class WorkerScanner:
    """使用 Redis Sorted Set 优化的 Worker 扫描器

    核心优化：
    1. O(log N) 的超时检测复杂度
    2. 自动一致性维护
    3. 原子性操作保证数据一致
    """

    def __init__(self, sync_redis, async_redis, redis_prefix: str = 'jettask',
                 heartbeat_timeout: float = 3.0, worker_prefix: str = 'WORKER',
                 worker_state_manager=None):
        self.redis = sync_redis
        self.async_redis = async_redis
        self.redis_prefix = redis_prefix
        self.worker_prefix = worker_prefix
        self.heartbeat_timeout = heartbeat_timeout
        self.active_workers_key = f"{redis_prefix}:ACTIVE_WORKERS"
        self.worker_state_manager = worker_state_manager

        self._initialized = False
        self._last_full_sync = 0
        self._full_sync_interval = 60
        self._scan_counter = 0
        self._partial_check_interval = 10

    async def scan_timeout_workers(self) -> List[Dict]:
        """快速扫描超时的 worker - O(log N) 复杂度"""
        self._scan_counter += 1
        if self._scan_counter >= self._partial_check_interval:
            self._scan_counter = 0
            asyncio.create_task(self._partial_check())

        current_time = time.time()
        max_possible_timeout = 300
        cutoff_time = current_time - max_possible_timeout

        potential_timeout_worker_ids = await self.async_redis.zrangebyscore(
            self.active_workers_key,
            min=0,
            max=current_time - 1
        )

        if not potential_timeout_worker_ids:
            return []

        if self.worker_state_manager:
            all_workers_info = await self.worker_state_manager.get_all_workers_info(only_alive=False)
            workers_data = [all_workers_info.get(wid) for wid in potential_timeout_worker_ids]
        else:
            pipeline = self.async_redis.pipeline()
            for worker_id in potential_timeout_worker_ids:
                worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"
                pipeline.hgetall(worker_key)
            workers_data = await pipeline.execute()

        result = []
        cleanup_pipeline = self.async_redis.pipeline()
        need_cleanup = False

        for worker_id, worker_data in zip(potential_timeout_worker_ids, workers_data):
            if not worker_data:
                cleanup_pipeline.zrem(self.active_workers_key, worker_id)
                workers_registry_key = f"{self.redis_prefix}:REGISTRY:WORKERS"
                cleanup_pipeline.srem(workers_registry_key, worker_id)
                need_cleanup = True
                continue

            worker_heartbeat_timeout = float(worker_data.get('heartbeat_timeout', self.heartbeat_timeout))
            last_heartbeat = float(worker_data.get('last_heartbeat', 0))
            worker_cutoff_time = current_time - worker_heartbeat_timeout

            if last_heartbeat >= worker_cutoff_time:
                cleanup_pipeline.zadd(self.active_workers_key, {worker_id: last_heartbeat})
                need_cleanup = True
                continue

            is_alive = worker_data.get('is_alive', 'true') == 'true' if self.worker_state_manager else worker_data.get('is_alive', 'true').lower() == 'true'
            if not is_alive:
                cleanup_pipeline.zrem(self.active_workers_key, worker_id)
                need_cleanup = True
                continue

            logger.debug(f"Worker {worker_id} timeout: last_heartbeat={last_heartbeat}, timeout={worker_heartbeat_timeout}s")
            worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"
            result.append({
                'worker_key': worker_key,
                'worker_data': worker_data,
                'worker_id': worker_id
            })

        if need_cleanup:
            await cleanup_pipeline.execute()

        if result:
            logger.info(f"Found {len(result)} timeout workers")

        return result

    async def update_heartbeat(self, worker_id: str, heartbeat_time: Optional[float] = None):
        """原子性更新心跳"""
        if heartbeat_time is None:
            heartbeat_time = time.time()

        pipeline = self.async_redis.pipeline()
        worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"

        pipeline.hset(worker_key, 'last_heartbeat', str(heartbeat_time))
        pipeline.zadd(self.active_workers_key, {worker_id: heartbeat_time})

        await pipeline.execute()

    async def add_worker(self, worker_id: str, worker_data: Dict):
        """添加新 worker"""
        heartbeat_time = float(worker_data.get('last_heartbeat', time.time()))

        pipeline = self.async_redis.pipeline()
        worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"

        pipeline.hset(worker_key, mapping=worker_data)
        pipeline.zadd(self.active_workers_key, {worker_id: heartbeat_time})

        await pipeline.execute()
        logger.debug(f"Added worker {worker_id} to system")

    async def remove_worker(self, worker_id: str):
        """移除 worker"""
        if self.worker_state_manager:
            await self.worker_state_manager.set_worker_offline(worker_id, reason="heartbeat_timeout")
        else:
            pipeline = self.async_redis.pipeline()
            worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"

            pipeline.hset(worker_key, 'is_alive', 'false')
            pipeline.zrem(self.active_workers_key, worker_id)

            await pipeline.execute()
            logger.debug(f"Removed worker {worker_id} from active set (direct mode)")

        if self.worker_state_manager:
            await self.async_redis.zrem(self.active_workers_key, worker_id)

    async def cleanup_stale_workers(self, max_age_seconds: float = 3600):
        """清理过期的 worker 记录"""
        current_time = time.time()
        cutoff_time = current_time - max_age_seconds

        stale_worker_ids = await self.async_redis.zrangebyscore(
            self.active_workers_key,
            min=0,
            max=cutoff_time
        )

        if not stale_worker_ids:
            return 0

        pipeline = self.async_redis.pipeline()

        for worker_id in stale_worker_ids:
            worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"
            pipeline.delete(worker_key)

        pipeline.zrem(self.active_workers_key, *stale_worker_ids)

        await pipeline.execute()

        logger.info(f"Cleaned up {len(stale_worker_ids)} stale worker records")
        return len(stale_worker_ids)

    async def _partial_check(self):
        """部分一致性检查"""
        try:
            sample_size = min(10, await self.async_redis.zcard(self.active_workers_key))
            if sample_size == 0:
                return

            random_workers = await self.async_redis.zrandmember(
                self.active_workers_key, sample_size, withscores=True
            )

            for worker_id, zset_score in random_workers:
                worker_key = f"{self.redis_prefix}:{self.worker_prefix}:{worker_id}"
                hash_heartbeat = await self.async_redis.hget(worker_key, 'last_heartbeat')

                if not hash_heartbeat:
                    await self.async_redis.zrem(self.active_workers_key, worker_id)
                    logger.debug(f"Partial check: removed {worker_id}")
                else:
                    hash_time = float(hash_heartbeat)
                    if abs(hash_time - zset_score) > 1.0:
                        await self.async_redis.zadd(self.active_workers_key, {worker_id: hash_time})
                        logger.debug(f"Partial check: synced {worker_id}")

        except Exception as e:
            logger.debug(f"Partial check error: {e}")

    async def get_active_count(self) -> int:
        """获取活跃 worker 数量 - O(1)"""
        return await self.async_redis.zcard(self.active_workers_key)


# ============================================================================
# Worker 生命周期
# ============================================================================

class WorkerLifecycle:
    """Worker 生命周期管理

    职责：
    - 初始化 Worker（生成ID、注册、启动心跳）
    - 清理 Worker（停止心跳、注销、离线标记）
    """

    def __init__(
        self,
        redis_client,
        async_redis_client,
        redis_prefix: str,
        naming: 'WorkerNaming',
        state_manager: 'WorkerStateManager',
        registry: 'WorkerRegistry',
        heartbeat_class
    ):
        """初始化生命周期管理器"""
        self.redis_client = redis_client
        self.async_redis_client = async_redis_client
        self.redis_prefix = redis_prefix
        self.naming = naming
        self.state = state_manager
        self.registry = registry
        self.heartbeat_class = heartbeat_class
        self.active_heartbeats: Dict[str, Any] = {}

    async def initialize_worker(
        self,
        prefix: str,
        queues: List[str],
        reuse_offline: bool = True
    ) -> str:
        """初始化 Worker"""
        worker_id = None
        if reuse_offline:
            worker_id = await self.naming.find_reusable_worker_id(prefix, self.registry)

        if not worker_id:
            worker_id = self.naming.generate_worker_id(prefix)

        logger.info(f"Initializing worker: {worker_id}")

        await self.state.set_worker_online(
            worker_id=worker_id,
            queues=queues,
            pid=os.getpid(),
            host=socket.gethostname()
        )

        await self.registry.register(worker_id)

        worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"
        heartbeat = self.heartbeat_class(
            redis_client=self.redis_client,
            worker_key=worker_key,
            worker_id=worker_id,
            redis_prefix=self.redis_prefix,
            interval=5.0
        )

        for queue in queues:
            heartbeat.queues.add(queue)

        heartbeat.start()
        self.active_heartbeats[worker_id] = heartbeat

        logger.info(f"Worker initialized successfully: {worker_id}")
        return worker_id

    async def cleanup_worker(self, worker_id: str):
        """清理 Worker 资源"""
        logger.info(f"Cleaning up worker: {worker_id}")

        try:
            if worker_id in self.active_heartbeats:
                heartbeat = self.active_heartbeats[worker_id]
                heartbeat.stop()
                del self.active_heartbeats[worker_id]

            await self.state.set_worker_offline(worker_id)
            await self.registry.unregister(worker_id)

            logger.info(f"Worker cleaned up successfully: {worker_id}")
        except Exception as e:
            logger.error(f"Error cleaning up worker {worker_id}: {e}")
            raise

    async def record_task_start(self, worker_id: str, queue: str):
        """记录任务开始"""
        await self.state.increment_queue_stats(
            worker_id=worker_id,
            queue=queue,
            running_tasks_delta=1
        )

    async def record_task_finish(
        self,
        worker_id: str,
        queue: str,
        success: bool,
        duration: float
    ):
        """记录任务完成"""
        await self.state.increment_queue_stats(
            worker_id=worker_id,
            queue=queue,
            running_tasks_delta=-1,
            success_count_increment=1 if success else 0,
            failed_count_increment=0 if success else 1,
            total_count_increment=1,
            processing_time_increment=duration
        )

        # 更新平均处理时间
        stats = await self.state.get_queue_total_stats(worker_id, queue)
        if stats['total_count'] > 0:
            avg_time = stats['total_processing_time'] / stats['total_count']
            await self.state.update_queue_stats(
                worker_id=worker_id,
                queue=queue,
                avg_processing_time=avg_time
            )

    async def get_worker_info(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """获取 Worker 信息"""
        return await self.state.get_worker_info(worker_id)


# ============================================================================
# 兼容性层：HeartbeatConsumerStrategy (for backward compatibility)
# ============================================================================

class HeartbeatConsumerStrategy:
    """
    兼容性类 - 为旧代码提供向后兼容

    ⚠️ 已废弃: 请使用 WorkerManager 和 WorkerNaming 代替
    """

    def __init__(self, redis_client, config: Dict = None, app=None):
        self.redis = redis_client
        self.config = config or {}
        self.app = app
        self.redis_prefix = config.get('redis_prefix', 'jettask')

        # 如果 app 传入了 worker_id，直接使用（子进程复用主进程的ID）
        if app and hasattr(app, 'worker_id') and app.worker_id:
            self.consumer_id = app.worker_id
            self._worker_key = app.worker_key or f'{self.redis_prefix}:WORKER:{app.worker_id}'
            logger.info(f"[PID {os.getpid()}] HeartbeatConsumerStrategy using provided worker_id: {self.consumer_id}")
        else:
            self.consumer_id = None
            self._worker_key = None

        # 获取主机名前缀
        try:
            hostname = socket.gethostname()
            ip = socket.gethostbyname(hostname)
            prefix = hostname if hostname != 'localhost' else ip
        except:
            prefix = os.environ.get('HOSTNAME', 'unknown')

        self.hostname_prefix = prefix

    def _ensure_consumer_id(self):
        """确保consumer_id已创建（兼容旧代码）"""
        import os
        if self.consumer_id is None:
            # 使用 WorkerNaming 生成
            from .manager import WorkerNaming
            naming = WorkerNaming()
            self.consumer_id = naming.generate_worker_id(self.hostname_prefix)
            self._worker_key = f'{self.redis_prefix}:WORKER:{self.consumer_id}'
            logger.info(f"[PID {os.getpid()}] Generated NEW worker ID: {self.consumer_id}")
        else:
            logger.debug(f"[PID {os.getpid()}] Reusing existing worker ID: {self.consumer_id}")

    def get_consumer_name(self, queue: str) -> str:
        """
        获取消费者名称

        统一 group_name 架构：所有队列（包括优先级队列）使用基础队列名生成 consumer name
        例如：robust_bench2 和 robust_bench2:8 都使用 "YYDG-xxx-robust_bench2"
        """
        self._ensure_consumer_id()

        # 提取基础队列名（移除优先级后缀）
        base_queue = queue
        if ':' in queue and queue.rsplit(':', 1)[1].isdigit():
            base_queue = queue.rsplit(':', 1)[0]

        return f"{self.consumer_id}-{base_queue}"

    def cleanup(self):
        """清理资源（兼容旧代码）"""
        pass


__all__ = [
    'WorkerStateManager',
    'HeartbeatThreadManager',
    'WorkerScanner',
    'WorkerLifecycle',
    'HeartbeatConsumerStrategy',  # 兼容性
]
