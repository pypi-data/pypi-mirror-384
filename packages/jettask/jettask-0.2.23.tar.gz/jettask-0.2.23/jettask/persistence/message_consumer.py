"""消息消费模块

负责从Redis Stream队列中消费消息，并持久化到PostgreSQL。
"""

import asyncio
import logging
import traceback
from typing import List, Dict
from collections import defaultdict

import redis.asyncio as redis
from redis.asyncio import Redis

from .task_persistence import TaskPersistence

logger = logging.getLogger(__name__)


class MessageConsumer:
    """消息消费器

    职责：
    - 从Redis Stream队列消费消息
    - 解析消息并持久化到数据库
    - 管理多个队列的消费任务
    - 处理错误重试和ACK
    """

    def __init__(
        self,
        redis_client: Redis,
        redis_prefix: str,
        consumer_group: str,
        consumer_id: str,
        task_persistence: TaskPersistence,
        queue_discovery: 'QueueDiscovery'
    ):
        """初始化消息消费器

        Args:
            redis_client: Redis异步客户端
            redis_prefix: Redis键前缀
            consumer_group: 消费者组名称
            consumer_id: 消费者ID
            task_persistence: 任务持久化处理器
            queue_discovery: 队列发现器
        """
        self.redis_client = redis_client
        self.redis_prefix = redis_prefix
        self.consumer_group = consumer_group
        self.consumer_id = consumer_id
        self.task_persistence = task_persistence
        self.queue_discovery = queue_discovery

        # 错误计数器
        self._consecutive_errors = defaultdict(int)

        # 已处理任务ID缓存（用于优化查询）
        self._processed_task_ids = set()
        self._processed_ids_lock = asyncio.Lock()
        self._processed_ids_max_size = 100000
        self._processed_ids_cleanup_interval = 300

        self._running = False
        self._consume_task = None
        self._queue_tasks = {}

    async def start(self):
        """启动消费器"""
        self._running = True
        self._consume_task = asyncio.create_task(self._consume_queues())
        logger.debug("MessageConsumer started")

    async def stop(self):
        """停止消费器"""
        self._running = False

        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        # 取消所有队列任务
        for task in self._queue_tasks.values():
            task.cancel()

        if self._queue_tasks:
            await asyncio.gather(*self._queue_tasks.values(), return_exceptions=True)

        logger.debug("MessageConsumer stopped")

    async def _consume_queues(self):
        """启动所有队列的消费任务"""
        while self._running:
            try:
                # 获取已知队列
                known_queues = self.queue_discovery.get_known_queues()

                # 为每个队列启动消费任务
                for queue in known_queues:
                    if queue not in self._queue_tasks or self._queue_tasks[queue].done():
                        self._queue_tasks[queue] = asyncio.create_task(self._consume_queue(queue))
                        logger.debug(f"Started consumer task for queue: {queue}")

                # 移除不存在的队列任务
                for queue in list(self._queue_tasks.keys()):
                    if queue not in known_queues:
                        self._queue_tasks[queue].cancel()
                        del self._queue_tasks[queue]
                        logger.debug(f"Stopped consumer task for removed queue: {queue}")

                await asyncio.sleep(10)

            except Exception as e:
                logger.error(f"Error in consume_queues manager: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(5)

    async def _consume_queue(self, queue_name: str):
        """消费单个队列的任务（包括优先级队列）"""
        # 判断是否是优先级队列
        is_priority_queue = ':' in queue_name and queue_name.rsplit(':', 1)[-1].isdigit()

        if is_priority_queue:
            # 优先级队列格式：base_queue:priority (如 robust_bench2:2)
            base_queue = queue_name.rsplit(':', 1)[0]
            priority = queue_name.rsplit(':', 1)[1]
            stream_key = f"{self.redis_prefix}:QUEUE:{base_queue}:{priority}"
        else:
            # 普通队列
            stream_key = f"{self.redis_prefix}:QUEUE:{queue_name}"

        logger.debug(f"Consuming queue: {queue_name}, stream_key: {stream_key}, is_priority: {is_priority_queue}")

        check_backlog = True
        lastid = "0-0"

        # pg_consumer 应该使用统一的 consumer_id，而不是为每个队列创建新的
        # 因为 pg_consumer 的职责是消费所有队列的消息并写入数据库
        # 它不是真正的任务执行者，所以不需要为每个队列创建独立的 consumer
        consumer_name = self.consumer_id

        # ConsumerManager会自动处理离线worker的pending消息恢复
        # 不需要手动恢复

        while self._running and queue_name in self.queue_discovery.get_known_queues():
            try:
                myid = lastid if check_backlog else ">"

                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    consumer_name,  # 使用ConsumerManager管理的consumer_name
                    {stream_key: myid},
                    count=10000,
                    block=1000 if not check_backlog else 0
                )

                if not messages or (messages and len(messages[0][1]) == 0):
                    check_backlog = False
                    continue

                if messages:
                    await self._process_messages(messages)
                    self._consecutive_errors[queue_name] = 0

                    if messages[0] and messages[0][1]:
                        lastid = messages[0][1][-1][0].decode('utf-8') if isinstance(messages[0][1][-1][0], bytes) else messages[0][1][-1][0]
                        check_backlog = len(messages[0][1]) >= 2000

            except redis.ResponseError as e:
                if "NOGROUP" in str(e):
                    try:
                        await self.redis_client.xgroup_create(
                            stream_key, self.consumer_group, id='0', mkstream=True
                        )
                        logger.debug(f"Recreated consumer group for queue: {queue_name}")
                        check_backlog = True
                        lastid = "0-0"
                    except:
                        pass
                else:
                    logger.error(f"Redis error for queue {queue_name}: {e}")
                    logger.error(traceback.format_exc())
                    self._consecutive_errors[queue_name] += 1

                if self._consecutive_errors[queue_name] > 10:
                    logger.debug(f"Too many errors for queue {queue_name}, will retry later")
                    await asyncio.sleep(30)
                    self._consecutive_errors[queue_name] = 0

            except Exception as e:
                logger.error(f"Error consuming queue {queue_name}: {e}", exc_info=True)
                self._consecutive_errors[queue_name] += 1
                await asyncio.sleep(1)

    async def _process_messages(self, messages: List):
        """处理消息并保存到PostgreSQL"""
        tasks_to_insert = []
        ack_batch = []

        for stream_key, stream_messages in messages:
            if not stream_messages:
                continue

            stream_key_str = stream_key.decode('utf-8') if isinstance(stream_key, bytes) else stream_key
            msg_ids_to_ack = []

            for msg_id, data in stream_messages:
                try:
                    if not msg_id or not data:
                        continue

                    msg_id_str = msg_id.decode('utf-8') if isinstance(msg_id, bytes) else str(msg_id)

                    # 使用TaskPersistence解析消息
                    task_info = self.task_persistence.parse_stream_message(msg_id_str, data)
                    if task_info:
                        tasks_to_insert.append(task_info)
                        msg_ids_to_ack.append(msg_id)

                except Exception as e:
                    logger.error(f"Error processing message {msg_id}: {e}")
                    logger.error(traceback.format_exc())

            if msg_ids_to_ack:
                ack_batch.append((stream_key, msg_ids_to_ack))

        if tasks_to_insert:
            # 使用TaskPersistence插入任务
            inserted_count = await self.task_persistence.insert_tasks(tasks_to_insert)

            # 将成功插入的任务ID添加到内存集合中
            async with self._processed_ids_lock:
                for task in tasks_to_insert:
                    self._processed_task_ids.add(task['id'])

                # 如果集合过大，清理最早的一半
                if len(self._processed_task_ids) > self._processed_ids_max_size:
                    # 只保留最新的一半ID
                    ids_list = list(self._processed_task_ids)
                    keep_count = self._processed_ids_max_size // 2
                    self._processed_task_ids = set(ids_list[-keep_count:])
                    logger.debug(f"Cleaned processed IDs cache, kept {keep_count} most recent IDs")

            # ACK所有消息（即使部分插入失败，也要ACK，避免重复处理）
            if ack_batch:
                pipeline = self.redis_client.pipeline()
                for stream_key, msg_ids in ack_batch:
                    pipeline.xack(stream_key, self.consumer_group, *msg_ids)

                try:
                    await pipeline.execute()
                    total_acked = sum(len(msg_ids) for _, msg_ids in ack_batch)
                    logger.debug(f"Successfully ACKed {total_acked} messages")
                except Exception as e:
                    logger.error(f"Error executing batch ACK: {e}")
