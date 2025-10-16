"""
PostgreSQL Consumer V2 - 支持多消费者组的双表结构
"""
import logging
import json
from typing import Optional, Dict, Any, List
from datetime import datetime
import asyncio
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import asyncpg

logger = logging.getLogger(__name__)


class PGConsumerV2:
    """PostgreSQL消费者V2 - 支持多消费者组"""
    
    def __init__(self, pg_url: str, redis_prefix: str = 'jettask'):
        self.pg_url = pg_url
        self.redis_prefix = redis_prefix
        self.conn = None
        self.async_conn = None
        
    def connect(self):
        """建立同步数据库连接"""
        if not self.conn or self.conn.closed:
            self.conn = psycopg2.connect(self.pg_url)
            self.conn.autocommit = False
            
    async def async_connect(self):
        """建立异步数据库连接"""
        if not self.async_conn:
            self.async_conn = await asyncpg.connect(self.pg_url)
            
    def close(self):
        """关闭同步连接"""
        if self.conn:
            self.conn.close()
            self.conn = None
            
    async def async_close(self):
        """关闭异步连接"""
        if self.async_conn:
            await self.async_conn.close()
            self.async_conn = None
            
    def ensure_tables(self):
        """确保数据表存在"""
        from .sql_utils import execute_sql_file
        self.connect()
        try:
            with self.conn.cursor() as cursor:
                # 检查新表是否存在
                cursor.execute("""
                    SELECT EXISTS (
                        SELECT 1 FROM information_schema.tables 
                        WHERE table_name = 'tasks'
                    )
                """)
                if not cursor.fetchone()[0]:
                    # 使用新的SQL执行函数
                    sql_path = '/home/yuyang/easy-task/jettask/pg_consumer/sql/create_new_tables.sql'
                    execute_sql_file(self.conn, sql_path)
                    logger.info("Created new table structure for multi-consumer group support")
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error ensuring tables: {e}")
            raise
            
    async def async_ensure_tables(self):
        """异步确保数据表存在"""
        from .sql_utils import split_sql_statements
        await self.async_connect()
        try:
            # 检查新表是否存在，并且有正确的列
            exists = await self.async_conn.fetchval("""
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_name = 'tasks' AND column_name = 'stream_id'
                )
            """)
            if not exists:
                logger.info("Creating new table structure...")
                # 执行创建表的SQL
                with open('/home/yuyang/easy-task/jettask/pg_consumer/sql/create_new_tables.sql', 'r') as f:
                    sql_content = f.read()
                    # 使用智能分割函数
                    statements = split_sql_statements(sql_content)
                    for i, stmt in enumerate(statements, 1):
                        try:
                            logger.debug(f"执行第 {i}/{len(statements)} 个SQL语句")
                            await self.async_conn.execute(stmt)
                        except Exception as e:
                            # 忽略已存在的对象错误
                            if 'already exists' not in str(e):
                                logger.warning(f"Error executing statement {i}: {e}")
                                logger.debug(f"Statement: {stmt[:100]}...")
                logger.info("Created new table structure for multi-consumer group support")
        except Exception as e:
            logger.error(f"Error ensuring tables: {e}")
            raise
    
    def record_task(self, event_id: str, event_data: Dict[str, Any], 
                    queue: str, consumer_group: str) -> int:
        """
        记录任务信息（同步方法）
        返回task_id
        """
        self.connect()
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # 1. 插入或获取任务基础信息
                task_name = event_data.get('_task_name', event_data.get('name', 'unknown'))
                
                # 尝试插入任务，如果已存在则忽略
                cursor.execute("""
                    INSERT INTO tasks (
                        stream_id, queue, task_name, task_type, 
                        payload, priority, source, metadata
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (stream_id) DO UPDATE
                    SET updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    event_id,
                    queue,
                    task_name,
                    event_data.get('event_type', 'task'),
                    Json(event_data),
                    event_data.get('priority', 0),
                    event_data.get('source', 'stream'),
                    Json({'consumer_group': consumer_group})
                ))
                
                task_id = cursor.fetchone()['id']
                
                # 2. 插入任务运行记录
                consumer_name = event_data.get('consumer', '')
                worker_id = event_data.get('worker_id', consumer_name)
                
                cursor.execute("""
                    INSERT INTO task_runs (
                        task_id, stream_id, consumer_group, 
                        consumer_name, worker_id, status
                    ) VALUES (
                        %s, %s, %s, %s, %s, %s
                    )
                    ON CONFLICT (task_id, consumer_group) DO UPDATE
                    SET 
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    task_id,
                    event_id,
                    consumer_group,
                    consumer_name,
                    worker_id,
                    'pending'
                ))
                
                self.conn.commit()
                return task_id
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error recording task: {e}")
            raise
            
    async def async_record_task(self, event_id: str, event_data: Dict[str, Any],
                                queue: str, consumer_group: str) -> int:
        """
        异步记录任务信息
        返回task_id
        """
        await self.async_connect()
        try:
            task_name = event_data.get('_task_name', event_data.get('name', 'unknown'))
            
            # 使用事务
            async with self.async_conn.transaction():
                # 1. 插入或获取任务基础信息
                task_id = await self.async_conn.fetchval("""
                    INSERT INTO tasks (
                        stream_id, queue, namespace, scheduled_task_id,
                        payload, priority, source, metadata
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, $8
                    )
                    ON CONFLICT (stream_id) DO UPDATE
                    SET metadata = EXCLUDED.metadata
                    RETURNING id
                """, 
                    event_id,
                    queue,
                    namespace,
                    scheduled_task_id,
                    json.dumps(event_data),
                    event_data.get('priority', 0),
                    event_data.get('source', 'stream'),
                    json.dumps({'consumer_group': consumer_group})
                )
                
                # 2. 插入任务运行记录
                consumer_name = event_data.get('consumer', '')
                worker_id = event_data.get('worker_id', consumer_name)
                
                await self.async_conn.execute("""
                    INSERT INTO task_runs (
                        task_id, stream_id, task_name, consumer_group,
                        consumer_name, worker_id, status, created_at
                    ) VALUES (
                        $1, $2, $3, $4, $5, $6, $7, CURRENT_TIMESTAMP
                    )
                    ON CONFLICT (task_id, consumer_group) DO UPDATE
                    SET 
                        status = EXCLUDED.status,
                        updated_at = CURRENT_TIMESTAMP
                """,
                    task_id,
                    event_id,
                    task_name,
                    consumer_group,
                    consumer_name,
                    worker_id,
                    'pending'
                )
                
            return task_id
            
        except Exception as e:
            logger.error(f"Error recording task async: {e}")
            raise
            
    def update_task_status(self, event_id: str, consumer_group: str, 
                          status: str, **kwargs) -> bool:
        """
        更新任务执行状态（同步方法）
        """
        self.connect()
        try:
            with self.conn.cursor() as cursor:
                # 构建更新字段
                update_fields = ['status = %s', 'updated_at = CURRENT_TIMESTAMP']
                update_values = [status]
                
                # 处理可选字段
                if 'end_time' in kwargs:
                    update_fields.append('end_time = %s')
                    update_values.append(kwargs['end_time'])
                    
                if 'error_message' in kwargs:
                    update_fields.append('error_message = %s')
                    update_values.append(kwargs['error_message'])
                    
                if 'error_details' in kwargs:
                    update_fields.append('error_details = %s')
                    update_values.append(Json(kwargs['error_details']))
                    
                if 'result' in kwargs:
                    update_fields.append('result = %s')
                    update_values.append(Json(kwargs['result']))
                    
                if 'retry_count' in kwargs:
                    update_fields.append('retry_count = %s')
                    update_values.append(kwargs['retry_count'])
                
                # 添加WHERE条件的值
                update_values.extend([event_id, consumer_group])
                
                # 更新task_runs表
                cursor.execute(f"""
                    UPDATE task_runs
                    SET {', '.join(update_fields)}
                    WHERE stream_id = %s AND consumer_group = %s
                """, update_values)
                
                # tasks表已经没有status字段，不需要更新总体状态
                
                self.conn.commit()
                return cursor.rowcount > 0
                
        except Exception as e:
            self.conn.rollback()
            logger.error(f"Error updating task status: {e}")
            return False
            
    async def async_update_task_status(self, event_id: str, consumer_group: str,
                                      status: str, **kwargs) -> bool:
        """
        异步更新任务执行状态
        """
        await self.async_connect()
        try:
            async with self.async_conn.transaction():
                # 构建更新语句
                set_clauses = ['status = $1', 'updated_at = CURRENT_TIMESTAMP']
                values = [status]
                param_count = 1
                
                # 添加可选字段
                for field, db_field in [
                    ('end_time', 'end_time'),
                    ('error_message', 'error_message'),
                    ('retry_count', 'retry_count')
                ]:
                    if field in kwargs:
                        param_count += 1
                        set_clauses.append(f'{db_field} = ${param_count}')
                        values.append(kwargs[field])
                        
                # JSON字段
                for field, db_field in [
                    ('error_details', 'error_details'),
                    ('result', 'result')
                ]:
                    if field in kwargs:
                        param_count += 1
                        set_clauses.append(f'{db_field} = ${param_count}::jsonb')
                        values.append(json.dumps(kwargs[field]))
                
                # 添加WHERE条件的值
                values.extend([event_id, consumer_group])
                
                # 更新task_runs表
                await self.async_conn.execute(f"""
                    UPDATE task_runs
                    SET {', '.join(set_clauses)}
                    WHERE stream_id = ${param_count + 1} 
                    AND consumer_group = ${param_count + 2}
                """, *values)
                
                # tasks表已经没有status字段，不需要更新总体状态
                    
            return True
            
        except Exception as e:
            logger.error(f"Error updating task status async: {e}")
            return False
            
    def get_task_info(self, event_id: str) -> Optional[Dict]:
        """获取任务信息（包括所有消费者组的执行情况）"""
        self.connect()
        try:
            with self.conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute("""
                    SELECT 
                        t.*,
                        array_agg(
                            json_build_object(
                                'consumer_group', tr.consumer_group,
                                'status', tr.status,
                                'start_time', tr.start_time,
                                'end_time', tr.end_time,
                                'duration_ms', tr.duration_ms,
                                'error_message', tr.error_message,
                                'retry_count', tr.retry_count
                            )
                        ) FILTER (WHERE tr.id IS NOT NULL) as runs
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.id = tr.task_id
                    WHERE t.stream_id = %s
                    GROUP BY t.id
                """, (event_id,))
                
                return cursor.fetchone()
                
        except Exception as e:
            logger.error(f"Error getting task info: {e}")
            return None
            
    async def async_get_task_info(self, event_id: str) -> Optional[Dict]:
        """异步获取任务信息"""
        await self.async_connect()
        try:
            row = await self.async_conn.fetchrow("""
                SELECT 
                    t.*,
                    array_agg(
                        json_build_object(
                            'consumer_group', tr.consumer_group,
                            'status', tr.status,
                            'start_time', tr.start_time,
                            'end_time', tr.end_time,
                            'duration_ms', tr.duration_ms,
                            'error_message', tr.error_message,
                            'retry_count', tr.retry_count
                        )
                    ) FILTER (WHERE tr.id IS NOT NULL) as runs
                FROM tasks t
                LEFT JOIN task_runs tr ON t.id = tr.task_id
                WHERE t.stream_id = $1
                GROUP BY t.id
            """, event_id)
            
            return dict(row) if row else None
            
        except Exception as e:
            logger.error(f"Error getting task info async: {e}")
            return None