"""
命名空间数据访问层 - 支持多租户的数据隔离访问
"""
import os
import asyncio
import json
import logging
import time
import traceback
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple, Any
import redis.asyncio as redis
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession
import aiohttp

# 导入统一的数据库连接工具
from ..utils.db_connector import (
    get_dual_mode_async_redis_client,
    get_pg_engine_and_factory
)

logger = logging.getLogger(__name__)


class NamespaceConnection:
    """单个命名空间的数据库连接"""

    def __init__(self, namespace_name: str, redis_config: dict, pg_config: dict):
        self.namespace_name = namespace_name
        self.redis_config = redis_config
        self.pg_config = pg_config
        self.redis_prefix = namespace_name  # 使用命名空间名作为Redis前缀

        # 使用全局单例连接池
        self._text_redis_client: Optional[redis.Redis] = None
        self._binary_redis_client: Optional[redis.Redis] = None
        self._initialized = False

        # PostgreSQL 相关
        self.async_engine = None
        self.AsyncSessionLocal = None
        
    async def initialize(self):
        """初始化数据库连接"""
        if self._initialized:
            return

        try:
            # 初始化 PostgreSQL 连接（使用全局单例）
            if self.pg_config:
                self.async_engine, self.AsyncSessionLocal = get_pg_engine_and_factory(
                    config=self.pg_config,
                    pool_size=10,
                    max_overflow=5,
                    pool_pre_ping=True,
                    echo=False
                )

            # 初始化 Redis 连接（使用全局单例，双模式）
            if self.redis_config:
                self._text_redis_client, self._binary_redis_client = get_dual_mode_async_redis_client(
                    redis_url=self.redis_config.get('url') if isinstance(self.redis_config, dict) else self.redis_config,
                    max_connections=50
                )

            self._initialized = True
            logger.info(f"命名空间 {self.namespace_name} 数据库连接初始化成功")

        except Exception as e:
            logger.error(f"初始化命名空间 {self.namespace_name} 数据库连接失败: {e}")
            traceback.print_exc()
            raise

    async def get_redis_client(self, decode: bool = True) -> redis.Redis:
        """获取 Redis 客户端（使用全局单例）"""
        try:
            if not self._initialized:
                await self.initialize()

            # 根据 decode 参数选择文本或二进制客户端
            client = self._text_redis_client if decode else self._binary_redis_client
            if not client:
                raise ValueError(f"命名空间 {self.namespace_name} 没有配置 Redis")

            return client
        except Exception as e:
            # 连接异常时重置初始化标志，允许重新初始化
            logger.error(f"获取 Redis 客户端失败: {e}")
            traceback.print_exc()
            self._initialized = False
            raise

    async def get_pg_session(self) -> AsyncSession:
        """获取 PostgreSQL 会话（使用全局单例）"""
        try:
            if not self._initialized:
                await self.initialize()

            if not self.AsyncSessionLocal:
                raise ValueError(f"命名空间 {self.namespace_name} 没有配置 PostgreSQL")

            return self.AsyncSessionLocal()
        except Exception as e:
            # 连接异常时重置初始化标志，允许重新初始化
            logger.error(f"获取 PostgreSQL 会话失败: {e}")
            traceback.print_exc()
            self._initialized = False
            raise

    async def close(self):
        """关闭数据库连接（由于使用全局单例，这里只重置状态）"""
        # 注意：连接池由全局单例管理，这里只清理引用
        self._text_redis_client = None
        self._binary_redis_client = None

        # PostgreSQL engine 也是全局单例，只清理引用
        self.async_engine = None
        self.AsyncSessionLocal = None

        self._initialized = False
        logger.info(f"命名空间 {self.namespace_name} 数据库连接已关闭")


