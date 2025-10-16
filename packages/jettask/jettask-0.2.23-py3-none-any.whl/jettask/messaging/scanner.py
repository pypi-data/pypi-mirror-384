"""
延迟消息扫描器 - 扫描延迟队列并将到期任务移到普通队列
从 EventPool 中提取的延迟任务扫描逻辑
"""

import time
import logging
import asyncio
from typing import List, Dict, Callable, Optional
from redis.asyncio import Redis as AsyncRedis

logger = logging.getLogger('app')


class DelayedMessageScanner:
    """
    延迟消息扫描器

    职责：
    1. 扫描 Redis Sorted Set 中到期的延迟任务
    2. 从 Stream 中读取任务数据
    3. 将到期任务从延迟队列移除
    4. 通过回调函数通知调用方处理到期任务

    工作原理：
    - 延迟任务发送时会：
      1. 写入 Stream（包含实际数据）
      2. 在 Sorted Set 中记录 Stream ID 和执行时间
    - 扫描器定期检查 Sorted Set，找到到期的 Stream ID
    - 从 Stream 读取完整数据后回调处理
    - 从 Sorted Set 移除已处理的任务
    """

    def __init__(
        self,
        async_binary_redis_client: AsyncRedis,
        redis_prefix: str = 'jettask',
        scan_interval: float = 0.05,  # 扫描间隔（秒）
        batch_size: int = 100,  # 每次扫描最多处理的任务数
        priority_discovery_callback: Optional[Callable] = None,  # 优先级队列发现回调
        ensure_consumer_group_callback: Optional[Callable] = None  # 确保consumer group存在的回调
    ):
        """
        初始化延迟消息扫描器

        Args:
            async_binary_redis_client: 异步Redis客户端（二进制模式）
            redis_prefix: Redis键前缀
            scan_interval: 扫描间隔（秒），默认50ms
            batch_size: 每次扫描最多处理的任务数
            priority_discovery_callback: 优先级队列发现回调，签名: async def (base_queue: str) -> List[str]
            ensure_consumer_group_callback: 确保consumer group存在的回调，签名: async def (queue: str) -> None
        """
        self.redis = async_binary_redis_client
        self.redis_prefix = redis_prefix
        self.scan_interval = scan_interval
        self.batch_size = batch_size
        self.priority_discovery_callback = priority_discovery_callback
        self.ensure_consumer_group_callback = ensure_consumer_group_callback

        # 任务回调：{queue_name: callback_function}
        self._callbacks: Dict[str, Callable] = {}

        # Lua脚本缓存
        self._scan_script = None

        # 控制标志
        self._running = False
        self._scan_tasks: List[asyncio.Task] = []

        # 优先级队列缓存：{base_queue: [priority_queues]}
        self._priority_queues_cache: Dict[str, List[str]] = {}

        logger.debug(f"DelayedMessageScanner initialized with prefix: {redis_prefix}")

    def _get_delayed_queue_name(self, queue: str) -> str:
        """获取延迟队列名（Sorted Set）"""
        return f"{self.redis_prefix}:DELAYED_QUEUE:{queue}"

    def _get_prefixed_queue_name(self, queue: str) -> str:
        """获取带前缀的队列名（Stream）"""
        return f"{self.redis_prefix}:QUEUE:{queue}"

    def register_callback(self, queue: str, callback: Callable):
        """
        注册队列的到期任务回调函数

        Args:
            queue: 队列名
            callback: 回调函数，签名: async def callback(tasks: List[Dict])
                     tasks格式: [{'event_id': '...', 'data': {...}}, ...]

        示例:
            async def handle_expired_tasks(tasks):
                for task in tasks:
                    print(f"Task {task['event_id']} expired")
                    await process(task['data'])

            scanner.register_callback("orders", handle_expired_tasks)
        """
        self._callbacks[queue] = callback
        logger.info(f"Registered callback for queue {queue}")

    async def start(self, queues: List[str]):
        """
        启动扫描器，为每个队列创建独立的扫描任务

        Args:
            queues: 队列名列表
        """
        if self._running:
            logger.warning("DelayedMessageScanner is already running")
            return

        self._running = True
        logger.info(f"Starting DelayedMessageScanner for queues: {queues}")

        # 为每个队列创建独立的扫描任务
        for queue in queues:
            task = asyncio.create_task(self._scan_queue_loop(queue))
            self._scan_tasks.append(task)

        logger.info(f"DelayedMessageScanner started with {len(self._scan_tasks)} scan tasks")

    async def stop(self):
        """停止扫描器"""
        if not self._running:
            return

        logger.info("Stopping DelayedMessageScanner...")
        self._running = False

        # 取消所有扫描任务
        for task in self._scan_tasks:
            task.cancel()

        # 等待所有任务完成
        await asyncio.gather(*self._scan_tasks, return_exceptions=True)
        self._scan_tasks.clear()

        logger.info("DelayedMessageScanner stopped")

    async def _scan_queue_loop(self, queue: str):
        """
        单个队列的扫描循环（支持动态优先级队列发现）

        Args:
            queue: 基础队列名（不含优先级后缀）
        """
        base_interval = self.scan_interval
        max_interval = 0.5  # 最大间隔500ms
        priority_check_interval = 1.0  # 优先级队列检查间隔（秒）
        last_priority_check = 0

        logger.info(f"Starting delayed task scanner for queue {queue}, interval={base_interval}")

        # 初始化优先级队列列表
        priority_queues = []
        if self.priority_discovery_callback:
            try:
                priority_queues = await self.priority_discovery_callback(queue)
                self._priority_queues_cache[queue] = priority_queues
                logger.info(f"Discovered priority queues for {queue}: {priority_queues}")
            except Exception as e:
                logger.error(f"Error discovering priority queues for {queue}: {e}")

        while self._running:
            try:
                # 定期检查优先级队列是否有变化（每1秒）
                current_time = time.time()
                if self.priority_discovery_callback and (current_time - last_priority_check >= priority_check_interval):
                    try:
                        new_priority_queues = await self.priority_discovery_callback(queue)
                        if new_priority_queues != priority_queues:
                            logger.info(f"Priority queues updated for {queue}: {priority_queues} -> {new_priority_queues}")

                            # 为新增的优先级队列确保consumer group存在
                            if self.ensure_consumer_group_callback:
                                new_queues = set(new_priority_queues) - set(priority_queues)
                                for new_q in new_queues:
                                    try:
                                        await self.ensure_consumer_group_callback(new_q)
                                        logger.info(f"Ensured consumer group for new priority queue: {new_q}")
                                    except Exception as e:
                                        logger.error(f"Error ensuring consumer group for {new_q}: {e}")

                            priority_queues = new_priority_queues
                            self._priority_queues_cache[queue] = priority_queues
                    except Exception as e:
                        logger.error(f"Error checking priority queues for {queue}: {e}")
                    last_priority_check = current_time

                # 扫描基础队列 + 所有优先级队列
                all_queues_to_scan = [queue] + priority_queues
                all_expired_tasks = []

                for q in all_queues_to_scan:
                    expired_tasks = await self._scan_and_get_expired_tasks(q)
                    if expired_tasks:
                        all_expired_tasks.extend(expired_tasks)

                # 如果有任务到期，通知回调
                if all_expired_tasks and queue in self._callbacks:
                    try:
                        await self._callbacks[queue](all_expired_tasks)
                    except Exception as e:
                        logger.error(f"Error in callback for queue {queue}: {e}", exc_info=True)

                # 动态调整扫描间隔
                if all_expired_tasks:
                    # 有任务到期，使用较短的间隔
                    sleep_time = base_interval
                else:
                    # 没有任务到期，检查下一个任务的到期时间
                    min_next_time = None
                    for q in all_queues_to_scan:
                        next_time = await self._get_next_task_time(q)
                        if next_time is not None:
                            if min_next_time is None or next_time < min_next_time:
                                min_next_time = next_time

                    if min_next_time is not None:
                        # 计算到下一个任务的时间，但不超过max_interval
                        sleep_time = min(max_interval, max(base_interval, min_next_time - time.time() - 0.01))
                    else:
                        # 没有待处理的延迟任务
                        sleep_time = max_interval

            except asyncio.CancelledError:
                logger.info(f"Delayed task scanner for queue {queue} cancelled")
                break
            except Exception as e:
                logger.error(f"Error scanning delayed tasks for queue {queue}: {e}", exc_info=True)
                sleep_time = base_interval

            await asyncio.sleep(sleep_time)

    async def _scan_and_get_expired_tasks(self, queue: str) -> List[Dict]:
        """
        扫描并获取到期的延迟任务

        Args:
            queue: 队列名

        Returns:
            List[Dict]: 到期任务列表，格式: [{'event_id': '...', 'data': {...}}, ...]
        """
        try:
            current_time = time.time()
            delayed_queue_key = self._get_delayed_queue_name(queue)

            # 使用Lua脚本原子地获取到期的任务ID
            # 注意：我们只获取ID，不读取数据，因为后续需要用XCLAIM转移所有权
            lua_script = """
            local delayed_queue_key = KEYS[1]
            local current_time = ARGV[1]
            local limit = ARGV[2]

            -- 获取到期的任务ID（这些是Stream消息ID）
            local expired_task_ids = redis.call('ZRANGEBYSCORE', delayed_queue_key, 0, current_time, 'LIMIT', 0, limit)

            if #expired_task_ids == 0 then
                return {}
            end

            -- 从延迟队列中移除这些任务（标记为已到期）
            for i, task_id in ipairs(expired_task_ids) do
                redis.call('ZREM', delayed_queue_key, task_id)
            end

            return expired_task_ids
            """

            # 注册Lua脚本
            if not self._scan_script:
                self._scan_script = self.redis.register_script(lua_script)

            # 执行脚本（只传入延迟队列key，返回到期的消息ID列表）
            expired_task_ids = await self._scan_script(
                keys=[delayed_queue_key],
                args=[str(current_time), str(self.batch_size)]
            )

            if not expired_task_ids:
                return []

            # 返回到期的消息ID列表（不包含数据）
            # 数据将在 worker 端通过 XCLAIM 获取，这样能正确转移消息所有权
            tasks_to_return = []
            for task_id in expired_task_ids:
                try:
                    # 解码消息ID
                    event_id = task_id if isinstance(task_id, str) else task_id.decode('utf-8')

                    # 只返回消息ID和队列信息
                    # worker会使用XCLAIM来获取消息并转移所有权
                    tasks_to_return.append({
                        'event_id': event_id,
                        'queue': queue  # 队列名（可能包含优先级后缀）
                    })

                except Exception as e:
                    logger.error(f"Error processing delayed task ID: {e}", exc_info=True)

            if tasks_to_return:
                logger.info(f"Found {len(tasks_to_return)} expired tasks in queue {queue}")

            return tasks_to_return

        except Exception as e:
            logger.error(f"Error scanning delayed tasks for queue {queue}: {e}", exc_info=True)
            return []

    async def _get_next_task_time(self, queue: str) -> Optional[float]:
        """
        获取下一个任务的到期时间

        Args:
            queue: 队列名

        Returns:
            Optional[float]: 到期时间（Unix时间戳），如果没有任务返回None
        """
        try:
            delayed_queue_key = self._get_delayed_queue_name(queue)

            # 获取分数最小的任务（最早到期的）
            result = await self.redis.zrange(
                delayed_queue_key, 0, 0, withscores=True
            )

            if result:
                # result格式: [(task_id, score)]
                return result[0][1]

            return None

        except Exception as e:
            logger.error(f"Error getting next task time for queue {queue}: {e}")
            return None

    async def get_delayed_count(self, queue: str) -> int:
        """
        获取延迟队列中的任务数量

        Args:
            queue: 队列名

        Returns:
            int: 任务数量
        """
        delayed_queue_key = self._get_delayed_queue_name(queue)
        return await self.redis.zcard(delayed_queue_key)

    async def get_expired_count(self, queue: str) -> int:
        """
        获取已到期但未处理的任务数量

        Args:
            queue: 队列名

        Returns:
            int: 已到期任务数量
        """
        delayed_queue_key = self._get_delayed_queue_name(queue)
        current_time = time.time()

        count = await self.redis.zcount(delayed_queue_key, 0, current_time)
        return count
