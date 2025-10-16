"""任务状态更新模块

负责从TASK_CHANGES流中消费任务变更事件，并更新数据库中的任务状态。
"""

import asyncio
import json
import logging
import traceback
from typing import Dict, List, Optional, Any, Set
from datetime import datetime, timezone

import redis.asyncio as redis
from redis.asyncio import Redis
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class TaskUpdater:
    """任务状态更新器

    职责：
    - 消费TASK_CHANGES流中的任务变更事件
    - 解析任务状态更新信息
    - 批量更新数据库中的任务状态
    - 支持pending消息恢复
    """

    def __init__(
        self,
        redis_client: Redis,
        async_session_local: sessionmaker,
        redis_prefix: str,
        consumer_id: str
    ):
        """初始化任务状态更新器

        Args:
            redis_client: Redis异步客户端
            async_session_local: SQLAlchemy会话工厂
            redis_prefix: Redis键前缀
            consumer_id: 消费者ID
        """
        self.redis_client = redis_client
        self.AsyncSessionLocal = async_session_local
        self.redis_prefix = redis_prefix
        self.consumer_id = consumer_id

        # Stream配置
        self.change_stream_key = f"{redis_prefix}:TASK_CHANGES"
        self.consumer_group = f"{redis_prefix}_changes_consumer"

        # 待重试的任务更新
        self._pending_updates = {}
        self._pending_updates_lock = asyncio.Lock()
        self._max_pending_updates = 10000
        self._retry_interval = 5  # 每5秒重试一次

        self._running = False
        self._consume_task = None
        self._retry_task = None

    async def start(self):
        """启动更新器"""
        # 创建消费者组
        try:
            await self.redis_client.xgroup_create(
                self.change_stream_key, self.consumer_group, id='0', mkstream=True
            )
            logger.debug(f"Created consumer group for task changes stream")
        except redis.ResponseError:
            pass

        self._running = True
        self._consume_task = asyncio.create_task(self._consume_task_changes())
        self._retry_task = asyncio.create_task(self._retry_pending_updates())
        logger.debug("TaskUpdater started")

    async def stop(self):
        """停止更新器"""
        self._running = False

        if self._consume_task:
            self._consume_task.cancel()
            try:
                await self._consume_task
            except asyncio.CancelledError:
                pass

        if self._retry_task:
            self._retry_task.cancel()
            try:
                await self._retry_task
            except asyncio.CancelledError:
                pass

        logger.debug("TaskUpdater stopped")

    async def _consume_task_changes(self):
        """消费任务变更事件流 - 基于事件驱动的更新（支持pending消息恢复）"""
        # 模仿 listen_event_by_task 的写法：先处理pending消息，再处理新消息
        check_backlog = True
        lastid = "0-0"
        batch_size = 1000

        while self._running:
            try:
                # 决定读取位置：如果有backlog，从lastid开始；否则读取新消息
                if check_backlog:
                    myid = lastid
                else:
                    myid = ">"

                messages = await self.redis_client.xreadgroup(
                    self.consumer_group,
                    self.consumer_id,
                    {self.change_stream_key: myid},
                    count=batch_size,
                    block=1000 if not check_backlog else 0  # backlog时不阻塞
                )

                if not messages:
                    check_backlog = False
                    continue

                # 检查是否还有更多backlog消息
                if messages and len(messages[0][1]) > 0:
                    check_backlog = len(messages[0][1]) >= batch_size
                else:
                    check_backlog = False

                # 收集消息ID和对应的task_id
                msg_to_task = {}  # msg_id -> (stream_id, task_key) 映射

                for _, stream_messages in messages:
                    for msg_id, data in stream_messages:
                        try:
                            # 更新lastid（无论消息是否处理成功）
                            if isinstance(msg_id, bytes):
                                lastid = msg_id.decode('utf-8')
                            else:
                                lastid = str(msg_id)

                            task_key = data[b'id']
                            task_key = task_key.decode('utf-8') if isinstance(task_key, bytes) else str(task_key)

                            # 从完整的task_key格式提取stream_id
                            # 格式: namespace:TASK:stream_id:queue_name
                            stream_id = None
                            if ':TASK:' in task_key:
                                parts = task_key.split(':TASK:')
                                if len(parts) == 2:
                                    # 再从右边部分提取stream_id
                                    right_parts = parts[1].split(':')
                                    if right_parts:
                                        stream_id = right_parts[0]  # 提取stream_id

                            if stream_id:
                                # 存储元组: (stream_id, task_key)
                                msg_to_task[msg_id] = (stream_id, task_key)
                            else:
                                logger.warning(f"Cannot extract stream_id from task_key: {task_key}")
                        except Exception as e:
                            logger.error(f"Error processing change event {msg_id}: {e} {data=}")
                            logger.error(traceback.format_exc())
                            # 解析失败的消息也应该ACK，避免一直重试
                            await self.redis_client.xack(self.change_stream_key, self.consumer_group, msg_id)

                if msg_to_task:
                    # 批量更新任务，返回成功更新的task_id列表
                    # msg_to_task 的值现在是元组 (stream_id, task_key)
                    id_tuples = list(set(msg_to_task.values()))
                    logger.info(f"Processing {len(id_tuples)} task updates from change stream")
                    successful_tuples = await self._update_tasks_by_event(id_tuples)

                    # 只ACK成功更新的消息
                    ack_ids = []
                    failed_count = 0
                    for msg_id, id_tuple in msg_to_task.items():
                        if successful_tuples and id_tuple in successful_tuples:
                            ack_ids.append(msg_id)
                        else:
                            failed_count += 1

                    if ack_ids:
                        await self.redis_client.xack(self.change_stream_key, self.consumer_group, *ack_ids)
                        if len(ack_ids) > 0:
                            logger.info(f"Updated {len(ack_ids)} task statuses")

                    if failed_count > 0:
                        logger.debug(f"Failed to update {failed_count} tasks, will retry")

            except redis.ResponseError as e:
                if "NOGROUP" in str(e):
                    # 如果消费者组不存在，重新创建
                    try:
                        await self.redis_client.xgroup_create(
                            self.change_stream_key, self.consumer_group, id='0', mkstream=True
                        )
                        logger.debug(f"Recreated consumer group for task changes stream")
                        check_backlog = True
                        lastid = "0-0"
                    except:
                        pass
                else:
                    logger.error(f"Redis error in consume_task_changes: {e}")
                    logger.error(traceback.format_exc())
                    await asyncio.sleep(1)
            except Exception as e:
                logger.error(f"Error in consume_task_changes: {e}", exc_info=True)
                await asyncio.sleep(1)

    async def _update_tasks_by_event(self, id_tuples: List[tuple]) -> Set[tuple]:
        """基于事件ID批量更新任务状态

        Args:
            id_tuples: 元组列表，每个元组为 (stream_id, task_key)

        Returns:
            成功更新的元组集合
        """
        if not id_tuples:
            return set()

        successful_tuples = set()

        try:
            pipeline = self.redis_client.pipeline()
            for stream_id, task_key in id_tuples:
                pipeline.hgetall(task_key)

            redis_values = await pipeline.execute()
            updates = []
            valid_tuples = []  # 记录有效的元组

            if len(id_tuples) != len(redis_values):
                logger.error(f'Mismatch: {len(id_tuples)=} {len(redis_values)=}')
                # 不抛出异常，继续处理能处理的

            for i, (stream_id, task_key) in enumerate(id_tuples):
                if i >= len(redis_values):
                    logger.error(f'Missing redis value for task_key={task_key}')
                    continue

                hash_data = redis_values[i]

                if not hash_data:
                    logger.debug(f'No hash data for task_key={task_key}')
                    continue

                try:
                    # 从task_key解析出consumer_group
                    # task_key格式: namespace:TASK:stream_id:group_name
                    # 其中group_name就是完整的consumer_group（格式: jettask:QUEUE:queue_name:task_name）
                    parts = task_key.split(':', 3)  # 最多分割成4部分
                    if len(parts) == 4:
                        # parts[0] = namespace (如 'default')
                        # parts[1] = 'TASK'
                        # parts[2] = stream_id
                        # parts[3] = group_name (consumer_group)
                        consumer_group = parts[3]  # 直接使用group_name作为consumer_group
                        logger.debug(f"Extracted consumer_group from task_key: {consumer_group}")
                    else:
                        logger.warning(f"Cannot parse consumer_group from task_key: {task_key}")
                        continue

                    # 从consumer_group中提取task_name
                    # consumer_group格式: prefix:QUEUE:queue:task_name (如 jettask:QUEUE:robust_bench2:robust_benchmark.benchmark_task)
                    task_name = None
                    if consumer_group:
                        parts = consumer_group.split(':')
                        if len(parts) >= 4:
                            # 最后一部分是task_name
                            task_name = parts[-1]
                            logger.debug(f"Extracted task_name '{task_name}' from consumer_group '{consumer_group}'")

                    # 使用stream_id作为任务ID
                    update_info = self._parse_task_hash(stream_id, hash_data)
                    if update_info:
                        # 添加consumer_group和task_name到更新信息中
                        update_info['consumer_group'] = consumer_group
                        update_info['task_name'] = task_name or 'unknown'  # 如果无法提取task_name，使用'unknown'
                        # consumer_name就是worker_id（执行任务的实际worker）
                        update_info['consumer_name'] = update_info.get('worker_id')
                        updates.append(update_info)
                        valid_tuples.append((stream_id, task_key))
                    else:
                        logger.debug(f'Failed to parse stream_id={stream_id} hash_data={hash_data}')
                except Exception as e:
                    logger.error(f'Error parsing task stream_id={stream_id}: {e}')
                    continue

            if updates:
                logger.info(f"Attempting to update {len(updates)} tasks, first few: {[u['id'] for u in updates[:3]]}")
                try:
                    # _update_tasks 现在返回成功更新的ID集合
                    batch_successful = await self._update_tasks(updates)
                    # 将成功的stream_id映射回元组
                    for stream_id in batch_successful:
                        for tuple_item in valid_tuples:
                            if tuple_item[0] == stream_id:  # stream_id匹配
                                successful_tuples.add(tuple_item)
                    if batch_successful:
                        logger.info(f"Successfully updated {len(batch_successful)} tasks from change events")
                    else:
                        logger.warning(f"No tasks were successfully updated")
                except Exception as e:
                    logger.error(f"Error in batch update: {e}")
                    # 批量更新失败，尝试逐个更新
                    for update, tuple_item in zip(updates, valid_tuples):
                        try:
                            single_successful = await self._update_tasks([update])
                            if update['id'] in single_successful:
                                successful_tuples.add(tuple_item)
                        except Exception as single_error:
                            logger.error(f"Failed to update task {tuple_item[0]}: {single_error}")

        except Exception as e:
            logger.error(f"Error updating tasks by event: {e}", exc_info=True)

        logger.debug(f'{successful_tuples=}')
        return successful_tuples

    def _parse_task_hash(self, task_id: str, hash_data: dict) -> Optional[dict]:
        """解析Redis Hash数据"""
        update_info = {
            'id': task_id,
            'status': None,
            'result': None,
            'error_message': None,
            'started_at': None,
            'completed_at': None,
            'worker_id': None,
            'execution_time': None,
            'duration': None
        }

        try:
            from jettask.utils.serializer import loads_str

            hash_dict = {}
            for k, v in hash_data.items():
                key = k.decode('utf-8') if isinstance(k, bytes) else k
                if isinstance(v, bytes):
                    try:
                        value = loads_str(v)
                        if isinstance(value, (dict, list)):
                            value = json.dumps(value, ensure_ascii=False)
                        else:
                            value = str(value)
                    except:
                        try:
                            value = v.decode('utf-8')
                        except:
                            value = str(v)
                else:
                    value = v
                hash_dict[key] = value

            update_info['status'] = hash_dict.get('status')
            update_info['error_message'] = hash_dict.get('error_msg') or hash_dict.get('exception')

            # 转换时间戳
            for time_field in ['started_at', 'completed_at']:
                if hash_dict.get(time_field):
                    try:
                        time_str = hash_dict[time_field]
                        if isinstance(time_str, str) and time_str.startswith("b'") and time_str.endswith("'"):
                            time_str = time_str[2:-1]
                        update_info[time_field] = datetime.fromtimestamp(float(time_str), tz=timezone.utc)
                    except:
                        pass

            update_info['worker_id'] = hash_dict.get('consumer') or hash_dict.get('worker_id')

            # 转换数值 - 直接存储原始秒数值
            for num_field in ['execution_time', 'duration']:
                if hash_dict.get(num_field):
                    try:
                        num_str = hash_dict[num_field]
                        # 直接存储浮点数秒值
                        update_info[num_field] = float(num_str)
                    except:
                        pass

            # 处理result
            if 'result' in hash_dict:
                result_str = hash_dict['result']
                if result_str == 'null':
                    update_info['result'] = None
                else:
                    update_info['result'] = result_str

            # 只返回有数据的更新
            if any(v is not None for k, v in update_info.items() if k != 'id'):
                return update_info

        except Exception as e:
            logger.error(f"Failed to parse hash data for task {task_id}: {e}")

        return None

    async def _update_tasks(self, updates: List[Dict[str, Any]]) -> Set[str]:
        """批量更新任务状态（使用UPSERT逻辑处理task_runs表）

        Returns:
            成功更新的stream_id集合
        """
        if not updates:
            return set()

        try:
            async with self.AsyncSessionLocal() as session:
                # V3结构：使用UPSERT逻辑处理task_runs表
                stream_ids = [u['id'] for u in updates]
                logger.info(f"Upserting {len(stream_ids)} task_runs records")

                # 对于分区表，我们需要使用不同的UPSERT策略
                # 先尝试UPDATE，如果没有更新到任何行，则INSERT
                upsert_query = text("""
                    WITH updated AS (
                        UPDATE task_runs SET
                            consumer_name = COALESCE(CAST(:consumer_name AS TEXT), consumer_name),
                            status = CASE
                                WHEN CAST(:status AS TEXT) IS NULL THEN status
                                WHEN status = 'pending' THEN COALESCE(CAST(:status AS TEXT), status)
                                WHEN status = 'running' AND CAST(:status AS TEXT) IN ('success', 'failed', 'timeout', 'skipped') THEN CAST(:status AS TEXT)
                                WHEN status IN ('success', 'failed', 'timeout', 'skipped') THEN status
                                ELSE COALESCE(CAST(:status AS TEXT), status)
                            END,
                            result = CASE
                                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND CAST(:status AS TEXT) NOT IN ('success', 'failed', 'timeout', 'skipped') THEN result
                                ELSE COALESCE(CAST(:result AS jsonb), result)
                            END,
                            error_message = CASE
                                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND CAST(:status AS TEXT) NOT IN ('success', 'failed', 'timeout', 'skipped') THEN error_message
                                ELSE COALESCE(CAST(:error_message AS TEXT), error_message)
                            END,
                            start_time = COALESCE(CAST(:started_at AS TIMESTAMPTZ), start_time),
                            end_time = CASE
                                WHEN status IN ('success', 'failed', 'timeout', 'skipped') AND CAST(:status AS TEXT) NOT IN ('success', 'failed', 'timeout', 'skipped') THEN end_time
                                ELSE COALESCE(CAST(:completed_at AS TIMESTAMPTZ), end_time)
                            END,
                            worker_id = COALESCE(CAST(:worker_id AS TEXT), worker_id),
                            duration = COALESCE(CAST(:duration AS DOUBLE PRECISION), duration),
                            execution_time = COALESCE(CAST(:execution_time AS DOUBLE PRECISION), execution_time),
                            updated_at = CURRENT_TIMESTAMP
                        WHERE stream_id = :stream_id AND consumer_group = :consumer_group
                        RETURNING stream_id
                    )
                    INSERT INTO task_runs (
                        stream_id, task_name, consumer_group, consumer_name, status, result, error_message,
                        start_time, end_time, worker_id, duration, execution_time,
                        created_at, updated_at
                    )
                    SELECT
                        :stream_id, :task_name, :consumer_group, :consumer_name,
                        COALESCE(CAST(:status AS TEXT), 'pending'),
                        CAST(:result AS jsonb),
                        CAST(:error_message AS TEXT),
                        CAST(:started_at AS TIMESTAMPTZ),
                        CAST(:completed_at AS TIMESTAMPTZ),
                        CAST(:worker_id AS TEXT),
                        CAST(:duration AS DOUBLE PRECISION),
                        CAST(:execution_time AS DOUBLE PRECISION),
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    WHERE NOT EXISTS (SELECT 1 FROM updated)
                    RETURNING stream_id;
                """)

                # 为每个更新转换参数名称（从id改为stream_id）
                run_updates = []
                for update in updates:
                    run_update = update.copy()
                    run_update['stream_id'] = run_update.pop('id')  # 将id改为stream_id
                    # consumer_group 已经在 update_info 中了，不需要额外处理
                    run_updates.append(run_update)

                # 批量执行UPSERT - 使用事务批处理提高性能
                successful_count = 0
                batch_size = 20  # 每批处理20条记录

                for i in range(0, len(run_updates), batch_size):
                    batch = run_updates[i:i+batch_size]

                    try:
                        # 在一个事务中处理整批
                        for run_update in batch:
                            result = await session.execute(upsert_query, run_update)
                            if result.rowcount > 0:
                                successful_count += 1

                        # 批量提交
                        await session.commit()
                        logger.debug(f"Batch {i//batch_size + 1} committed: {len(batch)} records")

                    except Exception as e:
                        logger.error(f"Batch {i//batch_size + 1} failed, trying individual records: {e}")
                        await session.rollback()

                        # 如果批处理失败，回退到逐个处理这批记录
                        for run_update in batch:
                            try:
                                result = await session.execute(upsert_query, run_update)
                                await session.commit()
                                if result.rowcount > 0:
                                    successful_count += 1
                            except Exception as individual_error:
                                logger.error(f"Individual upsert failed for {run_update.get('stream_id')}: {individual_error}")
                                await session.rollback()

                # 记录成功更新的数量
                if successful_count > 0:
                    logger.info(f"Upserted {successful_count}/{len(run_updates)} task_runs records")

                # 检查哪些任务是完成状态，需要从Redis中删除
                completed_task_keys = []
                for update in updates:
                    status = update.get('status')
                    # 如果状态是完成状态（success, error, cancel等）
                    if status in ['success', 'error', 'failed', 'cancel', 'cancelled', 'timeout', 'skipped']:
                        # 构建task_key
                        # task_key格式: namespace:TASK:stream_id:group_name
                        stream_id = update['id']
                        consumer_group = update.get('consumer_group')
                        if consumer_group:
                            # 从consumer_group提取namespace
                            # consumer_group格式: prefix:QUEUE:queue:task_name
                            parts = consumer_group.split(':', 1)
                            namespace = parts[0] if parts else 'default'
                            task_key = f"{namespace}:TASK:{stream_id}:{consumer_group}"
                            completed_task_keys.append(task_key)
                            logger.info(f"Task {stream_id} with status {status} will be deleted from Redis: {task_key}")

                # 从Redis中删除已完成的任务
                if completed_task_keys:
                    try:
                        pipeline = self.redis_client.pipeline()
                        for task_key in completed_task_keys:
                            pipeline.delete(task_key)
                        deleted_results = await pipeline.execute()
                        deleted_count = sum(1 for r in deleted_results if r > 0)
                        if deleted_count > 0:
                            logger.info(f"Deleted {deleted_count} completed tasks from Redis")
                    except Exception as e:
                        logger.error(f"Error deleting completed tasks from Redis: {e}")

                # UPSERT 操作总是成功的，返回所有stream_id
                # 不需要复杂的错误处理，因为UPSERT保证了操作的原子性
                return set(stream_ids)

        except Exception as e:
            logger.error(f"Error upserting task statuses: {e}")
            logger.error(traceback.format_exc())
            return set()  # 出错时返回空集

    async def _retry_pending_updates(self):
        """定期重试待更新的任务"""
        while self._running:
            try:
                await asyncio.sleep(self._retry_interval)  # 等待一段时间

                # 获取待重试的更新
                async with self._pending_updates_lock:
                    if not self._pending_updates:
                        continue

                    # 取出所有待重试的更新
                    pending_items = list(self._pending_updates.items())
                    self._pending_updates.clear()

                if pending_items:
                    # 重新尝试更新
                    updates = [update_info for _, update_info in pending_items]
                    logger.debug(f"Retrying {len(pending_items)} pending task updates")
                    await self._update_tasks(updates)

            except Exception as e:
                logger.error(f"Error in retry pending updates: {e}")
                await asyncio.sleep(5)
