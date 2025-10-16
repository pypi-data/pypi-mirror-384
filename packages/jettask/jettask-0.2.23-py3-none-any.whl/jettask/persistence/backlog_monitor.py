"""Stream积压监控模块

负责监控Redis Stream的积压情况，包括：
- 采集各队列的积压指标
- 使用分布式锁确保只有一个实例在采集
- 保存积压数据到PostgreSQL数据库
"""

import asyncio
import logging
import traceback
from typing import List, Dict, Optional
from datetime import datetime, timezone

from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from jettask.config.constants import is_internal_consumer

logger = logging.getLogger(__name__)


class BacklogMonitor:
    """Stream积压监控器

    职责：
    - 定期采集Redis Stream的积压指标
    - 使用分布式锁确保单实例采集
    - 将指标保存到PostgreSQL
    """

    def __init__(
        self,
        redis_client: Redis,
        async_session_local: sessionmaker,
        redis_prefix: str,
        namespace_name: str,
        node_id: str,
        enable_monitor: bool = True,
        monitor_interval: int = 1
    ):
        """初始化积压监控器

        Args:
            redis_client: Redis异步客户端
            async_session_local: SQLAlchemy会话工厂
            redis_prefix: Redis键前缀
            namespace_name: 命名空间名称
            node_id: 节点ID
            enable_monitor: 是否启用监控
            monitor_interval: 监控采集间隔（秒）
        """
        self.redis_client = redis_client
        self.AsyncSessionLocal = async_session_local
        self.redis_prefix = redis_prefix
        self.namespace_name = namespace_name
        self.node_id = node_id

        self.enable_monitor = enable_monitor
        self.monitor_interval = monitor_interval

        # 分布式锁配置
        self.lock_key = f"{redis_prefix}:BACKLOG_MONITOR_LOCK"
        self.lock_ttl = monitor_interval * 2  # 锁的TTL（秒），设为采集间隔的2倍

        # Stream注册表键
        self.stream_registry_key = f"{redis_prefix}:STREAM_REGISTRY"

        self._running = False
        self._monitor_task = None

    async def start(self):
        """启动监控任务"""
        if not self.enable_monitor:
            logger.info("Backlog monitor is disabled")
            return

        self._running = True
        self._monitor_task = asyncio.create_task(self._monitor_loop())
        logger.info(f"Backlog monitor started with {self.monitor_interval}s interval")

    async def stop(self):
        """停止监控任务"""
        self._running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        logger.debug("Backlog monitor stopped")

    async def _monitor_loop(self):
        """监控循环"""
        while self._running:
            try:
                # 尝试获取分布式锁
                lock_acquired = await self._try_acquire_lock()

                if lock_acquired:
                    try:
                        logger.debug(f"Acquired backlog monitor lock, collecting metrics...")
                        await self._collect_stream_backlog_metrics()
                        logger.debug("Stream backlog metrics collected successfully")
                    finally:
                        # 释放锁
                        await self._release_lock()
                else:
                    logger.debug("Another instance is collecting backlog metrics, skipping...")

                # 等待下一次采集
                await asyncio.sleep(self.monitor_interval)

            except Exception as e:
                logger.error(f"Error in stream backlog monitor: {e}")
                await asyncio.sleep(30)  # 出错后等待30秒

    async def _try_acquire_lock(self) -> bool:
        """尝试获取监控锁（使用Redis原生锁）"""
        try:
            # 使用SET NX EX命令实现分布式锁
            # NX: 只在键不存在时设置
            # EX: 设置过期时间（秒）
            result = await self.redis_client.set(
                self.lock_key.encode(),
                self.node_id.encode(),  # 锁的值为当前节点ID
                nx=True,  # 只在不存在时设置
                ex=self.lock_ttl  # 过期时间
            )
            return result is not None
        except Exception as e:
            logger.error(f"Error acquiring monitor lock: {e}")
            return False

    async def _release_lock(self):
        """释放监控锁（只释放自己持有的锁）"""
        try:
            # 使用Lua脚本确保只释放自己持有的锁
            lua_script = """
            if redis.call("get", KEYS[1]) == ARGV[1] then
                return redis.call("del", KEYS[1])
            else
                return 0
            end
            """
            await self.redis_client.eval(
                lua_script,
                1,
                self.lock_key.encode(),
                self.node_id.encode()
            )
        except Exception as e:
            logger.error(f"Error releasing monitor lock: {e}")

    async def _collect_stream_backlog_metrics(self):
        """采集Stream积压指标并保存到数据库（使用offset方式）"""
        try:
            # 获取所有队列的最新offset (QUEUE_OFFSETS)
            queue_offsets_key = f"{self.namespace_name}:QUEUE_OFFSETS"
            queue_offsets = {}
            try:
                # 使用decode_responses=False的客户端，手动解码
                raw_queue_offsets = await self.redis_client.hgetall(queue_offsets_key.encode())
                for k, v in raw_queue_offsets.items():
                    queue_name = k.decode() if isinstance(k, bytes) else k
                    offset_value = v.decode() if isinstance(v, bytes) else v
                    queue_offsets[queue_name] = int(offset_value)
            except Exception as e:
                logger.debug(f"No QUEUE_OFFSETS found for {queue_offsets_key}: {e}")

            # 获取所有任务组的消费offset (TASK_OFFSETS)
            task_offsets_key = f"{self.namespace_name}:TASK_OFFSETS"
            task_offsets = {}
            try:
                raw_task_offsets = await self.redis_client.hgetall(task_offsets_key.encode())
                for k, v in raw_task_offsets.items():
                    task_key = k.decode() if isinstance(k, bytes) else k
                    offset_value = v.decode() if isinstance(v, bytes) else v
                    task_offsets[task_key] = int(offset_value)
            except Exception as e:
                logger.debug(f"No TASK_OFFSETS found for {task_offsets_key}: {e}")

            # 使用Stream注册表替代SCAN命令获取队列信息
            stream_info_map = {}  # {queue_name: [(stream_key, priority), ...]}

            # 从redis中获取stream注册表（Hash结构）
            # 格式: {"queue_name:priority": "stream_key"}
            # 对于普通队列，priority为0
            stream_registry = await self.redis_client.hgetall(self.stream_registry_key.encode())

            for queue_priority_bytes, stream_key_bytes in stream_registry.items():
                queue_priority_str = queue_priority_bytes.decode() if isinstance(queue_priority_bytes, bytes) else str(queue_priority_bytes)
                stream_key = stream_key_bytes.decode() if isinstance(stream_key_bytes, bytes) else str(stream_key_bytes)

                # 解析queue_name和priority
                if ':' in queue_priority_str:
                    parts = queue_priority_str.rsplit(':', 1)
                    if len(parts) == 2 and parts[1].isdigit():
                        queue_name = parts[0]
                        priority = int(parts[1])
                    else:
                        # 如果最后一部分不是数字，说明是普通队列名包含冒号
                        queue_name = queue_priority_str
                        priority = 0
                else:
                    # 普通队列
                    queue_name = queue_priority_str
                    priority = 0

                if queue_name not in stream_info_map:
                    stream_info_map[queue_name] = []
                stream_info_map[queue_name].append((stream_key, priority))

            # 如果Stream注册表为空，进行一次性的scan作为初始化（仅在首次运行时）
            if not stream_info_map:
                # 使用 RegistryManager 获取队列，避免 scan
                from jettask.messaging.registry import QueueRegistry
                registry = QueueRegistry(
                    redis_client=None,
                    async_redis_client=self.redis_client,
                    redis_prefix=self.redis_prefix
                )

                # 获取所有队列
                all_queues = await registry.get_all_queues()

                for queue_full_name in all_queues:
                    # 构建 stream key
                    stream_key = f"{self.redis_prefix}:QUEUE:{queue_full_name}".encode()

                    # 检查 stream 是否存在
                    if await self.redis_client.exists(stream_key):
                        # 解析队列名和优先级
                        parts = queue_full_name.split(':')
                        if len(parts) >= 2 and parts[-1].isdigit():
                            # 优先级队列
                            queue_name = ':'.join(parts[:-1])
                            priority = int(parts[-1])
                        else:
                            # 普通队列
                            queue_name = queue_full_name
                            priority = 0

                        if queue_name not in stream_info_map:
                            stream_info_map[queue_name] = []
                        stream_info_map[queue_name].append((stream_key, priority))

                # 将发现的Stream信息添加到注册表中
                if stream_info_map:
                    pipeline = self.redis_client.pipeline()
                    for queue_name, stream_list in stream_info_map.items():
                        for stream_key, priority in stream_list:
                            if priority > 0:
                                queue_priority_key = f"{queue_name}:{priority}"
                            else:
                                queue_priority_key = queue_name
                            # 确保stream_key是bytes类型
                            if isinstance(stream_key, str):
                                stream_key = stream_key.encode()
                            pipeline.hset(self.stream_registry_key.encode(), queue_priority_key.encode(), stream_key)
                    await pipeline.execute()
                    logger.info(f"Registered {sum(len(stream_list) for stream_list in stream_info_map.values())} streams to registry during initialization")

            if not stream_info_map:
                logger.debug("No streams found in registry for backlog monitoring")
                return

            # 调试日志（使用debug级别避免刷屏）
            logger.debug(f"Found {len(stream_info_map)} queues for backlog monitoring")
            for queue_name, stream_list in stream_info_map.items():
                priorities = [p for _, p in stream_list]
                # 筛选出非0优先级（0表示普通队列）
                high_priorities = [p for p in priorities if p > 0]
                if high_priorities:
                    logger.debug(f"  - {queue_name}: {len(stream_list)} streams (includes priorities: {sorted(set(priorities))})")
                else:
                    logger.debug(f"  - {queue_name}: regular queue only (priority=0)")

            # 收集每个队列的指标（聚合所有优先级）
            metrics = []
            current_time = datetime.now(timezone.utc)

            for queue_name, stream_list in stream_info_map.items():
                # 分别处理每个优先级队列
                for stream_key, priority in stream_list:
                    try:
                        # 获取该队列的最新offset（考虑优先级队列）
                        if priority > 0:
                            # 优先级队列的key格式: queue_name:priority
                            queue_key = f"{queue_name}:{priority}"
                        else:
                            queue_key = queue_name
                        last_published_offset = queue_offsets.get(queue_key, 0)

                        # 获取Stream信息
                        stream_info = await self.redis_client.xinfo_stream(stream_key)
                        stream_length = stream_info.get(b'length', 0)

                        # 获取消费组信息
                        has_consumer_groups = False
                        try:
                            groups = await self.redis_client.xinfo_groups(stream_key)

                            for group in groups:
                                # 处理group_name
                                raw_name = group.get('name', b'')
                                if isinstance(raw_name, bytes):
                                    group_name = raw_name.decode() if raw_name else ''
                                else:
                                    group_name = str(raw_name) if raw_name else ''

                                if not group_name:
                                    group_name = 'unknown'

                                # 过滤内部消费者组
                                if is_internal_consumer(group_name):
                                    # logger.info(f"Skipping internal consumer group: {group_name}")
                                    continue

                                # 处理pending - 直接是int
                                pending_count = group.get('pending', 0)

                                # 从TASK_OFFSETS获取该组的消费offset
                                # 从 group_name 中提取 task_name（最后一段）
                                task_name = group_name.split(':')[-1]
                                # 构建 field：队列名（含优先级）+ 任务名
                                # 例如：robust_bench2:8:benchmark_task
                                task_offset_key = f"{queue_key}:{task_name}"
                                last_acked_offset = task_offsets.get(task_offset_key, 0)

                                # 计算各种积压指标
                                # 1. 总积压 = 队列最新offset - 消费组已确认的offset
                                total_backlog = max(0, last_published_offset - last_acked_offset)

                                # 2. 未投递的积压 = 总积压 - pending数量
                                backlog_undelivered = max(0, total_backlog - pending_count)

                                # 3. 已投递未确认 = pending数量
                                backlog_delivered_unacked = pending_count

                                # 4. 已投递的offset = 已确认offset + pending数量
                                last_delivered_offset = last_acked_offset + pending_count

                                # 为每个消费组创建一条记录
                                metrics.append({
                                    'namespace': self.namespace_name,
                                    'stream_name': queue_name,
                                    'priority': priority,  # 添加优先级字段
                                    'consumer_group': group_name,
                                    'last_published_offset': last_published_offset,
                                    'last_delivered_offset': last_delivered_offset,
                                    'last_acked_offset': last_acked_offset,
                                    'pending_count': pending_count,
                                    'backlog_undelivered': backlog_undelivered,
                                    'backlog_unprocessed': total_backlog,
                                    'created_at': current_time
                                })
                                has_consumer_groups = True

                        except Exception as e:
                            # 这个队列没有消费组
                            stream_key_str = stream_key.decode('utf-8') if isinstance(stream_key, bytes) else str(stream_key)
                            logger.debug(f"No consumer groups for stream {stream_key_str}: {e}")

                        # 如果没有消费组，保存Stream级别的指标
                        if not has_consumer_groups and last_published_offset > 0:
                            metrics.append({
                                'namespace': self.namespace_name,
                                'stream_name': queue_name,
                                'priority': priority,  # 添加优先级字段
                                'consumer_group': None,
                                'last_published_offset': last_published_offset,
                                'last_delivered_offset': 0,
                                'last_acked_offset': 0,
                                'pending_count': 0,
                                'backlog_undelivered': last_published_offset,
                                'backlog_unprocessed': last_published_offset,
                                'created_at': current_time
                            })

                    except Exception as e:
                        stream_key_str = stream_key.decode('utf-8') if isinstance(stream_key, bytes) else str(stream_key)
                        logger.error(f"Error collecting metrics for stream {stream_key_str}: {e}")
                        continue

            # 保存指标到数据库
            if metrics:
                await self._save_backlog_metrics(metrics)

        except Exception as e:
            logger.error(f"Error collecting stream backlog metrics: {e}")
            logger.error(traceback.format_exc())

    async def _save_backlog_metrics(self, metrics: List[Dict]):
        """保存积压指标到数据库（仅保存发生变化的数据）"""
        if not metrics:
            return

        try:
            async with self.AsyncSessionLocal() as session:
                # 要保存的新记录
                metrics_to_save = []

                # 使用批量查询优化性能
                metric_keys = {}  # 用于快速查找

                for metric in metrics:
                    # 构建唯一键：namespace + stream_name + consumer_group + priority
                    unique_key = f"{metric['namespace']}:{metric['stream_name']}:{metric['consumer_group']}:{metric['priority']}"
                    metric_keys[unique_key] = metric

                # 批量查询最新记录 - 分批查询以避免SQL过长
                last_records = {}
                metric_list = list(metric_keys.values())
                batch_size = 50  # 每批查询50个

                for i in range(0, len(metric_list), batch_size):
                    batch = metric_list[i:i + batch_size]

                    # 构建参数化查询
                    conditions = []
                    params = {}
                    for idx, metric in enumerate(batch):
                        param_prefix = f"p{i + idx}"
                        conditions.append(f"""
                            (namespace = :{param_prefix}_ns
                             AND stream_name = :{param_prefix}_sn
                             AND consumer_group = :{param_prefix}_cg
                             AND priority = :{param_prefix}_pr)
                        """)
                        params[f"{param_prefix}_ns"] = metric['namespace']
                        params[f"{param_prefix}_sn"] = metric['stream_name']
                        params[f"{param_prefix}_cg"] = metric['consumer_group']
                        params[f"{param_prefix}_pr"] = metric['priority']

                    if conditions:
                        # 使用窗口函数获取每个组合的最新记录
                        query_sql = text(f"""
                            WITH latest_records AS (
                                SELECT
                                    namespace,
                                    stream_name,
                                    consumer_group,
                                    priority,
                                    last_published_offset,
                                    last_delivered_offset,
                                    last_acked_offset,
                                    pending_count,
                                    backlog_undelivered,
                                    backlog_unprocessed,
                                    ROW_NUMBER() OVER (
                                        PARTITION BY namespace, stream_name, consumer_group, priority
                                        ORDER BY created_at DESC
                                    ) as rn
                                FROM stream_backlog_monitor
                                WHERE ({' OR '.join(conditions)})
                            )
                            SELECT
                                namespace,
                                stream_name,
                                consumer_group,
                                priority,
                                last_published_offset,
                                last_delivered_offset,
                                last_acked_offset,
                                pending_count,
                                backlog_undelivered,
                                backlog_unprocessed
                            FROM latest_records
                            WHERE rn = 1
                        """)

                        result = await session.execute(query_sql, params)
                        for row in result:
                            key = f"{row.namespace}:{row.stream_name}:{row.consumer_group}:{row.priority}"
                            last_records[key] = row
                            logger.debug(f"Found last record for {key}: published={row.last_published_offset}")

                # 对每个指标进行去重检查
                for unique_key, metric in metric_keys.items():
                    should_save = False

                    if unique_key not in last_records:
                        # 没有历史记录，需要保存
                        should_save = True
                    else:
                        # 比较关键指标是否发生变化
                        last_record = last_records[unique_key]

                        # 详细的调试日志
                        changes = []
                        logger.debug(f"Comparing for {unique_key}:")
                        logger.debug(f"  DB record: published={last_record.last_published_offset} (type={type(last_record.last_published_offset)}), "
                                   f"delivered={last_record.last_delivered_offset} (type={type(last_record.last_delivered_offset)}), "
                                   f"acked={last_record.last_acked_offset}, pending={last_record.pending_count}, "
                                   f"undelivered={last_record.backlog_undelivered}, unprocessed={last_record.backlog_unprocessed}")
                        logger.debug(f"  New metric: published={metric['last_published_offset']} (type={type(metric['last_published_offset'])}), "
                                   f"delivered={metric['last_delivered_offset']} (type={type(metric['last_delivered_offset'])}), "
                                   f"acked={metric['last_acked_offset']}, pending={metric['pending_count']}, "
                                   f"undelivered={metric['backlog_undelivered']}, unprocessed={metric['backlog_unprocessed']}")

                        # 确保类型一致的比较（全部转为int进行比较）
                        db_published = int(last_record.last_published_offset) if last_record.last_published_offset is not None else 0
                        new_published = int(metric['last_published_offset']) if metric['last_published_offset'] is not None else 0

                        db_delivered = int(last_record.last_delivered_offset) if last_record.last_delivered_offset is not None else 0
                        new_delivered = int(metric['last_delivered_offset']) if metric['last_delivered_offset'] is not None else 0

                        db_acked = int(last_record.last_acked_offset) if last_record.last_acked_offset is not None else 0
                        new_acked = int(metric['last_acked_offset']) if metric['last_acked_offset'] is not None else 0

                        db_pending = int(last_record.pending_count) if last_record.pending_count is not None else 0
                        new_pending = int(metric['pending_count']) if metric['pending_count'] is not None else 0

                        db_undelivered = int(last_record.backlog_undelivered) if last_record.backlog_undelivered is not None else 0
                        new_undelivered = int(metric['backlog_undelivered']) if metric['backlog_undelivered'] is not None else 0

                        db_unprocessed = int(last_record.backlog_unprocessed) if last_record.backlog_unprocessed is not None else 0
                        new_unprocessed = int(metric['backlog_unprocessed']) if metric['backlog_unprocessed'] is not None else 0

                        if db_published != new_published:
                            changes.append(f"published: {db_published} -> {new_published}")
                        if db_delivered != new_delivered:
                            changes.append(f"delivered: {db_delivered} -> {new_delivered}")
                        if db_acked != new_acked:
                            changes.append(f"acked: {db_acked} -> {new_acked}")
                        if db_pending != new_pending:
                            changes.append(f"pending: {db_pending} -> {new_pending}")
                        if db_undelivered != new_undelivered:
                            changes.append(f"undelivered: {db_undelivered} -> {new_undelivered}")
                        if db_unprocessed != new_unprocessed:
                            changes.append(f"unprocessed: {db_unprocessed} -> {new_unprocessed}")

                        if changes:
                            should_save = True
                        else:
                            logger.debug(f"Metric unchanged for {unique_key}, skipping")

                    if should_save:
                        metrics_to_save.append(metric)

                # 批量插入发生变化的监控数据
                if metrics_to_save:
                    insert_sql = text("""
                        INSERT INTO stream_backlog_monitor
                        (namespace, stream_name, priority, consumer_group, last_published_offset,
                         last_delivered_offset, last_acked_offset, pending_count,
                         backlog_undelivered, backlog_unprocessed, created_at)
                        VALUES
                        (:namespace, :stream_name, :priority, :consumer_group, :last_published_offset,
                         :last_delivered_offset, :last_acked_offset, :pending_count,
                         :backlog_undelivered, :backlog_unprocessed, :created_at)
                    """)

                    # 逐条插入（SQLAlchemy的execute不支持批量插入参数列表）
                    for metric_data in metrics_to_save:
                        await session.execute(insert_sql, metric_data)

                    await session.commit()
                else:
                    logger.debug(f"No metrics changed, skipped saving all {len(metrics)} records")

        except Exception as e:
            logger.error(f"Error saving backlog metrics to database: {e}")
            logger.error(traceback.format_exc())
