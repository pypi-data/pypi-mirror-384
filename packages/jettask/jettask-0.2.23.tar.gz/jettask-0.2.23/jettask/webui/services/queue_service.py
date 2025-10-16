"""
队列服务层
处理队列相关的业务逻辑
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta, timezone
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
import logging
import traceback

logger = logging.getLogger(__name__)


class QueueService:
    """队列服务类"""
    
    @staticmethod
    def get_base_queue_name(queue_name: str) -> str:
        """
        提取基础队列名（去除优先级后缀）
        
        Args:
            queue_name: 完整队列名
            
        Returns:
            基础队列名
        """
        if ':' in queue_name:
            parts = queue_name.rsplit(':', 1)
            if parts[-1].isdigit():
                return parts[0]
        return queue_name
    
    @staticmethod
    async def get_queues_by_namespace(namespace_data_access, namespace: str) -> Dict[str, Any]:
        """
        获取指定命名空间的队列列表
        
        Args:
            namespace_data_access: 命名空间数据访问实例
            namespace: 命名空间
            
        Returns:
            队列列表
        """
        queues_data = await namespace_data_access.get_queue_stats(namespace)
        return {
            "success": True,
            "data": list(set([QueueService.get_base_queue_name(q['queue_name']) for q in queues_data]))
        }
    
    @staticmethod
    async def get_queue_flow_rates(data_access, query) -> Dict[str, Any]:
        """
        获取单个队列的流量速率（入队、开始执行、完成）
        
        Args:
            data_access: 数据访问层实例
            query: 时间范围查询对象
            
        Returns:
            队列流量速率数据
        """
        # 处理时间范围
        now = datetime.now(timezone.utc)
        
        if query.start_time and query.end_time:
            # 使用提供的时间范围
            start_time = query.start_time
            end_time = query.end_time
            logger.info(f"使用自定义时间范围: {start_time} 到 {end_time}")
        else:
            # 根据time_range参数计算时间范围
            time_range_map = {
                "15m": timedelta(minutes=15),
                "30m": timedelta(minutes=30),
                "1h": timedelta(hours=1),
                "3h": timedelta(hours=3),
                "6h": timedelta(hours=6),
                "12h": timedelta(hours=12),
                "24h": timedelta(hours=24),
                "7d": timedelta(days=7),
                "30d": timedelta(days=30),
            }
            
            # 优先使用 time_range，如果没有则使用 interval
            time_range_value = query.time_range if query.time_range else query.interval
            delta = time_range_map.get(time_range_value, timedelta(minutes=15))
            
            # 获取队列的最新任务时间，确保图表包含最新数据
            queue_name = query.queues[0] if query.queues else None
            if queue_name:
                latest_time = await data_access.get_latest_task_time(queue_name)
                if latest_time:
                    # 使用最新任务时间作为结束时间
                    end_time = latest_time.replace(second=59, microsecond=999999)  # 包含整分钟
                    logger.info(f"使用最新任务时间: {latest_time}")
                else:
                    # 如果没有任务，使用当前时间
                    end_time = now.replace(second=0, microsecond=0)
            else:
                end_time = now.replace(second=0, microsecond=0)
            
            start_time = end_time - delta
            logger.info(f"使用预设时间范围 {time_range_value}: {start_time} 到 {end_time}, delta: {delta}")
        
        # 确保有队列名称
        if not query.queues or len(query.queues) == 0:
            return {"data": [], "granularity": "minute"}
        
        # 获取第一个队列的流量速率
        queue_name = query.queues[0]
        # TimeRangeQuery 没有 filters 属性，传递 None 或空字典
        filters = getattr(query, 'filters', None)
        data, granularity = await data_access.fetch_queue_flow_rates(
            queue_name, start_time, end_time, filters
        )
        
        return {"data": data, "granularity": granularity}
    
    @staticmethod
    async def get_global_stats(data_access) -> Dict[str, Any]:
        """
        获取全局统计信息
        
        Args:
            data_access: 数据访问层实例
            
        Returns:
            全局统计数据
        """
        stats_data = await data_access.fetch_global_stats()
        return {
            "success": True,
            "data": stats_data
        }
    
    @staticmethod
    async def get_queues_detail(data_access) -> Dict[str, Any]:
        """
        获取队列详细信息
        
        Args:
            data_access: 数据访问层实例
            
        Returns:
            队列详细数据
        """
        queues_data = await data_access.fetch_queues_data()
        return {
            "success": True,
            "data": queues_data
        }
    
    @staticmethod
    async def delete_queue(queue_name: str) -> Dict[str, Any]:
        """
        删除队列
        
        Args:
            queue_name: 队列名称
            
        Returns:
            操作结果
        """
        # TODO: 实现删除队列的逻辑
        logger.info(f"删除队列请求: {queue_name}")
        return {
            "success": True,
            "message": f"队列 {queue_name} 已删除"
        }
    
    @staticmethod
    async def trim_queue(queue_name: str, max_length: int) -> Dict[str, Any]:
        """
        裁剪队列到指定长度
        
        Args:
            queue_name: 队列名称
            max_length: 最大长度
            
        Returns:
            操作结果
        """
        # TODO: 实现裁剪队列的逻辑
        logger.info(f"裁剪队列请求: {queue_name}, 保留 {max_length} 条消息")
        return {
            "success": True,
            "message": f"队列 {queue_name} 已裁剪至 {max_length} 条消息"
        }
    
    @staticmethod
    async def get_queue_stats_v2(
        namespace_data_access,
        namespace: str,
        queue: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        time_range: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取队列统计信息v2 - 支持消费者组详情和优先级队列
        
        Args:
            namespace_data_access: 命名空间数据访问实例
            namespace: 命名空间
            queue: 可选，筛选特定队列
            start_time: 开始时间
            end_time: 结束时间
            time_range: 时间范围
            
        Returns:
            队列统计数据
        """
        # 获取命名空间连接
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        # 获取Redis客户端
        redis_client = await conn.get_redis_client(decode=False)
        
        # 获取PostgreSQL会话（可选）
        pg_session = None
        if conn.AsyncSessionLocal:
            pg_session = conn.AsyncSessionLocal()
        
        try:
            # 导入 QueueStatsV2
            from jettask.webui.services.queue_stats_v2 import QueueStatsV2
            
            # 创建统计服务实例
            stats_service = QueueStatsV2(
                redis_client=redis_client,
                pg_session=pg_session,
                redis_prefix=conn.redis_prefix
            )
            
            # 处理时间筛选参数
            time_filter = None
            if time_range or start_time or end_time:
                time_filter = {}
                
                # 如果提供了time_range，计算开始和结束时间
                if time_range and time_range != 'custom':
                    now = datetime.now(timezone.utc)
                    if time_range.endswith('m'):
                        minutes = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(minutes=minutes)
                        time_filter['end_time'] = now
                    elif time_range.endswith('h'):
                        hours = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(hours=hours)
                        time_filter['end_time'] = now
                    elif time_range.endswith('d'):
                        days = int(time_range[:-1])
                        time_filter['start_time'] = now - timedelta(days=days)
                        time_filter['end_time'] = now
                else:
                    # 使用提供的start_time和end_time
                    if start_time:
                        time_filter['start_time'] = start_time
                    if end_time:
                        time_filter['end_time'] = end_time
            
            # 获取队列统计（使用分组格式）
            stats = await stats_service.get_queue_stats_grouped(time_filter)
            
            # 如果指定了队列筛选，则过滤结果
            if queue:
                stats = [s for s in stats if s['queue_name'] == queue]
            
            return {
                "success": True,
                "data": stats
            }
            
        finally:
            if pg_session:
                await pg_session.close()
            await redis_client.aclose()
    
    @staticmethod
    async def get_tasks_v2(namespace_data_access, namespace: str, body: Dict[str, Any]) -> Dict[str, Any]:
        """
        获取任务列表v2 - 支持tasks和task_runs表连表查询
        
        Args:
            namespace_data_access: 命名空间数据访问实例
            namespace: 命名空间
            body: 请求体参数
            
        Returns:
            任务列表数据
        """
        from sqlalchemy import text
        from datetime import datetime, timezone, timedelta
        
        queue_name = body.get('queue_name')
        page = body.get('page', 1)
        page_size = body.get('page_size', 20)
        filters = body.get('filters', [])
        time_range = body.get('time_range', '1h')
        start_time = body.get('start_time')
        end_time = body.get('end_time')
        sort_field = body.get('sort_field', 'created_at')
        sort_order = body.get('sort_order', 'desc')
        
        if not queue_name:
            raise ValueError("queue_name is required")
        
        # 获取命名空间连接
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        if not conn.pg_config or not conn.async_engine:
            return {
                "success": True,
                "data": [],
                "total": 0
            }
        
        # 解析时间范围
        if start_time and end_time:
            # 使用自定义时间范围
            start_dt = datetime.fromisoformat(start_time.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end_time.replace('Z', '+00:00'))
        else:
            # 使用预定义时间范围
            end_dt = datetime.now(timezone.utc)
            time_deltas = {
                '15m': timedelta(minutes=15),
                '30m': timedelta(minutes=30),
                '1h': timedelta(hours=1),
                '3h': timedelta(hours=3),
                '6h': timedelta(hours=6),
                '12h': timedelta(hours=12),
                '1d': timedelta(days=1),
                '3d': timedelta(days=3),
                '7d': timedelta(days=7),
                '30d': timedelta(days=30)
            }
            delta = time_deltas.get(time_range, timedelta(hours=1))
            start_dt = end_dt - delta
        
        offset = (page - 1) * page_size
        
        async with conn.async_engine.begin() as pg_conn:
            # 构建查询条件
            conditions = [
                "t.namespace = :namespace",
                "t.queue = :queue",
                "t.created_at >= :start_time",
                "t.created_at <= :end_time"
            ]
            query_params = {
                "namespace": namespace,
                "queue": queue_name,
                "start_time": start_dt,
                "end_time": end_dt,
                "limit": page_size,
                "offset": offset
            }
            
            # 处理筛选条件
            for i, filter_item in enumerate(filters):
                field = filter_item.get('field')
                operator = filter_item.get('operator')
                value = filter_item.get('value')
                
                if field and operator and value is not None:
                    param_key = f"filter_{i}"
                    
                    # 映射前端字段到数据库字段（使用payload JSONB列）
                    db_field_map = {
                        'id': 't.stream_id',
                        'task_name': "t.payload::jsonb->'event_data'->>'__task_name'",
                        'status': "t.payload::jsonb->>'status'",
                        'worker_id': "t.payload::jsonb->>'worker_id'",
                        'scheduled_task_id': 't.scheduled_task_id'
                    }
                    
                    db_field = db_field_map.get(field, f't.{field}')
                    
                    if operator == 'eq':
                        conditions.append(f"{db_field} = :{param_key}")
                        query_params[param_key] = value
                    elif operator == 'contains':
                        conditions.append(f"{db_field} LIKE :{param_key}")
                        query_params[param_key] = f"%{value}%"
                    elif operator == 'gt':
                        conditions.append(f"{db_field} > :{param_key}")
                        query_params[param_key] = value
                    elif operator == 'lt':
                        conditions.append(f"{db_field} < :{param_key}")
                        query_params[param_key] = value
            
            where_clause = " AND ".join(conditions)
            
            # 获取总数
            count_query = f"""
                SELECT COUNT(*) as total 
                FROM tasks t
                WHERE {where_clause}
            """
            count_result = await pg_conn.execute(text(count_query), query_params)
            total = count_result.fetchone().total
            
            # 构建排序
            sort_map = {
                'created_at': 't.created_at',
                'started_at': 't.started_at',
                'completed_at': 't.completed_at'
            }
            order_by = sort_map.get(sort_field, 't.created_at')
            order_direction = 'DESC' if sort_order == 'desc' else 'ASC'
            
            # 获取任务列表（从payload JSONB中提取数据）
            query = f"""
                SELECT 
                    t.stream_id as id,
                    t.payload::jsonb->'event_data'->>'__task_name' as task_name,
                    t.queue,
                    t.payload::jsonb->>'status' as status,
                    t.priority,
                    COALESCE((t.payload::jsonb->>'retry_count')::int, 0) as retry_count,
                    COALESCE((t.payload::jsonb->>'max_retry')::int, 3) as max_retry,
                    t.created_at,
                    (t.payload::jsonb->>'started_at')::timestamptz as started_at,
                    (t.payload::jsonb->>'completed_at')::timestamptz as completed_at,
                    t.payload::jsonb->>'worker_id' as worker_id,
                    t.payload::jsonb->>'error_message' as error_message,
                    (t.payload::jsonb->>'execution_time')::float as execution_time,
                    CASE 
                        WHEN t.payload::jsonb->>'completed_at' IS NOT NULL AND t.created_at IS NOT NULL 
                        THEN EXTRACT(EPOCH FROM ((t.payload::jsonb->>'completed_at')::timestamptz - t.created_at))
                        ELSE NULL 
                    END as duration,
                    t.scheduled_task_id,
                    t.source,
                    t.metadata
                FROM tasks t
                WHERE {where_clause}
                ORDER BY {order_by} {order_direction}
                LIMIT :limit OFFSET :offset
            """
            
            result = await pg_conn.execute(text(query), query_params)
            
            tasks = []
            for row in result:
                tasks.append({
                    "id": row.id,
                    "task_name": row.task_name or "unknown",
                    "queue": row.queue,
                    "status": row.status,
                    "priority": row.priority,
                    "retry_count": row.retry_count,
                    "max_retry": row.max_retry,
                    "created_at": row.created_at.isoformat() if row.created_at else None,
                    "started_at": row.started_at.isoformat() if row.started_at else None,
                    "completed_at": row.completed_at.isoformat() if row.completed_at else None,
                    "duration": round(row.duration, 2) if row.duration else None,
                    "execution_time": float(row.execution_time) if row.execution_time else None,
                    "worker_id": row.worker_id,
                    "error_message": row.error_message
                })
            
            return {
                "success": True,
                "data": tasks,
                "total": total
            }
    
    @staticmethod
    async def get_consumer_group_stats(namespace_data_access, namespace: str, group_name: str) -> Dict[str, Any]:
        """
        获取特定消费者组的详细统计
        
        Args:
            namespace_data_access: 命名空间数据访问实例
            namespace: 命名空间
            group_name: 消费者组名称
            
        Returns:
            消费者组统计数据
        """
        # 获取命名空间连接
        conn = await namespace_data_access.manager.get_connection(namespace)
        
        # 获取PostgreSQL会话
        if not conn.AsyncSessionLocal:
            raise ValueError("PostgreSQL not configured for this namespace")
        
        async with conn.AsyncSessionLocal() as session:
            # 查询消费者组的执行统计
            query = text("""
                WITH group_stats AS (
                    SELECT 
                        tr.consumer_group,
                        tr.task_name,
                        COUNT(*) as total_tasks,
                        COUNT(CASE WHEN tr.status = 'success' THEN 1 END) as success_count,
                        COUNT(CASE WHEN tr.status = 'failed' THEN 1 END) as failed_count,
                        COUNT(CASE WHEN tr.status = 'running' THEN 1 END) as running_count,
                        AVG(tr.execution_time) as avg_execution_time,
                        MIN(tr.execution_time) as min_execution_time,
                        MAX(tr.execution_time) as max_execution_time,
                        AVG(tr.duration) as avg_duration,
                        MIN(tr.started_at) as first_task_time,
                        MAX(tr.completed_at) as last_task_time
                    FROM task_runs tr
                    WHERE tr.consumer_group = :group_name
                        AND tr.started_at > NOW() - INTERVAL '24 hours'
                    GROUP BY tr.consumer_group, tr.task_name
                ),
                hourly_stats AS (
                    SELECT 
                        DATE_TRUNC('hour', tr.started_at) as hour,
                        COUNT(*) as task_count,
                        AVG(tr.execution_time) as avg_exec_time
                    FROM task_runs tr
                    WHERE tr.consumer_group = :group_name
                        AND tr.started_at > NOW() - INTERVAL '24 hours'
                    GROUP BY DATE_TRUNC('hour', tr.started_at)
                    ORDER BY hour
                )
                SELECT 
                    (SELECT row_to_json(gs) FROM group_stats gs) as summary,
                    (SELECT json_agg(hs) FROM hourly_stats hs) as hourly_trend
            """)
            
            result = await session.execute(query, {'group_name': group_name})
            row = result.fetchone()
            
            if not row or not row.summary:
                return {
                    "success": True,
                    "data": {
                        "group_name": group_name,
                        "summary": {},
                        "hourly_trend": []
                    }
                }
            
            return {
                "success": True,
                "data": {
                    "group_name": group_name,
                    "summary": row.summary,
                    "hourly_trend": row.hourly_trend or []
                }
            }
    
    @staticmethod
    async def get_stream_backlog(
        data_access,
        namespace: str,
        stream_name: Optional[str] = None,
        hours: int = 24
    ) -> Dict[str, Any]:
        """
        获取Stream积压监控数据
        
        Args:
            data_access: 数据访问层实例
            namespace: 命名空间
            stream_name: 可选，指定stream名称
            hours: 查询最近多少小时的数据
            
        Returns:
            Stream积压数据
        """
        # 计算时间范围
        end_time = datetime.now(timezone.utc)
        start_time = end_time - timedelta(hours=hours)
        
        async with data_access.AsyncSessionLocal() as session:
            # 构建查询
            if stream_name:
                query = text("""
                    SELECT 
                        stream_name,
                        consumer_group,
                        last_published_offset,
                        last_delivered_offset,
                        last_acked_offset,
                        pending_count,
                        backlog_undelivered,
                        backlog_unprocessed,
                        created_at
                    FROM stream_backlog_monitor
                    WHERE namespace = :namespace
                        AND stream_name = :stream_name
                        AND created_at >= :start_time
                        AND created_at <= :end_time
                    ORDER BY created_at DESC
                    LIMIT 1000
                """)
                params = {
                    'namespace': namespace,
                    'stream_name': stream_name,
                    'start_time': start_time,
                    'end_time': end_time
                }
            else:
                # 获取最新的所有stream数据
                query = text("""
                    SELECT DISTINCT ON (stream_name, consumer_group)
                        stream_name,
                        consumer_group,
                        last_published_offset,
                        last_delivered_offset,
                        last_acked_offset,
                        pending_count,
                        backlog_undelivered,
                        backlog_unprocessed,
                        created_at
                    FROM stream_backlog_monitor
                    WHERE namespace = :namespace
                        AND created_at >= :start_time
                    ORDER BY stream_name, consumer_group, created_at DESC
                """)
                params = {
                    'namespace': namespace,
                    'start_time': start_time
                }
            
            result = await session.execute(query, params)
            rows = result.fetchall()
            
            # 格式化数据
            data = []
            for row in rows:
                data.append({
                    'stream_name': row.stream_name,
                    'consumer_group': row.consumer_group,
                    'last_published_offset': row.last_published_offset,
                    'last_delivered_offset': row.last_delivered_offset,
                    'last_acked_offset': row.last_acked_offset,
                    'pending_count': row.pending_count,
                    'backlog_undelivered': row.backlog_undelivered,
                    'backlog_unprocessed': row.backlog_unprocessed,
                    'created_at': row.created_at.isoformat() if row.created_at else None
                })
            
            return {
                'success': True,
                'data': data,
                'total': len(data)
            }
    
    @staticmethod
    async def get_stream_backlog_summary(data_access, namespace: str) -> Dict[str, Any]:
        """
        获取Stream积压监控汇总数据
        
        Args:
            data_access: 数据访问层实例
            namespace: 命名空间
            
        Returns:
            汇总数据
        """
        async with data_access.AsyncSessionLocal() as session:
            # 获取最新的汇总数据
            query = text("""
                WITH latest_data AS (
                    SELECT DISTINCT ON (stream_name, consumer_group)
                        stream_name,
                        consumer_group,
                        backlog_undelivered,
                        backlog_unprocessed,
                        pending_count
                    FROM stream_backlog_monitor
                    WHERE namespace = :namespace
                        AND created_at >= NOW() - INTERVAL '1 hour'
                    ORDER BY stream_name, consumer_group, created_at DESC
                )
                SELECT 
                    COUNT(DISTINCT stream_name) as total_streams,
                    COUNT(DISTINCT consumer_group) as total_groups,
                    SUM(backlog_unprocessed) as total_backlog,
                    SUM(pending_count) as total_pending,
                    MAX(backlog_unprocessed) as max_backlog
                FROM latest_data
            """)
            
            result = await session.execute(query, {'namespace': namespace})
            row = result.fetchone()
            
            if row:
                return {
                    'success': True,
                    'data': {
                        'total_streams': row.total_streams or 0,
                        'total_groups': row.total_groups or 0,
                        'total_backlog': row.total_backlog or 0,
                        'total_pending': row.total_pending or 0,
                        'max_backlog': row.max_backlog or 0
                    }
                }
            else:
                return {
                    'success': True,
                    'data': {
                        'total_streams': 0,
                        'total_groups': 0,
                        'total_backlog': 0,
                        'total_pending': 0,
                        'max_backlog': 0
                    }
                }