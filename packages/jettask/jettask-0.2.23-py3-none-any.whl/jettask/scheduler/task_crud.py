"""
定时任务管理器 - 负责数据库CRUD操作
"""
import asyncio
import asyncpg
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta
import json

from .models import ScheduledTask, TaskExecutionHistory, TaskType, TaskStatus


class ScheduledTaskManager:
    """定时任务数据库管理器"""
    
    def __init__(self, app_or_db_url):
        """
        初始化管理器
        
        Args:
            app_or_db_url: Jettask应用实例或PostgreSQL连接URL字符串
        """
        # 支持两种初始化方式：传入app对象或直接传入db_url
        if isinstance(app_or_db_url, str):
            self.db_url = app_or_db_url
        else:
            # 从app对象获取pg_url
            self.db_url = app_or_db_url.pg_url
        
        # 将SQLAlchemy格式的URL转换为原生PostgreSQL URL
        # postgresql+asyncpg:// -> postgresql://
        if self.db_url and '+' in self.db_url:
            self.db_url = self.db_url.split('+')[0] + self.db_url[self.db_url.index('://'):]
        
        self.pool: Optional[asyncpg.Pool] = None
    
    async def connect(self):
        """建立数据库连接池"""
        if not self.pool:
            self.pool = await asyncpg.create_pool(
                self.db_url,
                min_size=2,
                max_size=10,
                command_timeout=60
            )
    
    async def disconnect(self):
        """关闭数据库连接池"""
        if self.pool:
            await self.pool.close()
            self.pool = None
    
    async def init_schema(self):
        """初始化数据库表结构（幂等操作）"""
        import os
        schema_path = os.path.join(os.path.dirname(__file__), 'schema.sql')
        
        with open(schema_path, 'r') as f:
            schema_sql = f.read()
        
        async with self.pool.acquire() as conn:
            # 使用事务，忽略已存在的对象错误
            try:
                await conn.execute(schema_sql)
            except Exception as e:
                if "already exists" in str(e):
                    # 表或索引已存在，这是正常的
                    pass
                else:
                    # 其他错误则重新抛出
                    raise
    
    # ==================== 任务CRUD操作 ====================
    
    async def create_task(self, task: ScheduledTask) -> ScheduledTask:
        """创建定时任务"""
        sql = """
            INSERT INTO scheduled_tasks (
                scheduler_id, task_name, task_type, queue_name, namespace,
                task_args, task_kwargs, cron_expression, interval_seconds,
                next_run_time, enabled, max_retries, retry_delay, timeout,
                priority, description, tags, metadata
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13, $14, $15, $16, $17, $18)
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                task.scheduler_id,
                task.task_name,
                task.task_type.value,
                task.queue_name,
                task.namespace,  # 添加namespace
                json.dumps(task.task_args),
                json.dumps(task.task_kwargs),
                task.cron_expression,
                task.interval_seconds,
                task.next_run_time,
                task.enabled,
                task.max_retries,
                task.retry_delay,
                task.timeout,
                task.priority,
                task.description,
                json.dumps(task.tags),
                json.dumps(task.metadata)
            )
            
            return self._row_to_task(row)
    
    async def get_task(self, task_id: int) -> Optional[ScheduledTask]:
        """获取单个任务"""
        sql = "SELECT * FROM scheduled_tasks WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql, task_id)
            if row:
                return self._row_to_task(row)
            return None
    
    async def get_task_by_scheduler_id(self, scheduler_id: str) -> Optional[ScheduledTask]:
        """通过scheduler_id获取任务"""
        sql = "SELECT * FROM scheduled_tasks WHERE scheduler_id = $1"
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(sql, scheduler_id)
            if row:
                return self._row_to_task(row)
            return None
    
    async def update_task(self, task: ScheduledTask) -> ScheduledTask:
        """更新任务"""
        sql = """
            UPDATE scheduled_tasks SET
                scheduler_id = $2,
                task_name = $3,
                task_type = $4,
                queue_name = $5,
                namespace = $6,
                task_args = $7,
                task_kwargs = $8,
                cron_expression = $9,
                interval_seconds = $10,
                next_run_time = $11,
                last_run_time = $12,
                enabled = $13,
                max_retries = $14,
                retry_delay = $15,
                timeout = $16,
                priority = $17,
                description = $18,
                tags = $19,
                metadata = $20
            WHERE id = $1
            RETURNING *
        """
        
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                sql,
                task.id,
                task.scheduler_id,
                task.task_name,
                task.task_type.value,
                task.queue_name,
                task.namespace,  # 添加namespace
                json.dumps(task.task_args),
                json.dumps(task.task_kwargs),
                task.cron_expression,
                task.interval_seconds,
                task.next_run_time,
                task.last_run_time,
                task.enabled,
                task.max_retries,
                task.retry_delay,
                task.timeout,
                task.priority,
                task.description,
                json.dumps(task.tags),
                json.dumps(task.metadata)
            )
            
            return self._row_to_task(row)
    
    async def delete_task(self, task_id: int) -> bool:
        """删除任务"""
        sql = "DELETE FROM scheduled_tasks WHERE id = $1"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(sql, task_id)
            return result.split()[-1] != '0'
    
    async def list_tasks(
        self,
        enabled: Optional[bool] = None,
        task_type: Optional[TaskType] = None,
        queue_name: Optional[str] = None,
        limit: int = 100,
        offset: int = 0
    ) -> List[ScheduledTask]:
        """列出任务"""
        conditions = []
        params = []
        param_count = 0
        
        if enabled is not None:
            param_count += 1
            conditions.append(f"enabled = ${param_count}")
            params.append(enabled)
        
        if task_type is not None:
            param_count += 1
            conditions.append(f"task_type = ${param_count}")
            params.append(task_type.value)
        
        if queue_name is not None:
            param_count += 1
            conditions.append(f"queue_name = ${param_count}")
            params.append(queue_name)
        
        where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        
        param_count += 1
        limit_param = f"${param_count}"
        params.append(limit)
        
        param_count += 1
        offset_param = f"${param_count}"
        params.append(offset)
        
        sql = f"""
            SELECT * FROM scheduled_tasks
            {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit_param} OFFSET {offset_param}
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [self._row_to_task(row) for row in rows]
    
    async def get_ready_tasks(
        self,
        batch_size: int = 100,
        lookahead_seconds: int = 60
    ) -> List[ScheduledTask]:
        """
        获取即将执行的任务
        
        Args:
            batch_size: 批次大小
            lookahead_seconds: 向前查看的秒数
        """
        cutoff_time = datetime.now() + timedelta(seconds=lookahead_seconds)
        
        sql = """
            SELECT * FROM scheduled_tasks
            WHERE enabled = true 
                AND next_run_time <= $1
                AND next_run_time IS NOT NULL
            ORDER BY next_run_time
            LIMIT $2
        """
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, cutoff_time, batch_size)
            return [self._row_to_task(row) for row in rows]
    
    async def update_task_next_run(
        self,
        task_id: int,
        next_run_time: Optional[datetime],
        last_run_time: datetime
    ):
        """更新任务的下次执行时间"""
        sql = """
            UPDATE scheduled_tasks 
            SET next_run_time = $2, last_run_time = $3
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(sql, task_id, next_run_time, last_run_time)
    
    async def disable_once_task(self, task_id: int):
        """禁用一次性任务（只更新必要字段）"""
        sql = """
            UPDATE scheduled_tasks 
            SET enabled = false, next_run_time = NULL
            WHERE id = $1
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(sql, task_id)
    
    async def batch_update_next_run_times(self, updates: List[tuple]):
        """批量更新任务的下次执行时间和执行次数"""
        if not updates:
            return
        
        sql = """
            UPDATE scheduled_tasks 
            SET next_run_time = u.next_run_time, 
                last_run_time = u.last_run_time,
                execution_count = COALESCE(execution_count, 0) + 1
            FROM (VALUES ($1::int, $2::timestamptz, $3::timestamptz)) AS u(id, next_run_time, last_run_time)
            WHERE scheduled_tasks.id = u.id
        """
        
        async with self.pool.acquire() as conn:
            # 使用executemany批量更新
            await conn.executemany(sql, updates)
    
    async def batch_disable_once_tasks(self, task_ids: List[int]):
        """批量禁用一次性任务"""
        if not task_ids:
            return
        
        sql = """
            UPDATE scheduled_tasks 
            SET enabled = false, next_run_time = NULL
            WHERE id = ANY($1)
        """
        
        async with self.pool.acquire() as conn:
            await conn.execute(sql, task_ids)
    
    # ==================== 执行历史操作 ====================
    
    async def record_execution(self, history: TaskExecutionHistory):
        """记录任务执行历史到tasks表"""
        # 在tasks表中创建一条新的任务记录，关联到scheduled_task
        sql = """
            INSERT INTO tasks (
                queue_name, status, scheduled_task_id, scheduled_time,
                started_at, finished_at, duration_ms, worker_id,
                error_message, retry_count, result
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            RETURNING id
        """
        
        # 获取scheduled_task的队列名称
        task_info = await self.get_task(history.task_id)
        queue_name = task_info.queue_name if task_info else 'default'
        
        async with self.pool.acquire() as conn:
            task_id = await conn.fetchval(
                sql,
                queue_name,
                history.status.value,
                history.task_id,  # scheduled_task_id
                history.scheduled_time,
                history.started_at,
                history.finished_at,
                history.duration_ms,
                history.worker_id,
                history.error_message,
                history.retry_count,
                json.dumps(history.result) if history.result else None
            )
            return task_id
    
    async def get_task_history(
        self,
        task_id: int,
        limit: int = 100,
        status: Optional[TaskStatus] = None
    ) -> List[Dict[str, Any]]:
        """从tasks表获取任务执行历史"""
        if status:
            sql = """
                SELECT id, queue_name, status, scheduled_task_id,
                       scheduled_time, started_at, finished_at,
                       duration_ms, worker_id, error_message,
                       retry_count, result, created_at
                FROM tasks
                WHERE scheduled_task_id = $1 AND status = $2
                ORDER BY created_at DESC
                LIMIT $3
            """
            params = [task_id, status.value, limit]
        else:
            sql = """
                SELECT id, queue_name, status, scheduled_task_id,
                       scheduled_time, started_at, finished_at,
                       duration_ms, worker_id, error_message,
                       retry_count, result, created_at
                FROM tasks
                WHERE scheduled_task_id = $1
                ORDER BY created_at DESC
                LIMIT $2
            """
            params = [task_id, limit]
        
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(sql, *params)
            return [dict(row) for row in rows]
    
    async def cleanup_old_history(self, days: int = 30):
        """清理旧的执行历史"""
        cutoff_date = datetime.now() - timedelta(days=days)
        
        sql = "DELETE FROM tasks WHERE scheduled_task_id IS NOT NULL AND created_at < $1"
        
        async with self.pool.acquire() as conn:
            result = await conn.execute(sql, cutoff_date)
            return int(result.split()[-1])
    
    # ==================== 批量操作方法 ====================
    
    async def batch_record_executions(self, histories: List[TaskExecutionHistory]):
        """批量记录任务执行历史到tasks表"""
        if not histories:
            return
        
        # 获取所有scheduled_task的队列和名称信息
        task_ids = list(set(h.task_id for h in histories))
        task_info_map = {}
        
        if task_ids:
            async with self.pool.acquire() as conn:
                rows = await conn.fetch(
                    "SELECT id, queue_name, task_name FROM scheduled_tasks WHERE id = ANY($1)",
                    task_ids
                )
                task_info_map = {row['id']: {'queue_name': row['queue_name'], 'task_name': row['task_name']} for row in rows}
        
        sql = """
            INSERT INTO tasks (
                id, queue_name, task_name, status, scheduled_task_id, scheduled_time,
                started_at, finished_at, duration_ms, worker_id,
                error_message, retry_count, result
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13)
        """
        
        # 准备批量数据
        data = []
        for history in histories:
            task_info = task_info_map.get(history.task_id, {})
            queue_name = task_info.get('queue_name', 'default')
            task_name = task_info.get('task_name', 'scheduled_task')
            
            data.append((
                history.event_id,  # id字段使用event_id
                queue_name,
                task_name,  # task_name
                history.status.value if isinstance(history.status, TaskStatus) else history.status,
                history.task_id,  # scheduled_task_id
                history.scheduled_time,
                history.started_at,
                history.finished_at,
                history.duration_ms,
                history.worker_id,
                history.error_message,
                history.retry_count,
                json.dumps(history.result) if history.result else None
            ))
        
        async with self.pool.acquire() as conn:
            # 使用executemany批量插入
            await conn.executemany(sql, data)
    
    async def batch_update_tasks(self, tasks: List[ScheduledTask]):
        """批量更新任务"""
        if not tasks:
            return
        
        sql = """
            UPDATE scheduled_tasks SET
                scheduler_id = $2,
                task_name = $3,
                task_type = $4,
                queue_name = $5,
                task_args = $6,
                task_kwargs = $7,
                cron_expression = $8,
                interval_seconds = $9,
                next_run_time = $10,
                last_run_time = $11,
                enabled = $12,
                max_retries = $13,
                retry_delay = $14,
                timeout = $15,
                description = $16,
                metadata = $17,
                updated_at = $18
            WHERE id = $1
        """
        
        # 准备批量数据
        data = []
        now = datetime.now()
        for task in tasks:
            data.append((
                task.id,
                task.scheduler_id,
                task.task_name,
                task.task_type.value if isinstance(task.task_type, TaskType) else task.task_type,
                task.queue_name,
                json.dumps(task.task_args) if task.task_args else '[]',
                json.dumps(task.task_kwargs) if task.task_kwargs else '{}',
                task.cron_expression,
                task.interval_seconds,
                task.next_run_time,
                task.last_run_time,
                task.enabled,
                task.max_retries,
                task.retry_delay,
                task.timeout,
                task.description,
                json.dumps(task.metadata) if task.metadata else None,
                now
            ))
        
        async with self.pool.acquire() as conn:
            # 使用executemany批量更新
            await conn.executemany(sql, data)
    
    # ==================== 辅助方法 ====================
    
    def _row_to_task(self, row) -> ScheduledTask:
        """将数据库行转换为ScheduledTask对象"""
        from decimal import Decimal
        
        # 处理interval_seconds的Decimal类型
        interval_seconds = row['interval_seconds']
        if interval_seconds is not None and isinstance(interval_seconds, Decimal):
            interval_seconds = float(interval_seconds)
        
        return ScheduledTask(
            id=row['id'],
            scheduler_id=row['scheduler_id'],
            task_name=row['task_name'],
            task_type=TaskType(row['task_type']),
            queue_name=row['queue_name'],
            namespace=row.get('namespace', 'default'),  # 添加namespace字段
            task_args=row['task_args'] if isinstance(row['task_args'], list) else json.loads(row['task_args']),
            task_kwargs=row['task_kwargs'] if isinstance(row['task_kwargs'], dict) else json.loads(row['task_kwargs']),
            cron_expression=row['cron_expression'],
            interval_seconds=interval_seconds,
            next_run_time=row['next_run_time'],
            last_run_time=row['last_run_time'],
            enabled=row['enabled'],
            max_retries=row['max_retries'],
            retry_delay=row['retry_delay'],
            timeout=row['timeout'],
            priority=row.get('priority'),
            description=row['description'],
            tags=row['tags'] if isinstance(row['tags'], list) else (json.loads(row['tags']) if row['tags'] else []),
            metadata=row['metadata'] if isinstance(row['metadata'], dict) else (json.loads(row['metadata']) if row['metadata'] else None),
            created_at=row['created_at'],
            updated_at=row['updated_at']
        )
    
    def _row_to_history(self, row) -> Dict[str, Any]:
        """将数据库行转换为历史记录字典"""
        return {
            'id': row['id'],
            'scheduled_task_id': row['scheduled_task_id'],
            'status': row['status'],
            'scheduled_time': row['scheduled_time'],
            'started_at': row['started_at'],
            'finished_at': row['finished_at'],
            'duration_ms': row['duration_ms'],
            'worker_id': row['worker_id'],
            'error_message': row['error_message'],
            'retry_count': row['retry_count'],
            'result': row['result'] if isinstance(row['result'], dict) else json.loads(row['result']) if row['result'] else None,
            'created_at': row['created_at']
        }
    
    async def create_or_get_task(self, task: ScheduledTask, skip_if_exists: bool = True) -> tuple[ScheduledTask, bool]:
        """
        创建任务或获取已存在的任务
        
        Args:
            task: 任务对象
            skip_if_exists: 如果任务已存在是否跳过（True=跳过，False=抛出异常）
            
        Returns:
            (task, created): 任务对象和是否新创建的标志
        """
        if task.scheduler_id:
            # 先检查是否已存在
            existing = await self.get_task_by_scheduler_id(task.scheduler_id)
            if existing:
                if skip_if_exists:
                    return existing, False
                else:
                    raise ValueError(f"Task with scheduler_id '{task.scheduler_id}' already exists")
        
        # 创建新任务
        created_task = await self.create_task(task)
        return created_task, True
    
    async def batch_create_tasks(self, tasks: List[ScheduledTask], skip_existing: bool = True) -> List[ScheduledTask]:
        """
        批量创建任务（优化版本）
        
        Args:
            tasks: 任务列表
            skip_existing: 是否跳过已存在的任务
            
        Returns:
            成功创建的任务列表
        """
        if not tasks:
            return []
        
        async with self.pool.acquire() as conn:
            # 1. 批量查询已存在的scheduler_id
            scheduler_ids = [t.scheduler_id for t in tasks if t.scheduler_id]
            existing_ids = set()
            
            if scheduler_ids and skip_existing:
                rows = await conn.fetch(
                    "SELECT scheduler_id FROM scheduled_tasks WHERE scheduler_id = ANY($1)",
                    scheduler_ids
                )
                existing_ids = {row['scheduler_id'] for row in rows}
                
            # 2. 过滤出需要创建的任务
            tasks_to_create = []
            for task in tasks:
                if task.scheduler_id in existing_ids:
                    continue  # 跳过已存在的
                tasks_to_create.append(task)
            
            if not tasks_to_create:
                return []
            
            # 3. 准备批量插入的数据
            values = []
            for task in tasks_to_create:
                values.append((
                    task.scheduler_id,
                    task.task_name,
                    task.task_type.value,
                    task.queue_name,
                    json.dumps(task.task_args),
                    json.dumps(task.task_kwargs),
                    task.cron_expression,
                    task.interval_seconds,
                    task.next_run_time,
                    task.enabled,
                    task.max_retries,
                    task.retry_delay,
                    task.timeout,
                    task.priority,
                    task.description,
                    json.dumps(task.tags),
                    json.dumps(task.metadata)
                ))
            
            # 4. 批量插入（使用UNNEST进行批量插入）
            created_rows = await conn.fetch(
                """
                INSERT INTO scheduled_tasks (
                    scheduler_id, task_name, task_type, queue_name,
                    task_args, task_kwargs, cron_expression, interval_seconds,
                    next_run_time, enabled, max_retries, retry_delay, timeout,
                    priority, description, tags, metadata
                )
                SELECT * FROM UNNEST(
                    $1::text[], $2::text[], $3::text[], $4::text[],
                    $5::jsonb[], $6::jsonb[], $7::text[], $8::numeric[],
                    $9::timestamptz[], $10::boolean[], $11::int[], $12::int[], $13::int[],
                    $14::int[], $15::text[], $16::jsonb[], $17::jsonb[]
                ) AS t(
                    scheduler_id, task_name, task_type, queue_name,
                    task_args, task_kwargs, cron_expression, interval_seconds,
                    next_run_time, enabled, max_retries, retry_delay, timeout,
                    priority, description, tags, metadata
                )
                ON CONFLICT (scheduler_id) DO NOTHING
                RETURNING *
                """,
                # 解包values为列数组
                [v[0] for v in values],  # scheduler_id
                [v[1] for v in values],  # task_name
                [v[2] for v in values],  # task_type
                [v[3] for v in values],  # queue_name
                [v[4] for v in values],  # task_args
                [v[5] for v in values],  # task_kwargs
                [v[6] for v in values],  # cron_expression
                [v[7] for v in values],  # interval_seconds
                [v[8] for v in values],  # next_run_time
                [v[9] for v in values],  # enabled
                [v[10] for v in values],  # max_retries
                [v[11] for v in values],  # retry_delay
                [v[12] for v in values],  # timeout
                [v[13] for v in values],  # priority
                [v[14] for v in values],  # description
                [v[15] for v in values],  # tags
                [v[16] for v in values],  # metadata
            )
            
            # 5. 转换结果为任务对象
            created_tasks = [self._row_to_task(row) for row in created_rows]
            
            return created_tasks