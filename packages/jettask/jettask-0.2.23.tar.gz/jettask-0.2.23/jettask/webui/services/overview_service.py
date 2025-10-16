"""
概览服务层
处理系统概览和健康检查相关的业务逻辑
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, List, Optional
import logging
import time
import traceback
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from jettask.schemas import TimeRangeQuery
from jettask.persistence.db_manager import get_db_manager

logger = logging.getLogger(__name__)

# 获取全局数据访问实例
# 使用新的统一数据库管理器


class TimeRangeResult:
    """时间范围处理结果"""
    def __init__(self, start_time: datetime, end_time: datetime, interval: str, interval_seconds: int, granularity: str):
        self.start_time = start_time
        self.end_time = end_time
        self.interval = interval
        self.interval_seconds = interval_seconds
        self.granularity = granularity


class OverviewService:
    """概览服务类"""
    
    @staticmethod
    def get_root_info() -> Dict[str, Any]:
        """
        获取根路径信息
        
        Returns:
            API基本信息
        """
        return {
            "message": "JetTask Monitor API",
            "version": "1.0.0",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    def get_health_status() -> Dict[str, Any]:
        """
        获取健康状态
        
        Returns:
            健康状态信息
        """
        return {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    @staticmethod
    async def get_system_stats(namespace: str) -> Dict[str, Any]:
        """
        获取指定命名空间的系统统计信息
        
        Args:
            namespace: 命名空间名称
            
        Returns:
            系统统计信息
        """
        db_manager = get_db_manager()
        pool = await db_manager.get_pool(namespace)
        redis_client = await pool.get_redis_client()
        
        try:
            # 统计各种类型的键
            stats = {
                'namespace': namespace,
                'queues': 0,
                'tasks': 0,
                'delayed_tasks': 0,
                'workers': 0
            }
            
            # 使用注册管理器进行统计，避免 scan
            from jettask.messaging.registry import QueueRegistry
            from jettask.task.task_registry import TaskRegistry
            from jettask.worker.manager import WorkerState as WorkerRegistry

            queue_registry = QueueRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            task_registry = TaskRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            worker_registry = WorkerRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=namespace
            )

            # 统计队列数量
            stats['queues'] = await queue_registry.get_queue_count()

            # 统计任务数量
            stats['tasks'] = await task_registry.get_task_count_from_redis()

            # 统计延迟任务数量
            delayed_queues = await queue_registry.get_all_delayed_queues()
            for queue in delayed_queues:
                delayed_key = f"{namespace}:DELAYED_QUEUE:{queue}"
                count = await redis_client.zcard(delayed_key)
                stats['delayed_tasks'] += count

            # 统计工作进程数量
            stats['workers'] = await worker_registry.get_worker_count()
            
            return stats
            
        finally:
            await redis_client.aclose()
    
    @staticmethod
    async def get_dashboard_stats(
        namespace: str,
        time_range: str = "24h",
        queues: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取仪表板统计数据
        
        Args:
            namespace: 命名空间名称
            time_range: 时间范围
            queues: 逗号分隔的队列名称列表
            
        Returns:
            仪表板统计数据
        """
        db_manager = get_db_manager()
        pool = await db_manager.get_pool(namespace)
        
        # 如果没有PostgreSQL配置，返回空数据
        # 检查是否配置了PostgreSQL
        if not pool.config.has_postgres():
            return {
                "success": True,
                "data": _get_empty_dashboard_stats()
            }
        
        # 计算时间范围
        end_time = datetime.now(timezone.utc)
        start_time = _parse_time_range(time_range, end_time)
        
        # 构建队列筛选条件
        queue_filter, queue_list, queue_params = _build_queue_filter_and_params(queues)
        
        async with pool.get_sa_session() as session:
            # 获取统计数据
            stats_data = await _get_task_statistics(
                session, namespace, start_time, end_time,
                queue_filter, queue_params
            )
            
            # 计算吞吐量
            throughput = await _calculate_throughput(
                session, namespace, queue_filter, queue_params
            )
            
            # 获取任务分布数据
            # 合并所有查询参数
            distribution_params = {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                **queue_params
            }
            distribution_data = await _get_task_distribution(
                session, namespace, start_time, end_time,
                queue_filter, distribution_params
            )
            
            return {
                "success": True,
                "data": {
                    **stats_data,
                    "throughput": throughput,
                    "distribution": distribution_data
                }
            }
    
    @staticmethod
    async def get_top_queues(
        namespace: str,
        metric: str = "backlog",
        limit: int = 10,
        time_range: str = "24h",
        queues: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        获取队列排行榜
        
        Args:
            namespace: 命名空间名称
            metric: 指标类型 (backlog/error)
            limit: 返回的队列数量限制
            time_range: 时间范围
            queues: 逗号分隔的队列名称列表
            
        Returns:
            队列排行榜数据
        """
        if metric == "backlog":
            return await _get_top_backlog_queues(namespace, limit, time_range, queues)
        elif metric == "error":
            return await _get_top_error_queues(namespace, limit, time_range, queues)
        else:
            raise ValueError(f"不支持的指标类型: {metric}")
    
    @staticmethod
    async def get_dashboard_overview_stats(
        namespace: str,
        query: TimeRangeQuery
    ) -> Dict[str, Any]:
        """
        获取概览页面的统一统计数据
        
        Args:
            namespace: 命名空间名称
            query: 时间范围查询参数
            
        Returns:
            统一的时间序列数据
        """
        db_manager = get_db_manager()
        pool = await db_manager.get_pool(namespace)
        
        # 如果没有PostgreSQL配置，返回空数据
        # 检查是否配置了PostgreSQL
        if not pool.config.has_postgres():
            return _get_empty_overview_stats()
        
        # 解析时间范围
        time_range_result = _parse_time_range_query(query)
        
        # 构建队列筛选条件
        # 使用 TimeRangeQuery 的 queues 字段（支持多队列列表）
        queue_list = query.queues if hasattr(query, 'queues') and query.queues else None
        queue_filter, _, queue_params = _build_queue_filter_and_params(queue_list)
        
        async with pool.get_sa_session() as session:
            # 执行统一查询
            result = await _execute_overview_query(
                session, namespace, time_range_result,
                queue_filter, queue_params
            )
            
            # 格式化数据
            return _format_overview_data(result, time_range_result.granularity)


# ============ 辅助函数 ============

def _parse_time_range(time_range: str, end_time: datetime) -> datetime:
    """解析时间范围字符串"""
    if time_range.endswith('m'):
        minutes = int(time_range[:-1])
        return end_time - timedelta(minutes=minutes)
    elif time_range.endswith('h'):
        hours = int(time_range[:-1])
        return end_time - timedelta(hours=hours)
    elif time_range.endswith('d'):
        days = int(time_range[:-1])
        return end_time - timedelta(days=days)
    else:
        return end_time - timedelta(hours=24)  # 默认24小时


def _parse_time_range_query(query: TimeRangeQuery) -> TimeRangeResult:
    """解析TimeRangeQuery对象"""
    # TimeRangeQuery 有 start_time, end_time 和 interval 字段
    # 但没有 time_range 字段
    
    # 如果有结束时间，使用它；否则使用当前时间
    if query.end_time:
        end_time = datetime.fromisoformat(query.end_time.replace('Z', '+00:00')) if isinstance(query.end_time, str) else query.end_time
    else:
        end_time = datetime.now(timezone.utc)
    
    # 如果有开始时间，使用它；否则基于interval或默认24小时
    if query.start_time:
        start_time = datetime.fromisoformat(query.start_time.replace('Z', '+00:00')) if isinstance(query.start_time, str) else query.start_time
    else:
        # 使用interval字段来计算开始时间，默认为24小时
        interval = query.interval or "24h"
        start_time = _parse_time_range(interval, end_time)
    
    return _calculate_dynamic_interval(start_time, end_time)


def _calculate_dynamic_interval(start_time: datetime, end_time: datetime, target_points: int = 200) -> TimeRangeResult:
    """根据时间范围动态计算合适的时间间隔"""
    duration = (end_time - start_time).total_seconds()
    ideal_interval_seconds = duration / target_points
    
    # 选择合适的间隔
    intervals = [
        (1, '1 seconds', 'second'),
        (5, '5 seconds', 'second'),
        (10, '10 seconds', 'second'),
        (30, '30 seconds', 'second'),
        (60, '1 minute', 'minute'),
        (300, '5 minutes', 'minute'),
        (600, '10 minutes', 'minute'),
        (1800, '30 minutes', 'minute'),
        (3600, '1 hour', 'hour'),
        (21600, '6 hours', 'hour'),
        (43200, '12 hours', 'hour'),
        (86400, '1 day', 'day')
    ]
    
    for seconds, interval_str, granularity in intervals:
        if ideal_interval_seconds <= seconds:
            return TimeRangeResult(start_time, end_time, interval_str, seconds, granularity)
    
    # 默认返回1天间隔
    return TimeRangeResult(start_time, end_time, '1 day', 86400, 'day')


def _build_queue_filter_and_params(queues: Optional[List[str]] = None):
    """构建队列筛选条件和参数"""
    queue_list = []
    if queues:
        # 如果是字符串，按逗号分割（向后兼容）
        if isinstance(queues, str):
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]
        # 如果是列表，直接使用
        elif isinstance(queues, list):
            queue_list = [q.strip() for q in queues if q and q.strip()]
        else:
            queue_list = []
    
    queue_filter = ""
    queue_params = {}
    
    if queue_list:
        queue_placeholders = ','.join([f':queue_{i}' for i in range(len(queue_list))])
        queue_filter = f"AND t.queue IN ({queue_placeholders})"
        
        for i, queue in enumerate(queue_list):
            queue_params[f'queue_{i}'] = queue
    
    return queue_filter, queue_list, queue_params


def _get_empty_dashboard_stats():
    """返回空的仪表板统计数据"""
    return {
        "total_tasks": 0,
        "completed_tasks": 0,
        "failed_tasks": 0,
        "running_tasks": 0,
        "pending_tasks": 0,
        "success_rate": 0,
        "throughput": 0,
        "avg_processing_time": 0,
        "total_queues": 0,
        "distribution": [{'type': '暂无数据', 'value': 1, 'queue': '', 'status': 'empty'}]
    }


def _get_empty_overview_stats():
    """返回空的概览统计数据"""
    return {
        "task_trend": [],
        "concurrency": [],
        "processing_time": [],
        "creation_latency": [],
        "granularity": "minute"
    }


async def _get_task_statistics(session, namespace, start_time, end_time, queue_filter, queue_params):
    """获取任务统计数据"""
    stats_sql = text(f"""
        WITH task_stats AS (
            SELECT 
                t.stream_id,
                t.created_at,
                t.queue,
                tr.status,
                tr.execution_time,
                tr.end_time
            FROM tasks t
            LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
            WHERE t.namespace = :namespace
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
        )
        SELECT 
            COUNT(DISTINCT stream_id) as total_tasks,
            COUNT(DISTINCT CASE WHEN status = 'success' THEN stream_id END) as completed_tasks,
            COUNT(DISTINCT CASE WHEN status = 'error' THEN stream_id END) as failed_tasks,
            COUNT(DISTINCT CASE WHEN status = 'running' THEN stream_id END) as running_tasks,
            COUNT(DISTINCT CASE WHEN status IS NULL OR status = 'pending' THEN stream_id END) as pending_tasks,
            COUNT(DISTINCT queue) as total_queues,
            AVG(CASE WHEN status = 'success' AND execution_time IS NOT NULL 
                THEN execution_time END) as avg_execution_time
        FROM task_stats
    """)
    
    # 合并所有查询参数
    all_params = {
        'namespace': namespace,
        'start_time': start_time,
        'end_time': end_time,
        **queue_params
    }
    
    result = await session.execute(stats_sql, all_params)
    row = result.first()
    
    if row:
        avg_execution_time = row.avg_execution_time or 0
        success_rate = round((row.completed_tasks / row.total_tasks * 100) if row.total_tasks > 0 else 0, 1)
        
        return {
            "total_tasks": row.total_tasks or 0,
            "completed_tasks": row.completed_tasks or 0,
            "failed_tasks": row.failed_tasks or 0,
            "running_tasks": row.running_tasks or 0,
            "pending_tasks": row.pending_tasks or 0,
            "success_rate": success_rate,
            "avg_processing_time": round(avg_execution_time * 1000 if avg_execution_time else 0, 1),
            "total_queues": row.total_queues or 0
        }
    
    return _get_empty_dashboard_stats()


async def _calculate_throughput(session, namespace, queue_filter, queue_params):
    """计算吞吐量（每分钟完成的任务数）"""
    recent_end_time = datetime.now(timezone.utc)
    throughput = 0
    
    time_windows = [
        (5, "最近5分钟"),
        (10, "最近10分钟"), 
        (30, "最近30分钟"),
        (60, "最近1小时")
    ]
    
    for window_minutes, window_desc in time_windows:
        recent_start_time = recent_end_time - timedelta(minutes=window_minutes)
        
        recent_query = text(f"""
            SELECT COUNT(DISTINCT t.stream_id) as recent_completed
            FROM tasks t
            LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
            WHERE t.namespace = :namespace
                AND tr.status = 'success'
                AND tr.end_time >= :recent_start_time
                AND tr.end_time <= :recent_end_time
                {queue_filter}
        """)
        
        throughput_params = {
            'namespace': namespace,
            'recent_start_time': recent_start_time,
            'recent_end_time': recent_end_time,
            **queue_params
        }
        
        recent_result = await session.execute(recent_query, throughput_params)
        recent_row = recent_result.first()
        recent_completed = recent_row.recent_completed if recent_row else 0
        
        if recent_completed >= 5:
            throughput = round(recent_completed / window_minutes, 1)
            logger.info(f"使用{window_desc}计算吞吐量: {recent_completed}个任务/{window_minutes}分钟 = {throughput}任务/分钟")
            break
        elif recent_completed > 0:
            throughput = round(recent_completed / window_minutes, 1)
    
    return throughput


async def _get_task_distribution(session, namespace, start_time, end_time, queue_filter, query_params):
    """获取任务分布数据"""
    distribution_sql = text(f"""
        SELECT 
            t.queue,
            COUNT(DISTINCT t.stream_id) as count
        FROM tasks t
        WHERE t.namespace = :namespace
            AND t.created_at >= :start_time
            AND t.created_at <= :end_time
            {queue_filter}
        GROUP BY t.queue
        ORDER BY count DESC, t.queue
    """)
    
    distribution_result = await session.execute(distribution_sql, query_params)
    
    distribution_data = []
    for row in distribution_result.fetchall():
        if row.count > 0:
            distribution_data.append({
                'type': row.queue,
                'value': row.count,
                'queue': row.queue,
                'status': 'all'
            })
    
    if not distribution_data:
        distribution_data = [
            {'type': '暂无数据', 'value': 1, 'queue': '', 'status': 'empty'}
        ]
    
    return distribution_data


async def _get_top_backlog_queues(namespace, limit, time_range, queues):
    """获取积压最多的队列Top N"""
    db_manager = get_db_manager()
    pool = await db_manager.get_pool(namespace)
    
    # 检查是否配置了PostgreSQL
    if not pool.config.has_postgres():
        return {"success": True, "data": []}
    
    end_time = datetime.now(timezone.utc)
    start_time = _parse_time_range(time_range, end_time)
    
    async with pool.get_sa_session() as session:
        queue_list = []
        if queues:
            # 如果是字符串，按逗号分割（向后兼容）
            if isinstance(queues, str):
                queue_list = [q.strip() for q in queues.split(',') if q.strip()]
            # 如果是列表，直接使用
            elif isinstance(queues, list):
                queue_list = [q.strip() for q in queues if q and q.strip()]
        
        try:
            # 优先从stream_backlog_monitor获取最新的积压数据
            if queue_list:
                backlog_sql = text("""
                    SELECT 
                        stream_name as queue,
                        MAX(backlog_unprocessed) as backlog,
                        CASE 
                            WHEN MAX(backlog_unprocessed) > 100 THEN 'critical'
                            WHEN MAX(backlog_unprocessed) > 50 THEN 'warning'
                            ELSE 'normal'
                        END as status
                    FROM stream_backlog_monitor
                    WHERE namespace = :namespace
                        AND created_at >= :start_time
                        AND created_at <= :end_time
                        AND stream_name = ANY(:queues)
                    GROUP BY stream_name
                    HAVING MAX(backlog_unprocessed) > 0
                    ORDER BY backlog DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(backlog_sql, {
                    'namespace': namespace,
                    'start_time': start_time,
                    'end_time': end_time,
                    'queues': queue_list,
                    'limit': limit
                })
            else:
                backlog_sql = text("""
                    SELECT 
                        stream_name as queue,
                        MAX(backlog_unprocessed) as backlog,
                        CASE 
                            WHEN MAX(backlog_unprocessed) > 100 THEN 'critical'
                            WHEN MAX(backlog_unprocessed) > 50 THEN 'warning'
                            ELSE 'normal'
                        END as status
                    FROM stream_backlog_monitor
                    WHERE namespace = :namespace
                        AND created_at >= :start_time
                        AND created_at <= :end_time
                    GROUP BY stream_name
                    HAVING MAX(backlog_unprocessed) > 0
                    ORDER BY backlog DESC
                    LIMIT :limit
                """)
                
                result = await session.execute(backlog_sql, {
                    'namespace': namespace,
                    'start_time': start_time,
                    'end_time': end_time,
                    'limit': limit
                })
            
            backlog_queues = []
            for row in result.fetchall():
                backlog_queues.append({
                    "queue": row.queue,
                    "backlog": int(row.backlog),
                    "status": row.status
                })
            
            return {"success": True, "data": backlog_queues}
            
        except Exception as e:
            logger.warning(f"从stream_backlog_monitor获取积压数据失败: {e}")
            
        # 如果失败，从tasks表统计
        return await _get_top_backlog_from_tasks(session, namespace, limit)


async def _get_top_backlog_from_tasks(session, namespace, limit):
    """从tasks表获取积压数据"""
    task_sql = text("""
        SELECT 
            t.queue,
            COUNT(DISTINCT t.stream_id) as backlog,
            CASE 
                WHEN COUNT(DISTINCT t.stream_id) > 1000 THEN 'critical'
                WHEN COUNT(DISTINCT t.stream_id) > 500 THEN 'warning'
                ELSE 'normal'
            END as status
        FROM tasks t
        LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
        WHERE t.namespace = :namespace
            AND (tr.stream_id IS NULL OR tr.status = 'pending')
            AND t.created_at > NOW() - INTERVAL '24 hour'
        GROUP BY t.queue
        ORDER BY backlog DESC
        LIMIT :limit
    """)
    
    result = await session.execute(task_sql, {
        'namespace': namespace,
        'limit': limit
    })
    
    backlog_queues = []
    for row in result.fetchall():
        backlog_queues.append({
            "queue": row.queue,
            "backlog": int(row.backlog),
            "status": row.status
        })
    
    return {"success": True, "data": backlog_queues}


async def _get_top_error_queues(namespace, limit, time_range, queues):
    """获取错误率最高的队列Top N"""
    db_manager = get_db_manager()
    pool = await db_manager.get_pool(namespace)
    
    # 检查是否配置了PostgreSQL
    if not pool.config.has_postgres():
        return {"success": True, "data": []}
    
    end_time = datetime.now(timezone.utc)
    start_time = _parse_time_range(time_range, end_time)
    
    async with pool.get_sa_session() as session:
        queue_list = []
        if queues:
            queue_list = [q.strip() for q in queues.split(',') if q.strip()]
        
        if queue_list:
            error_sql = text("""
                WITH queue_stats AS (
                    SELECT 
                        t.queue,
                        COUNT(DISTINCT t.stream_id) as total,
                        COUNT(DISTINCT CASE WHEN tr.status = 'error' THEN t.stream_id END) as errors
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                    WHERE t.namespace = :namespace
                        AND t.created_at >= :start_time
                        AND t.created_at <= :end_time
                        AND t.queue = ANY(:queues)
                    GROUP BY t.queue
                )
                SELECT 
                    queue,
                    errors,
                    total,
                    CASE 
                        WHEN total > 0 THEN ROUND(errors::numeric / total * 100, 1)
                        ELSE 0 
                    END as error_rate
                FROM queue_stats
                WHERE errors > 0
                ORDER BY error_rate DESC, errors DESC
                LIMIT :limit
            """)
            
            result = await session.execute(error_sql, {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                'queues': queue_list,
                'limit': limit
            })
        else:
            error_sql = text("""
                WITH queue_stats AS (
                    SELECT 
                        t.queue,
                        COUNT(DISTINCT t.stream_id) as total,
                        COUNT(DISTINCT CASE WHEN tr.status = 'error' THEN t.stream_id END) as errors
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                    WHERE t.namespace = :namespace
                        AND t.created_at >= :start_time
                        AND t.created_at <= :end_time
                    GROUP BY t.queue
                )
                SELECT 
                    queue,
                    errors,
                    total,
                    CASE 
                        WHEN total > 0 THEN ROUND(errors::numeric / total * 100, 1)
                        ELSE 0 
                    END as error_rate
                FROM queue_stats
                WHERE errors > 0
                ORDER BY error_rate DESC, errors DESC
                LIMIT :limit
            """)
            
            result = await session.execute(error_sql, {
                'namespace': namespace,
                'start_time': start_time,
                'end_time': end_time,
                'limit': limit
            })
        
        error_queues = []
        for row in result.fetchall():
            error_queues.append({
                "queue": row.queue,
                "errors": int(row.errors),
                "total": int(row.total),
                "error_rate": float(row.error_rate)
            })
        
        return {"success": True, "data": error_queues}


async def _execute_overview_query(session, namespace, time_range_result, queue_filter, queue_params):
    """执行概览统计查询"""
    interval_seconds = time_range_result.interval_seconds
    
    # 直接在SQL中使用间隔秒数，避免参数类型问题
    sql = text(f"""
        WITH time_series AS (
            SELECT to_timestamp(FLOOR(EXTRACT(epoch FROM ts) / {interval_seconds}) * {interval_seconds}) AS time_bucket
            FROM generate_series(
                :start_time ::timestamptz,
                :end_time ::timestamptz + INTERVAL '{interval_seconds} seconds',
                INTERVAL '{interval_seconds} seconds'
            ) AS ts
        ),
        enqueue_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM t.created_at) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as enqueued
            FROM tasks t
            WHERE t.namespace = :namespace
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        complete_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as completed
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'success'
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        failed_counts AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as failed
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'error'
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        concurrency_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.start_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                COUNT(DISTINCT t.stream_id) as concurrent_tasks
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.start_time >= :start_time
                AND tr.start_time <= :end_time
                AND tr.start_time IS NOT NULL
                AND tr.end_time IS NOT NULL
                AND t.created_at >= :start_time
                AND t.created_at <= :end_time
                {queue_filter}
            GROUP BY time_bucket
        ),
        processing_time_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                AVG(CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as avg_processing_time,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as p50_processing_time,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY 
                    CASE WHEN tr.status = 'success' AND tr.execution_time > 0 
                    THEN tr.execution_time END) as p90_processing_time
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.end_time >= :start_time
                AND tr.end_time <= :end_time
                AND tr.status = 'success'
                {queue_filter}
            GROUP BY time_bucket
        ),
        creation_latency_data AS (
            SELECT 
                to_timestamp(FLOOR(EXTRACT(epoch FROM tr.start_time) / {interval_seconds}) * {interval_seconds}) AS time_bucket,
                AVG(EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as avg_creation_latency,
                PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY 
                    EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as p50_creation_latency,
                PERCENTILE_CONT(0.9) WITHIN GROUP (ORDER BY 
                    EXTRACT(EPOCH FROM (tr.start_time - t.created_at))) as p90_creation_latency
            FROM task_runs tr
            JOIN tasks t ON tr.stream_id = t.stream_id
            WHERE t.namespace = :namespace
                AND tr.start_time >= :start_time
                AND tr.start_time <= :end_time
                AND tr.start_time IS NOT NULL
                {queue_filter}
            GROUP BY time_bucket
        )
        SELECT 
            ts.time_bucket,
            COALESCE(eq.enqueued, 0) as enqueued,
            COALESCE(cc.completed, 0) as completed,
            COALESCE(fc.failed, 0) as failed,
            COALESCE(cd.concurrent_tasks, 0) as concurrent_tasks,
            ROUND(ptd.avg_processing_time::numeric, 6) as avg_processing_time,
            ROUND(ptd.p50_processing_time::numeric, 6) as p50_processing_time,
            ROUND(ptd.p90_processing_time::numeric, 6) as p90_processing_time,
            ROUND(cld.avg_creation_latency::numeric, 3) as avg_creation_latency,
            ROUND(cld.p50_creation_latency::numeric, 3) as p50_creation_latency,
            ROUND(cld.p90_creation_latency::numeric, 3) as p90_creation_latency
        FROM time_series ts
        LEFT JOIN enqueue_counts eq ON ts.time_bucket = eq.time_bucket
        LEFT JOIN complete_counts cc ON ts.time_bucket = cc.time_bucket
        LEFT JOIN failed_counts fc ON ts.time_bucket = fc.time_bucket
        LEFT JOIN concurrency_data cd ON ts.time_bucket = cd.time_bucket
        LEFT JOIN processing_time_data ptd ON ts.time_bucket = ptd.time_bucket
        LEFT JOIN creation_latency_data cld ON ts.time_bucket = cld.time_bucket
        ORDER BY ts.time_bucket
    """)
    
    query_params = {
        'namespace': namespace,
        'start_time': time_range_result.start_time,
        'end_time': time_range_result.end_time,
        **queue_params
    }
    
    result = await session.execute(sql, query_params)
    return result.fetchall()


def _format_overview_data(rows, granularity):
    """格式化概览数据"""
    task_trend = []
    concurrency = []
    processing_time = []
    creation_latency = []
    
    end_index = len(rows) - 1
    
    for idx, row in enumerate(rows):
        time_str = row.time_bucket.isoformat()
        
        # 任务处理趋势数据
        enqueued_val = row.enqueued if row.enqueued > 0 or idx == 0 or idx == end_index else None
        completed_val = row.completed if row.completed > 0 or idx == 0 or idx == end_index else None
        failed_val = row.failed if row.failed > 0 or idx == 0 or idx == end_index else None
        
        task_trend.extend([
            {'time': time_str, 'value': enqueued_val, 'metric': '入队速率'},
            {'time': time_str, 'value': completed_val, 'metric': '完成速率'},
            {'time': time_str, 'value': failed_val, 'metric': '失败数'}
        ])
        
        # 任务并发数量
        concurrency.append({
            'time': time_str,
            'value': row.concurrent_tasks or 0,
            'metric': '并发任务数'
        })
        
        # 任务处理时间（转换为毫秒）
        _add_processing_time_data(processing_time, time_str, row, idx, end_index)
        
        # 任务执行延时（秒）
        _add_creation_latency_data(creation_latency, time_str, row, idx, end_index)
    
    return {
        "task_trend": task_trend,
        "concurrency": concurrency,
        "processing_time": processing_time,
        "creation_latency": creation_latency,
        "granularity": granularity
    }


def _add_processing_time_data(processing_time, time_str, row, idx, end_index):
    """添加处理时间数据"""
    if row.avg_processing_time is not None:
        avg_time_val = round(float(row.avg_processing_time * 1000), 1)
    else:
        avg_time_val = None if idx != 0 and idx != end_index else 0
        
    if row.p50_processing_time is not None:
        p50_time_val = round(float(row.p50_processing_time * 1000), 1)
    else:
        p50_time_val = None if idx != 0 and idx != end_index else 0
        
    if row.p90_processing_time is not None:
        p90_time_val = round(float(row.p90_processing_time * 1000), 1)
    else:
        p90_time_val = None if idx != 0 and idx != end_index else 0
    
    processing_time.extend([
        {'time': time_str, 'value': avg_time_val, 'metric': '平均处理时间'},
        {'time': time_str, 'value': p50_time_val, 'metric': 'P50处理时间'},
        {'time': time_str, 'value': p90_time_val, 'metric': 'P90处理时间'}
    ])


def _add_creation_latency_data(creation_latency, time_str, row, idx, end_index):
    """添加创建延迟数据"""
    if row.avg_creation_latency is not None:
        avg_latency_val = round(float(row.avg_creation_latency), 3)
    else:
        avg_latency_val = None if idx != 0 and idx != end_index else 0
        
    if row.p50_creation_latency is not None:
        p50_latency_val = round(float(row.p50_creation_latency), 3)
    else:
        p50_latency_val = None if idx != 0 and idx != end_index else 0
        
    if row.p90_creation_latency is not None:
        p90_latency_val = round(float(row.p90_creation_latency), 3)
    else:
        p90_latency_val = None if idx != 0 and idx != end_index else 0
    
    creation_latency.extend([
        {'time': time_str, 'value': avg_latency_val, 'metric': '平均执行延时'},
        {'time': time_str, 'value': p50_latency_val, 'metric': 'P50执行延时'},
        {'time': time_str, 'value': p90_latency_val, 'metric': 'P90执行延时'}
    ])