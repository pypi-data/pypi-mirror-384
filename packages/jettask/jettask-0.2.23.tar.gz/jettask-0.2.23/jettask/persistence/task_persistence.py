"""任务持久化模块

负责解析Redis Stream消息，并将任务数据批量插入PostgreSQL数据库。
"""

import json
import logging
import traceback
from typing import Dict, List, Optional, Any
from datetime import datetime, timezone

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class TaskPersistence:
    """任务持久化处理器

    职责：
    - 解析Stream消息为任务信息
    - 批量插入任务到PostgreSQL的tasks表
    - 处理插入失败的降级策略
    """

    def __init__(
        self,
        async_session_local: sessionmaker,
        namespace_id: str,
        namespace_name: str
    ):
        """初始化任务持久化处理器

        Args:
            async_session_local: SQLAlchemy会话工厂
            namespace_id: 命名空间ID
            namespace_name: 命名空间名称
        """
        self.AsyncSessionLocal = async_session_local
        self.namespace_id = namespace_id
        self.namespace_name = namespace_name

    def parse_stream_message(self, task_id: str, data: dict) -> Optional[dict]:
        """解析Stream消息为任务信息（返回完整的字段）

        Args:
            task_id: 任务ID（Redis Stream ID）
            data: 消息数据

        Returns:
            解析后的任务信息字典，失败返回None
        """
        try:
            from jettask.utils.serializer import loads_str

            if b'data' in data:
                task_data = loads_str(data[b'data'])
            else:
                task_data = {}
                for k, v in data.items():
                    key = k.decode('utf-8') if isinstance(k, bytes) else k
                    if isinstance(v, bytes):
                        try:
                            value = loads_str(v)
                        except:
                            value = str(v)
                    else:
                        value = v
                    task_data[key] = value

            # 如果配置了命名空间，检查消息是否属于该命名空间
            # if self.namespace_id:
            #     msg_namespace_id = task_data.get('__namespace_id')
            #     # 如果消息没有namespace_id且当前不是默认命名空间，跳过
            #     if msg_namespace_id != self.namespace_id:
            #         if not (msg_namespace_id is None and self.namespace_id == 'default'):
            #             logger.debug(f"Skipping message from different namespace: {msg_namespace_id} != {self.namespace_id}")
            #             return None

            queue_name = task_data['queue']
            task_name = task_data.get('name', task_data.get('task', 'unknown'))

            created_at = None
            if 'trigger_time' in task_data:
                try:
                    timestamp = float(task_data['trigger_time'])
                    created_at = datetime.fromtimestamp(timestamp, tz=timezone.utc)
                except:
                    pass

            # 返回完整的字段，包括所有可能为None的字段
            return {
                'id': task_id,
                'queue_name': queue_name,
                'task_name': task_name,
                'task_data': json.dumps(task_data),
                'priority': int(task_data.get('priority', 0)),
                'retry_count': int(task_data.get('retry', 0)),
                'max_retry': int(task_data.get('max_retry', 3)),
                'status': 'pending',
                'result': None,  # 新任务没有结果
                'error_message': None,  # 新任务没有错误信息
                'created_at': created_at,
                'started_at': None,  # 新任务还未开始
                'completed_at': None,  # 新任务还未完成
                'scheduled_task_id': task_data.get('scheduled_task_id'),  # 调度任务ID
                'metadata': json.dumps(task_data.get('metadata', {})),
                'worker_id': None,  # 新任务还未分配worker
                'execution_time': None,  # 新任务还没有执行时间
                'duration': None,  # 新任务还没有持续时间
                'namespace_id': self.namespace_id  # 添加命名空间ID
            }

        except Exception as e:
            logger.error(f"Error parsing stream message for task {task_id}: {e}")
            logger.error(traceback.format_exc())
            return None

    async def insert_tasks(self, tasks: List[Dict[str, Any]]) -> int:
        """批量插入任务到PostgreSQL（只处理tasks表）

        Args:
            tasks: 任务信息列表

        Returns:
            实际插入的记录数
        """
        if not tasks:
            return 0

        logger.info(f"Attempting to insert {len(tasks)} tasks to tasks table")

        try:
            async with self.AsyncSessionLocal() as session:
                # 插入tasks表 - 使用批量INSERT忽略冲突
                # 由于stream_id在实践中是唯一的，我们可以简单地忽略重复
                tasks_query = text("""
                    INSERT INTO tasks (stream_id, queue, namespace, scheduled_task_id,
                                      payload, priority, created_at, source, metadata)
                    VALUES (:stream_id, :queue, :namespace, :scheduled_task_id,
                           CAST(:payload AS jsonb), :priority, :created_at, :source, CAST(:metadata AS jsonb))
                    ON CONFLICT DO NOTHING
                    RETURNING stream_id;
                """)

                # 准备tasks表的数据
                tasks_data = []
                for task in tasks:
                    task_data = json.loads(task['task_data'])

                    # 从task_data中获取scheduled_task_id
                    scheduled_task_id = task_data.get('scheduled_task_id') or task.get('scheduled_task_id')

                    # 根据是否有scheduled_task_id来判断任务来源
                    if scheduled_task_id:
                        source = 'scheduler'  # 定时任务
                    else:
                        source = 'redis_stream'  # 普通任务

                    tasks_data.append({
                        'stream_id': task['id'],  # Redis Stream ID作为stream_id
                        'queue': task['queue_name'],
                        'namespace': self.namespace_name,
                        'scheduled_task_id': str(scheduled_task_id) if scheduled_task_id else None,
                        'payload': task['task_data'],  # 完整的任务数据
                        'priority': task['priority'],
                        'created_at': task['created_at'],
                        'source': source,
                        'metadata': task.get('metadata', '{}')
                    })

                # 批量插入 - 使用executemany提高性能
                logger.debug(f"Executing batch insert with {len(tasks_data)} tasks")

                try:
                    # 使用executemany批量插入
                    result = await session.execute(tasks_query, tasks_data)

                    # 获取实际插入的记录数
                    inserted_count = result.rowcount

                    await session.commit()
                    logger.debug("Tasks table batch insert transaction completed")
                    return inserted_count

                except Exception as e:
                    logger.error(f"Error in batch insert, trying fallback: {e}")
                    await session.rollback()

                    # 如果批量插入失败，降级为小批量插入（每批10条）
                    batch_size = 10
                    total_inserted = 0

                    for i in range(0, len(tasks_data), batch_size):
                        batch = tasks_data[i:i+batch_size]
                        try:
                            result = await session.execute(tasks_query, batch)
                            batch_inserted = result.rowcount
                            if batch_inserted > 0:
                                total_inserted += batch_inserted
                            await session.commit()
                        except Exception as batch_error:
                            logger.error(f"Batch {i//batch_size + 1} failed: {batch_error}")
                            await session.rollback()

                    if total_inserted > 0:
                        logger.info(f"Fallback insert completed: {total_inserted} tasks inserted")
                    else:
                        logger.info(f"No new tasks inserted in fallback mode")

                    return total_inserted

        except Exception as e:
            logger.error(f"Error inserting tasks to PostgreSQL: {e}")
            logger.error(traceback.format_exc())
            return 0