class NamespaceDataAccessManager:
    """
    命名空间数据访问管理器
    管理多个命名空间的数据库连接，实现连接池和缓存
    """
    
    def __init__(self, task_center_base_url: str = None):
        self.task_center_base_url = task_center_base_url or os.getenv(
            'TASK_CENTER_BASE_URL', 'http://localhost:8001'
        )
        self._connections: Dict[str, NamespaceConnection] = {}
        self._session: Optional[aiohttp.ClientSession] = None
        
    async def _get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def get_namespace_config(self, namespace_name: str) -> dict:
        """从任务中心API获取命名空间配置"""
        # 使用127.0.0.1替代localhost，确保容器内能正确连接
        base_url = self.task_center_base_url
        if 'localhost' in base_url:
            base_url = base_url.replace('localhost', '127.0.0.1')
        url = f"{base_url}/api/v1/namespaces/{namespace_name}"
        
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    # API返回的是redis_config和pg_config，直接使用
                    redis_config = data.get('redis_config', {})
                    pg_config = data.get('pg_config', {})
                    
                    # 兼容旧格式：如果有redis_url和pg_url字段
                    if not redis_config and data.get('redis_url'):
                        redis_config = {'url': data.get('redis_url')}
                    
                    if not pg_config and data.get('pg_url'):
                        pg_config = {'url': data.get('pg_url')}
                    
                    return {
                        'name': data.get('name'),
                        'redis_config': redis_config,
                        'pg_config': pg_config
                    }
                else:
                    raise ValueError(f"无法获取命名空间 {namespace_name} 的配置: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"获取命名空间 {namespace_name} 配置失败: {e}")
            traceback.print_exc()
            raise
    
    async def get_connection(self, namespace_name: str) -> NamespaceConnection:
        """
        获取指定命名空间的数据库连接
        如果连接不存在，会自动创建并初始化
        """
        if namespace_name not in self._connections:
            # 获取命名空间配置
            config = await self.get_namespace_config(namespace_name)
            
            # 创建新的连接对象
            connection = NamespaceConnection(
                namespace_name=config['name'],
                redis_config=config['redis_config'],
                pg_config=config['pg_config']
            )
            
            # 初始化连接
            await connection.initialize()
            
            # 缓存连接对象
            self._connections[namespace_name] = connection
            logger.info(f"创建命名空间 {namespace_name} 的新连接")
        
        return self._connections[namespace_name]
    
    async def list_namespaces(self) -> List[dict]:
        """获取所有命名空间列表"""
        url = f"{self.task_center_base_url}/api/namespaces"
        
        try:
            session = await self._get_session()
            async with session.get(url) as resp:
                if resp.status == 200:
                    return await resp.json()
                else:
                    raise ValueError(f"无法获取命名空间列表: HTTP {resp.status}")
        except Exception as e:
            logger.error(f"获取命名空间列表失败: {e}")
            traceback.print_exc()
            raise
    
    async def close_connection(self, namespace_name: str):
        """关闭指定命名空间的连接"""
        if namespace_name in self._connections:
            await self._connections[namespace_name].close()
            del self._connections[namespace_name]
            logger.info(f"关闭命名空间 {namespace_name} 的连接")
    
    async def reset_connection(self, namespace_name: str):
        """重置指定命名空间的连接，清除缓存和初始化标志"""
        if namespace_name in self._connections:
            # 先关闭现有连接
            await self._connections[namespace_name].close()
            del self._connections[namespace_name]
            logger.info(f"重置命名空间 {namespace_name} 的连接，已清除缓存")
    
    async def close_all(self):
        """关闭所有连接"""
        for namespace_name in list(self._connections.keys()):
            await self.close_connection(namespace_name)
        
        if self._session:
            await self._session.close()
            self._session = None


class NamespaceJetTaskDataAccess:
    """
    支持命名空间的JetTask数据访问类
    所有数据查询方法都需要指定namespace_name参数
    """
    
    def __init__(self, manager: NamespaceDataAccessManager = None):
        self.manager = manager or NamespaceDataAccessManager()
        
    async def get_task_detail(self, namespace_name: str, task_id: str) -> dict:
        """获取任务详情"""
        conn = await self.manager.get_connection(namespace_name)
        redis_client = await conn.get_redis_client()
        
        try:
            # 构建任务键
            task_key = f"{conn.redis_prefix}:TASK:{task_id}"
            
            # 获取任务信息
            task_data = await redis_client.hgetall(task_key)
            if not task_data:
                return None
            
            # 解析任务数据
            result = {
                'id': task_id,
                'status': task_data.get('status', 'UNKNOWN'),
                'name': task_data.get('name', ''),
                'queue': task_data.get('queue', ''),
                'worker_id': task_data.get('worker_id', ''),
                'created_at': task_data.get('created_at', ''),
                'started_at': task_data.get('started_at', ''),
                'completed_at': task_data.get('completed_at', ''),
                'result': task_data.get('result', ''),
                'error': task_data.get('error', ''),
                'retry_count': int(task_data.get('retry_count', 0))
            }
            
            return result
            
        finally:
            await redis_client.aclose()
    
    async def get_queue_stats(self, namespace_name: str) -> List[dict]:
        """获取队列统计信息"""
        conn = await self.manager.get_connection(namespace_name)
        redis_client = await conn.get_redis_client()
        
        try:
            # 使用 RegistryManager 获取所有队列，避免 SCAN
            from jettask.messaging.registry import QueueRegistry
            registry = QueueRegistry(
                redis_client=None,
                async_redis_client=redis_client,
                redis_prefix=conn.redis_prefix
            )
            
            # 获取所有队列名称
            queue_names = await registry.get_all_queues()
            
            # 构建完整的队列键
            queue_keys = [f"{conn.redis_prefix}:QUEUE:{queue_name}" for queue_name in queue_names]
            
            stats = []
            for queue_key in queue_keys:
                # 提取队列名
                queue_name = queue_key.replace(f"{conn.redis_prefix}:QUEUE:", "")
                
                # 获取队列长度
                queue_length = await redis_client.xlen(queue_key)
                
                # 获取队列的消费组信息
                try:
                    groups_info = await redis_client.xinfo_groups(queue_key)
                    consumer_groups = len(groups_info)
                    total_consumers = sum(g.get('consumers', 0) for g in groups_info)
                    total_pending = sum(g.get('pending', 0) for g in groups_info)
                except redis.ResponseError:
                    consumer_groups = 0
                    total_consumers = 0
                    total_pending = 0
                
                stats.append({
                    'queue_name': queue_name,
                    'length': queue_length,
                    'consumer_groups': consumer_groups,
                    'consumers': total_consumers,
                    'pending': total_pending
                })
            
            return stats
            
        finally:
            await redis_client.aclose()
    
    async def get_scheduled_tasks(self, namespace_name: str, limit: int = 100, offset: int = 0) -> dict:
        """获取定时任务列表"""
        conn = await self.manager.get_connection(namespace_name)
        
        # 如果没有PostgreSQL配置，返回空结果
        if not conn.pg_config:
            return {
                'tasks': [],
                'total': 0,
                'has_more': False
            }
        
        async with await conn.get_pg_session() as session:
            try:
                # 查询定时任务（按命名空间筛选）
                query = text("""
                    SELECT 
                        id,
                        task_name as name,
                        queue_name as queue,
                        cron_expression,
                        interval_seconds,
                        CASE 
                            WHEN cron_expression IS NOT NULL THEN cron_expression
                            WHEN interval_seconds IS NOT NULL THEN interval_seconds::text || ' seconds'
                            ELSE 'unknown'
                        END as schedule,
                        json_build_object(
                            'args', task_args,
                            'kwargs', task_kwargs
                        ) as task_data,
                        enabled,
                        last_run_time as last_run_at,
                        next_run_time as next_run_at,
                        execution_count,
                        created_at,
                        updated_at,
                        description,
                        max_retries,
                        retry_delay,
                        timeout
                    FROM scheduled_tasks
                    WHERE namespace = :namespace
                    ORDER BY next_run_time ASC NULLS LAST, id ASC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(
                    query,
                    {'namespace': namespace_name, 'limit': limit, 'offset': offset}
                )
                tasks = result.fetchall()
                
                # 获取总数（按命名空间筛选）
                count_query = text("SELECT COUNT(*) FROM scheduled_tasks WHERE namespace = :namespace")
                count_result = await session.execute(count_query, {'namespace': namespace_name})
                total = count_result.scalar()
                
                # 格式化结果
                formatted_tasks = []
                for task in tasks:
                    # 解析调度配置 - 使用原始数据库字段
                    schedule_type = 'unknown'
                    schedule_config = {}
                    
                    if hasattr(task, 'cron_expression') and task.cron_expression:
                        # Cron表达式类型
                        schedule_type = 'cron'
                        schedule_config = {'cron_expression': task.cron_expression}
                    elif hasattr(task, 'interval_seconds') and task.interval_seconds:
                        # 间隔执行类型
                        schedule_type = 'interval'
                        try:
                            # 使用float而不是int，避免小数秒被截断为0
                            seconds = float(task.interval_seconds)
                            # 如果间隔小于1秒，至少显示为1秒，避免显示0秒的无效任务
                            if seconds < 1.0:
                                seconds = max(1, int(seconds))  # 小于1秒的向上舍入为1秒
                            else:
                                seconds = int(seconds)  # 大于等于1秒的保持整数显示
                            schedule_config = {'seconds': seconds}
                        except (ValueError, TypeError) as e:
                            logger.warning(f"解析间隔秒数失败: {task.interval_seconds}, 错误: {e}")
                            schedule_config = {}
                    
                    formatted_tasks.append({
                        'id': task.id,
                        'name': task.name,
                        'queue_name': task.queue,  # 前端期望 queue_name 而非 queue
                        'schedule_type': schedule_type,  # 新增调度类型
                        'schedule_config': schedule_config,  # 新增结构化调度配置
                        'schedule': task.schedule,  # 保留原始字段以兼容
                        'task_data': task.task_data if task.task_data else {},
                        'is_active': task.enabled,  # 前端期望 is_active 而非 enabled
                        'enabled': task.enabled,  # 保留原字段以兼容
                        'last_run': task.last_run_at.isoformat() if task.last_run_at else None,  # 前端期望 last_run
                        'last_run_at': task.last_run_at.isoformat() if task.last_run_at else None,  # 保留原字段
                        'next_run': task.next_run_at.isoformat() if task.next_run_at else None,  # 前端期望 next_run
                        'next_run_at': task.next_run_at.isoformat() if task.next_run_at else None,  # 保留原字段
                        'execution_count': task.execution_count,
                        'created_at': task.created_at.isoformat() if task.created_at else None,
                        'updated_at': task.updated_at.isoformat() if task.updated_at else None,
                        'description': task.description,
                        'max_retries': task.max_retries,
                        'retry_delay': task.retry_delay,
                        'timeout': task.timeout
                    })
                
                return {
                    'tasks': formatted_tasks,
                    'total': total,
                    'has_more': offset + limit < total
                }
                
            except Exception as e:
                logger.error(f"获取定时任务失败: {e}")
                traceback.print_exc()
                raise
    
    async def get_queue_history(self, namespace_name: str, queue_name: str, 
                                hours: int = 24, interval: int = 1) -> dict:
        """获取队列历史数据"""
        conn = await self.manager.get_connection(namespace_name)
        
        # 如果没有PostgreSQL配置，返回模拟数据
        if not conn.pg_config:
            return self._generate_mock_history(hours, interval)
        
        async with await conn.get_pg_session() as session:
            try:
                end_time = datetime.now(timezone.utc)
                start_time = end_time - timedelta(hours=hours)
                
                # 查询历史数据
                query = text("""
                    WITH time_series AS (
                        SELECT generate_series(
                            :start_time::timestamp,
                            :end_time::timestamp,
                            CAST(:interval AS interval)
                        ) AS bucket
                    )
                    SELECT 
                        ts.bucket,
                        COALESCE(AVG(qs.pending_count), 0) as avg_pending,
                        COALESCE(AVG(qs.processing_count), 0) as avg_processing,
                        COALESCE(AVG(qs.completed_count), 0) as avg_completed,
                        COALESCE(AVG(qs.failed_count), 0) as avg_failed,
                        COALESCE(AVG(qs.consumers), 0) as avg_consumers
                    FROM time_series ts
                    LEFT JOIN queue_stats qs ON 
                        qs.queue_name = :queue_name AND
                        qs.timestamp >= ts.bucket AND 
                        qs.timestamp < ts.bucket + CAST(:interval AS interval)
                    GROUP BY ts.bucket
                    ORDER BY ts.bucket
                """)
                
                result = await session.execute(
                    query,
                    {
                        'queue_name': queue_name,
                        'start_time': start_time,
                        'end_time': end_time,
                        'interval': f'{interval} hour'
                    }
                )
                
                rows = result.fetchall()
                
                # 格式化结果
                timestamps = []
                pending = []
                processing = []
                completed = []
                failed = []
                consumers = []
                
                for row in rows:
                    timestamps.append(row.bucket.isoformat())
                    pending.append(float(row.avg_pending))
                    processing.append(float(row.avg_processing))
                    completed.append(float(row.avg_completed))
                    failed.append(float(row.avg_failed))
                    consumers.append(float(row.avg_consumers))
                
                return {
                    'timestamps': timestamps,
                    'pending': pending,
                    'processing': processing,
                    'completed': completed,
                    'failed': failed,
                    'consumers': consumers
                }
                
            except Exception as e:
                logger.error(f"获取队列历史数据失败: {e}, 返回模拟数据")
                traceback.print_exc()
                return self._generate_mock_history(hours, interval)
    
    def _generate_mock_history(self, hours: int, interval: int) -> dict:
        """生成模拟历史数据"""
        import random
        
        now = datetime.now(timezone.utc)
        timestamps = []
        pending = []
        processing = []
        completed = []
        failed = []
        consumers = []
        
        for i in range(0, hours, interval):
            timestamp = now - timedelta(hours=hours-i)
            timestamps.append(timestamp.isoformat())
            
            # 生成随机数据
            base_value = 50 + random.randint(-20, 20)
            pending.append(base_value + random.randint(0, 30))
            processing.append(base_value // 2 + random.randint(0, 10))
            completed.append(base_value * 2 + random.randint(0, 50))
            failed.append(random.randint(0, 10))
            consumers.append(random.randint(1, 5))
        
        return {
            'timestamps': timestamps,
            'pending': pending,
            'processing': processing,
            'completed': completed,
            'failed': failed,
            'consumers': consumers
        }


# 全局实例
_global_manager = None

def get_namespace_data_access() -> NamespaceJetTaskDataAccess:
    """获取全局命名空间数据访问实例"""
    global _global_manager
    if _global_manager is None:
        manager = NamespaceDataAccessManager()
        _global_manager = NamespaceJetTaskDataAccess(manager)
    return _global_manager