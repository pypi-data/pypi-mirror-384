"""
独立的数据访问模块，不依赖 integrated_gradio_app.py
"""
import os
import asyncio
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional, Tuple
import redis.asyncio as redis
from sqlalchemy import text, bindparam
from sqlalchemy.ext.asyncio import AsyncSession

# 导入统一的数据库连接工具
from ..utils.db_connector import (
    get_dual_mode_async_redis_client,
    get_pg_engine_and_factory
)

# 设置日志
logger = logging.getLogger(__name__)


class RedisConfig:
    """Redis配置"""
    def __init__(self, host='localhost', port=6379, db=0, password=None):
        self.host = host
        self.port = port
        self.db = db
        self.password = password
    
    @classmethod
    def from_env(cls):
        import os
        return cls(
            host=os.getenv('REDIS_HOST', 'localhost'),
            port=int(os.getenv('REDIS_PORT', 6379)),
            db=int(os.getenv('REDIS_DB', 0)),
            password=os.getenv('REDIS_PASSWORD')
        )


class PostgreSQLConfig:
    """PostgreSQL配置"""
    def __init__(self, host='localhost', port=5432, user='postgres', password='', database='jettask'):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.database = database
    
    @property
    def dsn(self):
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"
    
    @classmethod
    def from_env(cls):
        import os
        return cls(
            host=os.getenv('POSTGRES_HOST', 'localhost'),
            port=int(os.getenv('POSTGRES_PORT', 5432)),
            user=os.getenv('POSTGRES_USER', 'jettask'),
            password=os.getenv('POSTGRES_PASSWORD', '123456'),
            database=os.getenv('POSTGRES_DB', 'jettask')
        )


class JetTaskDataAccess:
    """JetTask数据访问类（使用统一的数据库连接工具）"""

    def __init__(self):
        self.redis_config = RedisConfig.from_env()
        self.pg_config = PostgreSQLConfig.from_env()
        # Redis前缀可以从环境变量配置，默认为 "jettask"
        self.redis_prefix = os.environ.get('JETTASK_REDIS_PREFIX', 'jettask')

        # 使用全局单例连接池
        self._text_redis_client: Optional[redis.Redis] = None
        self._binary_redis_client: Optional[redis.Redis] = None

        # PostgreSQL 相关
        self.async_engine = None
        self.AsyncSessionLocal = None
        
    async def initialize(self):
        """初始化数据库连接（使用全局单例）"""
        try:
            # 构建 Redis URL
            redis_url = f"redis://"
            if self.redis_config.password:
                redis_url += f":{self.redis_config.password}@"
            redis_url += f"{self.redis_config.host}:{self.redis_config.port}/{self.redis_config.db}"

            # 构建 PostgreSQL 配置
            pg_config = {
                'host': self.pg_config.host,
                'port': self.pg_config.port,
                'user': self.pg_config.user,
                'password': self.pg_config.password,
                'database': self.pg_config.database
            }

            # 初始化 PostgreSQL 连接（使用全局单例）
            self.async_engine, self.AsyncSessionLocal = get_pg_engine_and_factory(
                config=pg_config,
                pool_size=10,
                max_overflow=5,
                pool_pre_ping=True,
                echo=False
            )

            # 初始化 Redis 连接（使用全局单例，双模式）
            self._text_redis_client, self._binary_redis_client = get_dual_mode_async_redis_client(
                redis_url=redis_url,
                max_connections=50,
                socket_keepalive=True,
                socket_connect_timeout=5,
                retry_on_timeout=True
            )

            logger.info("数据库连接初始化成功")

        except Exception as e:
            logger.error(f"数据库连接初始化失败: {e}")
            raise
    
    def get_session(self):
        """获取数据库会话（作为上下文管理器）"""
        return self.AsyncSessionLocal()
    
    async def close(self):
        """关闭数据库连接（由于使用全局单例，这里只重置状态）"""
        # 注意：连接池由全局单例管理，这里只清理引用
        self._text_redis_client = None
        self._binary_redis_client = None
        self.async_engine = None
        self.AsyncSessionLocal = None

    async def get_redis_client(self):
        """获取 Redis 客户端（使用全局单例）"""
        if not self._text_redis_client:
            raise RuntimeError("Redis client not initialized")
        return self._text_redis_client

    async def get_binary_redis_client(self):
        """获取二进制 Redis 客户端（用于Stream操作，使用全局单例）"""
        if not self._binary_redis_client:
            raise RuntimeError("Binary Redis client not initialized")
        return self._binary_redis_client
    
    async def fetch_queues_data(self) -> List[Dict]:
        """获取队列数据（基于Redis Stream）"""
        try:
            redis_client = await self.get_redis_client()
            binary_redis_client = await self.get_binary_redis_client()  # 用于Stream操作
            
            # 获取所有Stream类型的队列 - JetTask使用 jettask:QUEUE:队列名 格式
            all_keys = await redis_client.keys(f"{self.redis_prefix}:QUEUE:*")
            queues_data = []
            queue_names = set()
            
            for key in all_keys:
                # 检查是否是Stream类型
                key_type = await redis_client.type(key)
                if key_type == 'stream':
                    # 解析队列名称 - 格式: jettask:QUEUE:队列名
                    parts = key.split(':')
                    if len(parts) >= 3 and parts[0] == self.redis_prefix and parts[1] == 'QUEUE':
                        queue_name = ':'.join(parts[2:])  # 支持带冒号的队列名
                        queue_names.add(queue_name)
            
            # 获取每个队列的详细信息
            for queue_name in queue_names:
                stream_key = f"{self.redis_prefix}:QUEUE:{queue_name}"
                
                try:
                    # 使用二进制客户端获取Stream信息
                    stream_info = await binary_redis_client.xinfo_stream(stream_key)
                    # 直接提取需要的字段（字符串键）
                    stream_length = stream_info.get('length', 0)
                    
                    # 获取消费者组信息
                    groups_info = []
                    try:
                        groups_info_raw = await binary_redis_client.xinfo_groups(stream_key)
                        for group in groups_info_raw:
                            group_name = group.get('name', '')
                            if isinstance(group_name, bytes):
                                group_name = group_name.decode('utf-8')
                            groups_info.append({
                                'name': group_name,
                                'pending': group.get('pending', 0)
                            })
                    except:
                        pass
                    
                    pending_count = 0
                    processing_count = 0
                    
                    # 统计各消费者组的待处理消息
                    for group in groups_info:
                        pending_count += group.get('pending', 0)
                        
                        # 获取消费者信息
                        if group.get('name'):
                            try:
                                consumers = await binary_redis_client.xinfo_consumers(
                                    stream_key,
                                    group['name']
                                )
                                for consumer in consumers:
                                    processing_count += consumer.get('pending', 0)
                            except:
                                pass
                    
                    # Stream的长度即为总消息数
                    total_messages = stream_length if 'stream_length' in locals() else 0
                    
                    # 完成的消息数 = 总消息数 - 待处理 - 处理中
                    completed_count = max(0, total_messages - pending_count - processing_count)
                    
                    queues_data.append({
                        '队列名称': queue_name,
                        '待处理': pending_count,
                        '处理中': processing_count,
                        '已完成': completed_count,
                        '失败': 0,  # Stream中没有直接的失败计数
                        '总计': total_messages
                    })
                    
                except Exception as e:
                    logger.warning(f"获取队列 {queue_name} 信息失败: {e}")
                    # 如果获取详细信息失败，至少返回队列名称
                    queues_data.append({
                        '队列名称': queue_name,
                        '待处理': 0,
                        '处理中': 0,
                        '已完成': 0,
                        '失败': 0,
                        '总计': 0
                    })
            
            await redis_client.close()
            await binary_redis_client.close()
            return sorted(queues_data, key=lambda x: x['队列名称'])
            
        except Exception as e:
            logger.error(f"获取队列数据失败: {e}")
            return []
    
    async def fetch_queue_details(self, start_time: datetime = None, end_time: datetime = None, 
                                   time_range_minutes: int = None, queues: List[str] = None) -> List[Dict]:
        """获取队列详细信息，包含消费速度、在线workers等
        
        Args:
            start_time: 开始时间（优先使用）
            end_time: 结束时间（优先使用）
            time_range_minutes: 时间范围（分钟），仅在没有指定start_time/end_time时使用
            queues: 要筛选的队列列表，如果为None则返回所有队列
        """
        # 确定时间范围
        if start_time and end_time:
            # 使用指定的时间范围
            query_start_time = start_time
            query_end_time = end_time
        elif time_range_minutes:
            # 向后兼容：使用最近N分钟
            query_end_time = datetime.now(timezone.utc)
            query_start_time = query_end_time - timedelta(minutes=time_range_minutes)
        else:
            # 默认最近15分钟
            query_end_time = datetime.now(timezone.utc)
            query_start_time = query_end_time - timedelta(minutes=15)
        
        try:
            redis_client = await self.get_redis_client()
            
            # 获取所有队列名称
            all_keys = await redis_client.keys(f"{self.redis_prefix}:QUEUE:*")
            queue_details = []
            
            for key in all_keys:
                # 检查是否是Stream类型
                key_type = await redis_client.type(key)
                if key_type == 'stream':
                    # 解析队列名称
                    parts = key.split(':')
                    if len(parts) >= 3 and parts[0] == self.redis_prefix and parts[1] == 'QUEUE':
                        queue_name = ':'.join(parts[2:])
                        
                        # 如果指定了队列筛选，检查当前队列是否在筛选列表中
                        if queues and queue_name not in queues:
                            continue
                        
                        # 获取活跃的workers数量
                        active_workers = 0
                        try:
                            worker_keys = await redis_client.keys(f"{self.redis_prefix}:WORKER:*")
                            for worker_key in worker_keys:
                                worker_info = await redis_client.hgetall(worker_key)
                                if worker_info:
                                    last_heartbeat = worker_info.get('last_heartbeat')
                                    if last_heartbeat:
                                        try:
                                            heartbeat_time = float(last_heartbeat)
                                            if time.time() - heartbeat_time < 60:
                                                worker_queues = worker_info.get('queues', '')
                                                if queue_name in worker_queues:
                                                    active_workers += 1
                                        except:
                                            pass
                        except:
                            pass
                        
                        # 从PostgreSQL获取队列统计信息
                        total_messages = 0
                        visible_messages = 0
                        completed_count = 0
                        failed_count = 0
                        consumption_rate = 0
                        success_rate = 0
                        
                        if self.AsyncSessionLocal:
                            try:
                                async with self.AsyncSessionLocal() as session:
                                    # 获取指定时间范围的所有统计数据
                                    query = text("""
                                        SELECT 
                                            COUNT(*) as total,
                                            COUNT(CASE WHEN status = 'pending' THEN 1 END) as pending_count,
                                            COUNT(CASE WHEN status = 'success' THEN 1 END) as completed,
                                            COUNT(CASE WHEN status = 'error' THEN 1 END) as failed
                                        FROM tasks 
                                        WHERE queue = :queue_name
                                            AND created_at >= :start_time
                                            AND created_at <= :end_time
                                    """)
                                    result = await session.execute(query, {
                                        'queue_name': queue_name,
                                        'start_time': query_start_time,
                                        'end_time': query_end_time
                                    })
                                    row = result.first()
                                    if row:
                                        total_messages = row.total or 0
                                        visible_messages = row.pending_count or 0
                                        completed_count = row.completed or 0
                                        failed_count = row.failed or 0
                                        
                                        # 计算消费速度（任务/分钟）
                                        time_diff_minutes = (query_end_time - query_start_time).total_seconds() / 60
                                        if time_diff_minutes > 0:
                                            consumption_rate = round(total_messages / time_diff_minutes, 2)
                                        
                                        # 计算成功率
                                        if total_messages > 0:
                                            success_rate = round((completed_count / total_messages) * 100, 2)
                            except Exception as e:
                                logger.warning(f"获取队列 {queue_name} 统计信息失败: {e}")
                        
                        # 队列状态
                        queue_status = 'active' if total_messages > 0 or active_workers > 0 else 'idle'
                        
                        queue_details.append({
                            'queue_name': queue_name,
                            'message_count': total_messages,  # 总消息数量（基于时间范围）
                            'visible_messages': visible_messages,  # 可见消息（基于时间范围，status='pending'）
                            'invisible_messages': 0,  # 不可见消息（现在设为0，不从Redis获取）
                            'completed': completed_count,  # 成功数（基于时间范围，status='success'）
                            'failed': failed_count,  # 失败数（基于时间范围，status='error'）
                            'consumption_rate': consumption_rate,  # 消费速度（任务/分钟）
                            'success_rate': success_rate,  # 成功率（百分比）
                            'active_workers': active_workers,  # 在线workers
                            'queue_status': queue_status  # 队列状态
                        })
            
            await redis_client.close()
            return sorted(queue_details, key=lambda x: x['queue_name'])
            
        except Exception as e:
            logger.error(f"获取队列详细信息失败: {e}")
            return []
    
    async def get_latest_task_time(self, queue_name: str) -> Optional[datetime]:
        """获取队列的最新任务时间"""
        try:
            if not self.AsyncSessionLocal:
                await self.initialize()
            
            async with self.AsyncSessionLocal() as session:
                query = text("""
                    SELECT MAX(created_at) as latest_time
                    FROM tasks
                    WHERE queue = :queue_name
                """)
                
                result = await session.execute(query, {'queue_name': queue_name})
                row = result.fetchone()
                
                if row and row.latest_time:
                    return row.latest_time
                return None
                
        except Exception as e:
            logger.error(f"获取最新任务时间失败: {e}")
            return None
    
    async def fetch_task_details(self, task_id: str, consumer_group: Optional[str] = None) -> Optional[Dict]:
        """获取单个任务的详细数据（包括task_data、result和error_message）
        
        Args:
            task_id: 任务ID (stream_id)
            consumer_group: 消费者组名称（可选，用于精确定位）
        """
        try:
            if not self.AsyncSessionLocal:
                await self.initialize()
            
            async with self.AsyncSessionLocal() as session:
                # 根据是否提供consumer_group来调整查询
                if consumer_group:
                    # 如果提供了consumer_group，精确查询特定消费组的执行结果
                    query = text("""
                        SELECT 
                            t.stream_id as id,
                            t.payload as task_data,
                            tr.consumer_group,
                            tr.result,
                            tr.error_message
                        FROM tasks t
                        LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id 
                            AND tr.consumer_group = :consumer_group
                        WHERE t.stream_id = :task_id
                        LIMIT 1
                    """)
                    params = {'task_id': task_id, 'consumer_group': consumer_group}
                else:
                    # 如果没有提供consumer_group，返回第一个找到的结果（向后兼容）
                    query = text("""
                        SELECT 
                            t.stream_id as id,
                            t.payload as task_data,
                            tr.consumer_group,
                            tr.result,
                            tr.error_message
                        FROM tasks t
                        LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                        WHERE t.stream_id = :task_id
                        ORDER BY tr.updated_at DESC NULLS LAST
                        LIMIT 1
                    """)
                    params = {'task_id': task_id}
                
                result = await session.execute(query, params)
                row = result.fetchone()
                
                if row:
                    return {
                        'id': row.id,
                        'task_data': row.task_data,
                        'consumer_group': row.consumer_group if hasattr(row, 'consumer_group') else None,
                        'result': row.result,
                        'error_message': row.error_message
                    }
                return None
                
        except Exception as e:
            logger.error(f"获取任务详细数据失败: {e}")
            return None
    
    async def fetch_queue_flow_rates(self,
                                     queue_name: str,
                                     start_time: datetime,
                                     end_time: datetime,
                                     filters: List[Dict] = None) -> Tuple[List[Dict], str]:
        """获取队列的三种流量速率：入队、开始执行、完成
        
        Args:
            queue_name: 队列名称
            start_time: 开始时间
            end_time: 结束时间
            filters: 筛选条件列表，与fetch_tasks_with_filters的格式相同
        """
        try:
            if not self.AsyncSessionLocal:
                await self.initialize()
            print(f'{filters=}')
            async with self.AsyncSessionLocal() as session:
                # 动态计算时间间隔，目标是生成约200个时间点
                TARGET_POINTS = 200
                duration = (end_time - start_time).total_seconds()
                
                # 计算理想的间隔秒数
                ideal_interval_seconds = duration / TARGET_POINTS
                print(f'{duration=} {TARGET_POINTS=} {ideal_interval_seconds=}')
                # 将间隔秒数规范化到合理的值（与fetch_queue_timeline_data保持一致）
                if ideal_interval_seconds <= 1:
                    interval_seconds = 1
                    interval = '1 seconds'
                    granularity = 'second'
                elif ideal_interval_seconds <= 5:
                    interval_seconds = 5
                    interval = '5 seconds'
                    granularity = 'second'
                elif ideal_interval_seconds <= 10:
                    interval_seconds = 10
                    interval = '10 seconds'
                    granularity = 'second'
                elif ideal_interval_seconds <= 30:
                    interval_seconds = 30
                    interval = '30 seconds'
                    granularity = 'second'
                elif ideal_interval_seconds <= 60:
                    interval_seconds = 60
                    interval = '1 minute'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 120:
                    interval_seconds = 120
                    interval = '2 minutes'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 300:
                    interval_seconds = 300
                    interval = '5 minutes'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 600:
                    interval_seconds = 600
                    interval = '10 minutes'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 900:
                    interval_seconds = 900
                    interval = '15 minutes'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 1800:
                    interval_seconds = 1800
                    interval = '30 minutes'
                    granularity = 'minute'
                elif ideal_interval_seconds <= 3600:
                    interval_seconds = 3600
                    interval = '1 hour'
                    granularity = 'hour'
                elif ideal_interval_seconds <= 7200:
                    interval_seconds = 7200
                    interval = '2 hours'
                    granularity = 'hour'
                elif ideal_interval_seconds <= 14400:
                    interval_seconds = 14400
                    interval = '4 hours'
                    granularity = 'hour'
                elif ideal_interval_seconds <= 21600:
                    interval_seconds = 21600
                    interval = '6 hours'
                    granularity = 'hour'
                elif ideal_interval_seconds <= 43200:
                    interval_seconds = 43200
                    interval = '12 hours'
                    granularity = 'hour'
                else:
                    interval_seconds = 86400
                    interval = '1 day'
                    granularity = 'day'
                
                # 重新计算实际点数
                actual_points = int(duration / interval_seconds) + 1
                logger.info(f"使用时间间隔: {interval_seconds}秒 ({interval}), 预计生成 {actual_points} 个时间点")
                
                # 根据粒度确定 date_trunc 的单位
                if granularity == 'second':
                    trunc_unit = 'second'
                elif granularity == 'minute':
                    trunc_unit = 'minute'
                elif granularity == 'hour':
                    trunc_unit = 'hour'
                else:  # day
                    trunc_unit = 'day'
                
                # 构建筛选条件的WHERE子句
                # 分别为tasks表和task_runs表构建条件
                filter_conditions_enqueue = []  # 用于enqueued_rate（只有tasks表）
                filter_conditions_complete = []  # 用于completed_rate和failed_count（有join）
                filter_params = {}
                has_status_filter = False
                status_filter_value = None
                
                if filters:
                    for idx, filter_item in enumerate(filters):
                        # 跳过被禁用的筛选条件
                        if filter_item.get('enabled') == False:
                            continue
                            
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        if not field or not operator:
                            continue
                        
                        # 检查是否有status筛选
                        if field == 'status' and operator == 'eq':
                            has_status_filter = True
                            status_filter_value = value
                        
                        # 判断字段属于哪个表
                        # task_runs表独有的字段
                        task_runs_only_fields = ['task_name', 'consumer_group', 'worker_id', 'duration_ms', 
                                                 'retry_count', 'error_message', 'result', 'start_time', 
                                                 'end_time', 'consumer_name']
                        # tasks表和task_runs表都有的字段
                        both_tables_fields = ['status']
                        # tasks表独有的字段
                        tasks_only_fields = ['stream_id', 'queue', 'namespace', 'scheduled_task_id', 
                                           'payload', 'priority', 'created_at', 'source', 'metadata']
                        
                        param_name = f'filter_{idx}_value'
                        
                        if field in task_runs_only_fields:
                            # 只在task_runs表中的字段，只能用于completed_rate和failed_count查询
                            # enqueued_rate查询不支持这些字段
                            
                            # 特殊处理空值判断
                            if operator in ['is_null', 'is_not_null']:
                                if operator == 'is_null':
                                    filter_conditions_complete.append(f"tr.{field} IS NULL")
                                else:
                                    filter_conditions_complete.append(f"tr.{field} IS NOT NULL")
                            else:
                                op_map = {
                                    'eq': '=',
                                    'ne': '!=',
                                    'contains': 'LIKE',
                                    'starts_with': 'LIKE',
                                    'ends_with': 'LIKE'
                                }
                                sql_op = op_map.get(operator, '=')
                                
                                if operator == 'contains':
                                    filter_params[param_name] = f'%{value}%'
                                elif operator == 'starts_with':
                                    filter_params[param_name] = f'{value}%'
                                elif operator == 'ends_with':
                                    filter_params[param_name] = f'%{value}'
                                else:
                                    filter_params[param_name] = value
                                
                                filter_conditions_complete.append(f"tr.{field} {sql_op} :{param_name}")
                                
                        elif field == 'status':
                            # status字段在两个表中都存在，需要特殊处理
                            # tasks表中没有status字段，task_runs表中有
                            # 对于enqueued_rate，不应用status筛选
                            # 对于completed_rate和failed_count，应用到tr.status
                            
                            if operator in ['is_null', 'is_not_null']:
                                if operator == 'is_null':
                                    filter_conditions_complete.append(f"tr.{field} IS NULL")
                                else:
                                    filter_conditions_complete.append(f"tr.{field} IS NOT NULL")
                            else:
                                op_map = {
                                    'eq': '=',
                                    'ne': '!=',
                                    'contains': 'LIKE',
                                    'starts_with': 'LIKE',
                                    'ends_with': 'LIKE'
                                }
                                sql_op = op_map.get(operator, '=')
                                
                                if operator == 'contains':
                                    filter_params[param_name] = f'%{value}%'
                                elif operator == 'starts_with':
                                    filter_params[param_name] = f'{value}%'
                                elif operator == 'ends_with':
                                    filter_params[param_name] = f'%{value}'
                                else:
                                    filter_params[param_name] = value
                                
                                filter_conditions_complete.append(f"tr.{field} {sql_op} :{param_name}")
                                
                        elif field == 'id':
                            # id字段特殊处理，对应tasks表的stream_id
                            if operator in ['is_null', 'is_not_null']:
                                if operator == 'is_null':
                                    filter_conditions_enqueue.append(f"stream_id IS NULL")
                                    filter_conditions_complete.append(f"t.stream_id IS NULL")
                                else:
                                    filter_conditions_enqueue.append(f"stream_id IS NOT NULL")
                                    filter_conditions_complete.append(f"t.stream_id IS NOT NULL")
                            else:
                                op_map = {
                                    'eq': '=',
                                    'ne': '!=',
                                    'contains': 'LIKE',
                                    'starts_with': 'LIKE',
                                    'ends_with': 'LIKE'
                                }
                                sql_op = op_map.get(operator, '=')
                                
                                if operator == 'contains':
                                    filter_params[param_name] = f'%{value}%'
                                elif operator == 'starts_with':
                                    filter_params[param_name] = f'{value}%'
                                elif operator == 'ends_with':
                                    filter_params[param_name] = f'%{value}'
                                else:
                                    filter_params[param_name] = value
                                
                                filter_conditions_enqueue.append(f"stream_id {sql_op} :{param_name}")
                                filter_conditions_complete.append(f"t.stream_id {sql_op} :{param_name}")
                                
                        elif field == 'scheduled_task_id':
                            # scheduled_task_id字段特殊处理，数据库中是TEXT类型，需要转换
                            if operator in ['is_null', 'is_not_null']:
                                if operator == 'is_null':
                                    filter_conditions_enqueue.append(f"scheduled_task_id IS NULL")
                                    filter_conditions_complete.append(f"t.scheduled_task_id IS NULL")
                                else:
                                    filter_conditions_enqueue.append(f"scheduled_task_id IS NOT NULL")
                                    filter_conditions_complete.append(f"t.scheduled_task_id IS NOT NULL")
                            else:
                                op_map = {
                                    'eq': '=',
                                    'ne': '!=',
                                    'contains': 'LIKE',
                                    'starts_with': 'LIKE',
                                    'ends_with': 'LIKE'
                                }
                                sql_op = op_map.get(operator, '=')
                                
                                # 将值转换为字符串
                                if operator == 'contains':
                                    filter_params[param_name] = f'%{str(value)}%'
                                elif operator == 'starts_with':
                                    filter_params[param_name] = f'{str(value)}%'
                                elif operator == 'ends_with':
                                    filter_params[param_name] = f'%{str(value)}'
                                else:
                                    filter_params[param_name] = str(value)
                                
                                filter_conditions_enqueue.append(f"scheduled_task_id {sql_op} :{param_name}")
                                filter_conditions_complete.append(f"t.scheduled_task_id {sql_op} :{param_name}")
                                
                        else:
                            # 其他字段默认属于tasks表
                            # 特殊处理空值判断
                            if operator in ['is_null', 'is_not_null']:
                                if operator == 'is_null':
                                    filter_conditions_enqueue.append(f"{field} IS NULL")
                                    filter_conditions_complete.append(f"t.{field} IS NULL")
                                else:
                                    filter_conditions_enqueue.append(f"{field} IS NOT NULL")
                                    filter_conditions_complete.append(f"t.{field} IS NOT NULL")
                            else:
                                # 处理其他操作符
                                op_map = {
                                    'eq': '=',
                                    'ne': '!=',
                                    'contains': 'LIKE',
                                    'starts_with': 'LIKE',
                                    'ends_with': 'LIKE'
                                }
                                sql_op = op_map.get(operator, '=')
                                
                                if operator == 'contains':
                                    filter_params[param_name] = f'%{value}%'
                                elif operator == 'starts_with':
                                    filter_params[param_name] = f'{value}%'
                                elif operator == 'ends_with':
                                    filter_params[param_name] = f'%{value}'
                                else:
                                    filter_params[param_name] = value
                                
                                filter_conditions_enqueue.append(f"{field} {sql_op} :{param_name}")
                                filter_conditions_complete.append(f"t.{field} {sql_op} :{param_name}")
                
                # 构建额外的WHERE条件
                extra_where_enqueue = ""
                extra_where_complete = ""
                if filter_conditions_enqueue:
                    extra_where_enqueue = " AND " + " AND ".join(filter_conditions_enqueue)
                if filter_conditions_complete:
                    extra_where_complete = " AND " + " AND ".join(filter_conditions_complete)
                
                # SQL查询：获取入队速率、完成速率和失败数
                # 重要：时间桶对齐到固定边界（如整5秒、整分钟），确保聚合区间稳定
                query = text(f"""
                    WITH time_series AS (
                        -- 生成对齐到固定边界的时间序列
                        -- 结束时间需要加一个间隔，确保包含所有在end_time之前的数据
                        SELECT generate_series(
                            to_timestamp(FLOOR(EXTRACT(epoch FROM CAST(:start_time AS timestamptz)) / {interval_seconds}) * {interval_seconds}),
                            to_timestamp(CEILING(EXTRACT(epoch FROM CAST(:end_time AS timestamptz)) / {interval_seconds}) * {interval_seconds} + {interval_seconds}),
                            CAST(:interval AS interval)
                        ) AS time_bucket
                    ),
                    enqueued_rate AS (
                        SELECT 
                            -- 对齐到固定的时间边界
                            to_timestamp(
                                FLOOR(EXTRACT(epoch FROM created_at) / {interval_seconds}) * {interval_seconds}
                            ) AS time_bucket,
                            COUNT(*) AS count
                        FROM tasks
                        WHERE (queue = :queue_name OR queue LIKE :queue_pattern)
                            AND created_at >= :start_time
                            AND created_at <= :end_time
                            {extra_where_enqueue}
                        GROUP BY 1
                    ),
                    completed_rate AS (
                        SELECT 
                            -- 对齐到固定的时间边界
                            to_timestamp(
                                FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}
                            ) AS time_bucket,
                            COUNT(*) AS count
                        FROM tasks t
                        JOIN task_runs tr ON t.stream_id = tr.stream_id
                        WHERE (t.queue = :queue_name OR t.queue LIKE :queue_pattern)
                            AND tr.end_time >= :start_time
                            AND tr.end_time <= :end_time
                            AND tr.status = 'success'
                            {extra_where_complete}
                        GROUP BY 1
                    ),
                    failed_count AS (
                        SELECT 
                            -- 对齐到固定的时间边界
                            to_timestamp(
                                FLOOR(EXTRACT(epoch FROM tr.end_time) / {interval_seconds}) * {interval_seconds}
                            ) AS time_bucket,
                            COUNT(*) AS count
                        FROM tasks t
                        JOIN task_runs tr ON t.stream_id = tr.stream_id
                        WHERE (t.queue = :queue_name OR t.queue LIKE :queue_pattern)
                            AND tr.end_time >= :start_time
                            AND tr.end_time <= :end_time
                            AND tr.status IN ('failed', 'error')
                            {extra_where_complete}
                        GROUP BY 1
                    )
                    SELECT 
                        ts.time_bucket,
                        COALESCE(e.count, 0) AS enqueued,
                        COALESCE(c.count, 0) AS completed,
                        COALESCE(f.count, 0) AS failed
                    FROM time_series ts
                    LEFT JOIN enqueued_rate e ON ts.time_bucket = e.time_bucket
                    LEFT JOIN completed_rate c ON ts.time_bucket = c.time_bucket
                    LEFT JOIN failed_count f ON ts.time_bucket = f.time_bucket
                    ORDER BY ts.time_bucket
                """)
                
                # 合并参数
                params = {
                    'queue_name': queue_name,
                    'queue_pattern': f'{queue_name}:%',  # 匹配所有优先级队列
                    'start_time': start_time,
                    'end_time': end_time,
                    'interval': interval
                }
                params.update(filter_params)
                
                logger.info(f"执行查询 - 队列: {queue_name}, 时间范围: {start_time} 到 {end_time}, 间隔: {interval}, 筛选条件: {len(filter_conditions_enqueue) + len(filter_conditions_complete)} 个")
                
                result = await session.execute(query, params)
                
                rows = result.fetchall()
                logger.info(f"查询返回 {len(rows)} 行数据")
                
                # 转换为前端需要的格式
                data = []
                total_enqueued = 0
                total_completed = 0
                total_failed = 0
                end_index = len(rows) - 1
                
                # 根据status筛选决定显示什么指标
                if has_status_filter:
                    # 有status筛选时，需要特殊处理
                    for idx, row in enumerate(rows):
                        time_point = row.time_bucket.isoformat()
                        
                        # 累计统计
                        total_enqueued += row.enqueued
                        
                        # 添加入队速率数据点（蓝色）
                        data.append({
                            'time': time_point,
                            'value': row.enqueued or None if idx > 0 and end_index != idx else row.enqueued,
                            'metric': '入队速率'
                        })
                        
                        # 根据筛选的状态决定是否显示完成速率和失败数
                        if status_filter_value == 'success':
                            # 筛选成功任务时，显示完成速率，不显示失败数
                            total_completed += row.completed
                            data.append({
                                'time': time_point,
                                'value': row.completed or None if idx > 0 and end_index != idx else row.completed,
                                'metric': '完成速率'
                            })
                            data.append({
                                'time': time_point,
                                'value': None,
                                'metric': '失败数'
                            })
                        elif status_filter_value == 'error':
                            # 筛选失败任务时，不显示完成速率，显示失败数
                            total_failed += row.failed
                            data.append({
                                'time': time_point,
                                'value': None,
                                'metric': '完成速率'
                            })
                            data.append({
                                'time': time_point,
                                'value': row.failed or None if idx > 0 and end_index != idx else row.failed,
                                'metric': '失败数'
                            })
                        else:
                            # 其他状态（running, pending, rejected等），不显示完成速率和失败数
                            data.append({
                                'time': time_point,
                                'value': None,
                                'metric': '完成速率'
                            })
                            data.append({
                                'time': time_point,
                                'value': None,
                                'metric': '失败数'
                            })
                else:
                    # 默认或其他状态筛选：显示标准指标
                    for idx, row in enumerate(rows):
                        time_point = row.time_bucket.isoformat()
                        
                        # 累计统计
                        total_enqueued += row.enqueued
                        total_completed += row.completed
                        total_failed += row.failed
                        
                        # 添加入队速率数据点（蓝色）
                        data.append({
                            'time': time_point,
                            'value': row.enqueued or None if idx > 0 and end_index != idx else row.enqueued,
                            'metric': '入队速率'
                        })
                        # 添加完成速率数据点（绿色）
                        data.append({
                            'time': time_point,
                            'value': row.completed or None if idx > 0 and end_index != idx else row.completed,
                            'metric': '完成速率'
                        })
                        # 添加失败数数据点（红色）
                        data.append({
                            'time': time_point,
                            'value': row.failed or None if idx > 0 and end_index != idx else row.failed,
                            'metric': '失败数'
                        })
                    
                    # 调试日志：每10个点输出一次
                    if idx % 10 == 0 or idx == len(rows) - 1:
                        logger.debug(f"Row {idx}: time={time_point}, enqueued={row.enqueued}, completed={row.completed}, failed={row.failed}")
                
                logger.info(f"数据汇总 - 总入队: {total_enqueued}, 总完成: {total_completed}, 总失败: {total_failed}")
                
                return data, granularity
                
        except Exception as e:
            logger.error(f"获取队列流量速率失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    async def fetch_queue_timeline_data(self, 
                                      queues: List[str], 
                                      start_time: datetime, 
                                      end_time: datetime,
                                      filters: List[Dict] = None) -> List[Dict]:
        """获取队列时间线数据 - 优化版本，使用generate_series生成完整时间序列
        
        Args:
            queues: 队列名称列表
            start_time: 开始时间
            end_time: 结束时间
            filters: 筛选条件列表，与fetch_tasks_with_filters的格式相同
        """
        try:
            if not self.AsyncSessionLocal:
                await self.initialize()
            
            async with self.AsyncSessionLocal() as session:
                # 构建队列名称列表字符串
                queue_names_str = "', '".join(queues)
                
                # 动态计算时间间隔，目标是生成约200个时间点
                TARGET_POINTS = 200
                duration = (end_time - start_time).total_seconds()
                
                # 计算理想的间隔秒数
                ideal_interval_seconds = duration / TARGET_POINTS
                
                # 将间隔秒数规范化到合理的值
                if ideal_interval_seconds <= 1:
                    interval_seconds = 1
                    interval = '1 seconds'
                    trunc_unit = 'second'
                elif ideal_interval_seconds <= 5:
                    interval_seconds = 5
                    interval = '5 seconds'
                    trunc_unit = 'second'
                elif ideal_interval_seconds <= 10:
                    interval_seconds = 10
                    interval = '10 seconds'
                    trunc_unit = 'second'
                elif ideal_interval_seconds <= 30:
                    interval_seconds = 30
                    interval = '30 seconds'
                    trunc_unit = 'second'
                elif ideal_interval_seconds <= 60:
                    interval_seconds = 60
                    interval = '1 minute'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 120:
                    interval_seconds = 120
                    interval = '2 minutes'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 300:
                    interval_seconds = 300
                    interval = '5 minutes'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 600:
                    interval_seconds = 600
                    interval = '10 minutes'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 900:
                    interval_seconds = 900
                    interval = '15 minutes'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 1800:
                    interval_seconds = 1800
                    interval = '30 minutes'
                    trunc_unit = 'minute'
                elif ideal_interval_seconds <= 3600:
                    interval_seconds = 3600
                    interval = '1 hour'
                    trunc_unit = 'hour'
                elif ideal_interval_seconds <= 7200:
                    interval_seconds = 7200
                    interval = '2 hours'
                    trunc_unit = 'hour'
                elif ideal_interval_seconds <= 14400:
                    interval_seconds = 14400
                    interval = '4 hours'
                    trunc_unit = 'hour'
                elif ideal_interval_seconds <= 21600:
                    interval_seconds = 21600
                    interval = '6 hours'
                    trunc_unit = 'hour'
                elif ideal_interval_seconds <= 43200:
                    interval_seconds = 43200
                    interval = '12 hours'
                    trunc_unit = 'hour'
                else:
                    interval_seconds = 86400
                    interval = '1 day'
                    trunc_unit = 'day'
                
                # 重新计算实际点数
                actual_points = int(duration / interval_seconds) + 1
                logger.info(f"使用时间间隔: {interval_seconds}秒 ({interval}), 预计生成 {actual_points} 个时间点")
                
                # 构建筛选条件的WHERE子句
                filter_conditions = []
                filter_params = {}
                
                if filters:
                    for idx, filter_item in enumerate(filters):
                        # 跳过被禁用的筛选条件
                        if filter_item.get('enabled') == False:
                            continue
                            
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        if not field or not operator:
                            continue
                        
                        # 特殊处理空值判断
                        if operator in ['is_null', 'is_not_null']:
                            if operator == 'is_null':
                                filter_conditions.append(f"{field} IS NULL")
                            else:
                                filter_conditions.append(f"{field} IS NOT NULL")
                        # 处理IN和NOT IN操作符
                        elif operator in ['in', 'not_in']:
                            param_name = f'filter_{idx}_value'
                            if isinstance(value, list):
                                values_str = "', '".join(str(v) for v in value)
                                if operator == 'in':
                                    filter_conditions.append(f"{field} IN ('{values_str}')")
                                else:
                                    filter_conditions.append(f"{field} NOT IN ('{values_str}')")
                            else:
                                if operator == 'in':
                                    filter_conditions.append(f"{field} = :{param_name}")
                                else:
                                    filter_conditions.append(f"{field} != :{param_name}")
                                filter_params[param_name] = value
                        # 处理包含操作符
                        elif operator == 'contains':
                            param_name = f'filter_{idx}_value'
                            # 特殊处理JSON字段
                            if field in ['task_data', 'result']:
                                filter_conditions.append(f"{field}::text LIKE :{param_name}")
                            else:
                                filter_conditions.append(f"{field} LIKE :{param_name}")
                            filter_params[param_name] = f'%{value}%'
                        # 处理JSON相关操作符
                        elif operator == 'json_key_exists':
                            # 检查JSON中是否存在指定的键
                            if field in ['task_data', 'result']:
                                param_name = f'filter_{idx}_value'
                                filter_conditions.append(f"{field} ? :{param_name}")
                                filter_params[param_name] = value
                        elif operator == 'json_path_value':
                            # 使用JSON路径查询
                            if field in ['task_data', 'result'] and '=' in value:
                                import re
                                path, val = value.split('=', 1)
                                path = path.strip()
                                val = val.strip()
                                if path.startswith('$.'):
                                    path = path[2:]
                                path_parts = path.split('.')
                                # 验证路径安全性
                                if all(re.match(r'^[a-zA-Z0-9_]+$', part) for part in path_parts):
                                    param_name = f'filter_{idx}_value'
                                    if len(path_parts) == 1:
                                        filter_conditions.append(f"{field}->>'{path_parts[0]}' = :{param_name}")
                                    else:
                                        path_str = '{' + ','.join(path_parts) + '}'
                                        filter_conditions.append(f"{field}#>>'{path_str}' = :{param_name}")
                                    filter_params[param_name] = val.strip('"').strip("'")
                        elif operator == 'starts_with':
                            param_name = f'filter_{idx}_value'
                            filter_conditions.append(f"{field} LIKE :{param_name}")
                            filter_params[param_name] = f'{value}%'
                        elif operator == 'ends_with':
                            param_name = f'filter_{idx}_value'
                            filter_conditions.append(f"{field} LIKE :{param_name}")
                            filter_params[param_name] = f'%{value}'
                        # 处理标准比较操作符
                        else:
                            param_name = f'filter_{idx}_value'
                            op_map = {
                                'eq': '=',
                                'ne': '!=',
                                'gt': '>',
                                'lt': '<',
                                'gte': '>=',
                                'lte': '<='
                            }
                            sql_op = op_map.get(operator, '=')
                            filter_conditions.append(f"{field} {sql_op} :{param_name}")
                            filter_params[param_name] = value
                
                # 构建额外的WHERE条件
                extra_where = ""
                if filter_conditions:
                    extra_where = " AND " + " AND ".join(filter_conditions)
                
                # 优化的SQL查询 - 使用generate_series和CROSS JOIN生成完整的时间序列
                # 重要：时间桶对齐到固定边界，而不是基于start_time
                query = text(f"""
                    WITH time_series AS (
                        -- 生成对齐到固定边界的时间序列
                        -- 先计算对齐后的起始和结束时间
                        SELECT generate_series(
                            to_timestamp(FLOOR(EXTRACT(epoch FROM CAST(:start_time AS timestamptz)) / {interval_seconds}) * {interval_seconds}),
                            to_timestamp(CEILING(EXTRACT(epoch FROM CAST(:end_time AS timestamptz)) / {interval_seconds}) * {interval_seconds} + {interval_seconds}),
                            CAST(:interval AS interval)
                        ) AS time_bucket
                    ),
                    queue_list AS (
                        SELECT UNNEST(ARRAY['{queue_names_str}']) AS queue_name
                    ),
                    queue_data AS (
                        SELECT 
                            -- 对齐到固定的时间边界
                            -- 例如：5秒间隔会对齐到 00:00, 00:05, 00:10...
                            to_timestamp(
                                FLOOR(EXTRACT(epoch FROM created_at) / {interval_seconds}) * {interval_seconds}
                            ) AS time_bucket,
                            queue AS queue_name,
                            COUNT(*) as task_count
                        FROM tasks 
                        WHERE queue IN ('{queue_names_str}')
                            AND created_at >= :start_time 
                            AND created_at <= :end_time
                            {extra_where}
                        GROUP BY 1, 2
                    )
                    SELECT 
                        ts.time_bucket,
                        ql.queue_name,
                        COALESCE(qd.task_count, 0) as value
                    FROM time_series ts
                    CROSS JOIN queue_list ql
                    LEFT JOIN queue_data qd 
                        ON ts.time_bucket = qd.time_bucket 
                        AND ql.queue_name = qd.queue_name
                    ORDER BY ts.time_bucket, ql.queue_name
                """)
                
                # 合并参数
                query_params = {
                    'start_time': start_time,
                    'end_time': end_time,
                    'interval': interval
                }
                query_params.update(filter_params)
                
                result = await session.execute(query, query_params)
                
                # 直接转换结果为前端需要的格式
                timeline_data = []
                prev_time = None
                time_index = 0
                result_data = list(result)
                end_index = len(result_data) - 1
                for idx, row in enumerate(result_data):
                    time_str = row.time_bucket.isoformat()
                    
                    # 跟踪时间索引（用于决定是否将0值显示为None）
                    if prev_time != time_str:
                        time_index += 1
                        prev_time = time_str
                    
                    # 第一个时间点显示0，后续时间点如果是0则显示为None（用于图表美观）
                    value = row.value
                    if time_index > 1 and value == 0 and idx != end_index:
                        value = None
                    timeline_data.append({
                        'time': time_str,
                        'queue': row.queue_name,
                        'value': value
                    })
                
                logger.info(f"生成了 {len(timeline_data)} 个数据点")
                return timeline_data
                
        except Exception as e:
            logger.error(f"获取队列时间线数据失败: {e}")
            return []
    
    
    async def fetch_global_stats(self) -> Dict:
        """获取全局统计信息"""
        try:
            redis_client = await self.get_redis_client()
            
            # 获取所有队列的统计信息
            queues_data = await self.fetch_queues_data()
            
            total_pending = sum(q['待处理'] for q in queues_data)
            total_processing = sum(q['处理中'] for q in queues_data)
            total_completed = sum(q['已完成'] for q in queues_data)
            total_failed = sum(q['失败'] for q in queues_data)
            
            # 获取活跃worker数量
            worker_keys = await redis_client.keys(f"{self.redis_prefix}:worker:*")
            active_workers = len(worker_keys)
            
            await redis_client.close()
            
            return {
                'total_queues': len(queues_data),
                'total_pending': total_pending,
                'total_processing': total_processing,
                'total_completed': total_completed,
                'total_failed': total_failed,
                'active_workers': active_workers,
                'timestamp': datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"获取全局统计信息失败: {e}")
            return {}
    
    async def fetch_tasks_with_filters(self, 
                                      queue_name: str,
                                      page: int = 1,
                                      page_size: int = 20,
                                      filters: List[Dict] = None,
                                      start_time: Optional[datetime] = None,
                                      end_time: Optional[datetime] = None) -> Dict:
        """获取带灵活筛选条件的任务列表
        
        Args:
            queue_name: 队列名称
            page: 页码
            page_size: 每页大小
            filters: 筛选条件列表，每个条件包含:
                - field: 字段名 (task_id, status, worker_id, created_at, etc.)
                - operator: 操作符 (eq, ne, gt, lt, gte, lte, in, not_in, contains)
                - value: 比较值
        """
        try:
            if not self.AsyncSessionLocal:
                await self.initialize()
            
            async with self.AsyncSessionLocal() as session:
                # 构建基础查询
                query_parts = []
                params = {'queue_name': queue_name}
                
                # 基础条件
                query_parts.append("queue = :queue_name")
                
                # 添加时间范围筛选
                if start_time:
                    query_parts.append("created_at >= :start_time")
                    params['start_time'] = start_time
                if end_time:
                    query_parts.append("created_at <= :end_time")
                    params['end_time'] = end_time
                
                # 构建动态筛选条件
                if filters:
                    for idx, filter_item in enumerate(filters):
                        # 跳过被禁用的筛选条件
                        if filter_item.get('enabled') == False:
                            continue
                            
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        if not field or not operator or value is None:
                            continue
                        
                        param_name = f"filter_{idx}"
                        
                        # 根据操作符构建SQL条件
                        if operator == 'eq':
                            query_parts.append(f"{field} = :{param_name}")
                            params[param_name] = value
                        elif operator == 'ne':
                            query_parts.append(f"{field} != :{param_name}")
                            params[param_name] = value
                        elif operator == 'gt':
                            query_parts.append(f"{field} > :{param_name}")
                            params[param_name] = value
                        elif operator == 'lt':
                            query_parts.append(f"{field} < :{param_name}")
                            params[param_name] = value
                        elif operator == 'gte':
                            query_parts.append(f"{field} >= :{param_name}")
                            params[param_name] = value
                        elif operator == 'lte':
                            query_parts.append(f"{field} <= :{param_name}")
                            params[param_name] = value
                        elif operator == 'in':
                            # 处理IN操作符
                            if isinstance(value, str):
                                value = value.split(',')
                            in_params = []
                            for i, v in enumerate(value):
                                in_param_name = f"{param_name}_{i}"
                                in_params.append(f":{in_param_name}")
                                params[in_param_name] = v.strip() if isinstance(v, str) else v
                            query_parts.append(f"{field} IN ({','.join(in_params)})")
                        elif operator == 'not_in':
                            # 处理NOT IN操作符
                            if isinstance(value, str):
                                value = value.split(',')
                            not_in_params = []
                            for i, v in enumerate(value):
                                not_in_param_name = f"{param_name}_{i}"
                                not_in_params.append(f":{not_in_param_name}")
                                params[not_in_param_name] = v.strip() if isinstance(v, str) else v
                            query_parts.append(f"{field} NOT IN ({','.join(not_in_params)})")
                        elif operator == 'contains':
                            # 特殊处理JSON字段的搜索
                            if field in ['task_data', 'result']:
                                # 对JSON字段使用JSONB的文本搜索
                                query_parts.append(f"{field}::text LIKE :{param_name}")
                                params[param_name] = f"%{value}%"
                            else:
                                query_parts.append(f"{field} LIKE :{param_name}")
                                params[param_name] = f"%{value}%"
                        elif operator == 'json_key_exists':
                            # 检查JSON中是否存在指定的键
                            if field in ['task_data', 'result']:
                                query_parts.append(f"{field} ? :{param_name}")
                                params[param_name] = value
                        elif operator == 'json_key_value':
                            # 检查JSON中指定键的值
                            if field in ['task_data', 'result'] and '=' in value:
                                key, val = value.split('=', 1)
                                key = key.strip()
                                val = val.strip()
                                # 注意：PostgreSQL的 ->> 操作符的键名不能使用参数绑定，必须直接嵌入SQL
                                # 为了安全，对键名进行验证
                                import re
                                if not re.match(r'^[a-zA-Z0-9_]+$', key):
                                    continue  # 跳过无效的键名
                                
                                # 尝试解析值的类型
                                if val.lower() in ['true', 'false']:
                                    # 布尔值
                                    query_parts.append(f"({field}->'{key}')::boolean = :{param_name}_val")
                                    params[f'{param_name}_val'] = val.lower() == 'true'
                                elif val.isdigit() or (val.startswith('-') and val[1:].isdigit()):
                                    # 整数
                                    query_parts.append(f"({field}->'{key}')::text = :{param_name}_val")
                                    params[f'{param_name}_val'] = val
                                else:
                                    # 字符串 - 使用 ->> 操作符获取文本值
                                    query_parts.append(f"{field}->>'{key}' = :{param_name}_val")
                                    params[f'{param_name}_val'] = val.strip('"').strip("'")
                        elif operator == 'json_path_value':
                            # 使用JSON路径查询
                            if field in ['task_data', 'result'] and '=' in value:
                                path, val = value.split('=', 1)
                                path = path.strip()
                                val = val.strip()
                                
                                # 处理路径格式
                                if path.startswith('$.'):
                                    path = path[2:]  # 移除 $.
                                path_parts = path.split('.')
                                
                                # 验证路径部分的安全性
                                import re
                                if not all(re.match(r'^[a-zA-Z0-9_]+$', part) for part in path_parts):
                                    continue  # 跳过无效的路径
                                
                                # 构建JSONB路径查询
                                if len(path_parts) == 1:
                                    # 单层路径，同json_key_value处理
                                    query_parts.append(f"{field}->>'{path_parts[0]}' = :{param_name}_val")
                                else:
                                    # 多层路径，使用 #>> 操作符
                                    path_str = '{' + ','.join(path_parts) + '}'
                                    query_parts.append(f"{field}#>>'{path_str}' = :{param_name}_val")
                                    
                                # 处理值
                                params[f'{param_name}_val'] = val.strip('"').strip("'")
                        elif operator == 'starts_with':
                            query_parts.append(f"{field} LIKE :{param_name}")
                            params[param_name] = f"{value}%"
                        elif operator == 'ends_with':
                            query_parts.append(f"{field} LIKE :{param_name}")
                            params[param_name] = f"%{value}"
                        elif operator == 'is_null':
                            query_parts.append(f"{field} IS NULL")
                        elif operator == 'is_not_null':
                            query_parts.append(f"{field} IS NOT NULL")
                
                # 构建WHERE子句
                where_clause = " AND ".join(query_parts)
                
                # 计算总数
                count_query = text(f"""
                    SELECT COUNT(*) as total
                    FROM tasks
                    WHERE {where_clause}
                """)
                
                count_result = await session.execute(count_query, params)
                total = count_result.scalar() or 0
                
                # 获取分页数据（默认不包含task_data、result和error_message以提高性能）
                offset = (page - 1) * page_size
                data_query = text(f"""
                    SELECT 
                        id,
                        queue AS queue_name,
                        task_name,
                        status,
                        worker_id,
                        created_at,
                        started_at,
                        completed_at,
                        retry_count,
                        priority,
                        max_retry,
                        metadata,
                        duration,
                        EXTRACT(epoch FROM (
                            CASE 
                                WHEN completed_at IS NOT NULL THEN completed_at - started_at
                                WHEN started_at IS NOT NULL THEN NOW() - started_at
                                ELSE NULL
                            END
                        )) as execution_time
                    FROM tasks
                    WHERE {where_clause}
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                params['limit'] = page_size
                params['offset'] = offset
                
                result = await session.execute(data_query, params)
                rows = result.fetchall()
                
                # 转换为字典格式
                tasks = []
                for row in rows:
                    tasks.append({
                        'id': row.id,
                        'queue_name': row.queue_name,
                        'task_name': row.task_name,
                        'status': row.status,
                        'worker_id': row.worker_id,
                        'created_at': row.created_at.isoformat() if row.created_at else None,
                        'started_at': row.started_at.isoformat() if row.started_at else None,
                        'completed_at': row.completed_at.isoformat() if row.completed_at else None,
                        'execution_time': round(row.execution_time, 5) if row.execution_time else None,
                        'duration': round(row.duration, 5) if row.duration else None,
                        'retry_count': row.retry_count,
                        'priority': row.priority,
                        'max_retry': row.max_retry
                    })
                
                return {
                    'success': True,
                    'data': tasks,
                    'total': total,
                    'page': page,
                    'page_size': page_size
                }
                
        except Exception as e:
            logger.error(f"获取任务列表失败: {e}")
            import traceback
            traceback.print_exc()
            return {
                'success': False,
                'data': [],
                'total': 0,
                'page': page,
                'page_size': page_size,
                'error': str(e)
            }
    
    # ============= 定时任务相关方法 =============
    
    async def get_scheduled_tasks_statistics(self, session, namespace):
        """获取定时任务统计数据"""
        try:
            from datetime import datetime, timezone, timedelta
            
            # 获取今天的开始时间（UTC）
            today_start = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            
            # 查询统计数据
            # 今日执行次数：统计今天所有定时任务触发生成的tasks记录数
            # 成功率：统计今天成功完成的任务占总执行任务的百分比
            query = text("""
                WITH stats AS (
                    SELECT 
                        COUNT(*) as total,
                        COUNT(CASE WHEN enabled = true THEN 1 END) as active
                    FROM scheduled_tasks
                    WHERE namespace = :namespace
                ),
                today_tasks AS (
                    SELECT 
                        COUNT(DISTINCT t.stream_id) as today_count,
                        COUNT(DISTINCT CASE WHEN tr.status = 'success' THEN t.stream_id END) as success_count
                    FROM tasks t
                    LEFT JOIN task_runs tr ON t.stream_id = tr.stream_id
                    WHERE t.created_at >= :today_start
                        AND t.scheduled_task_id IS NOT NULL
                        AND t.namespace = :namespace
                )
                SELECT 
                    stats.total,
                    stats.active,
                    COALESCE(today_tasks.today_count, 0) as today_executions,
                    CASE 
                        WHEN today_tasks.today_count > 0
                        THEN ROUND(today_tasks.success_count::numeric * 100.0 / today_tasks.today_count::numeric, 1)
                        ELSE 0
                    END as success_rate
                FROM stats, today_tasks
            """)
            
            result = await session.execute(query, {
                'today_start': today_start,
                'namespace': namespace
            })
            row = result.first()
            
            if row:
                return {
                    'total': row.total or 0,
                    'active': row.active or 0,
                    'todayExecutions': int(row.today_executions or 0),
                    'successRate': float(row.success_rate or 0)
                }
            
            return {
                'total': 0,
                'active': 0,
                'todayExecutions': 0,
                'successRate': 0
            }
            
        except Exception as e:
            logger.error(f"获取定时任务统计失败: {e}")
            raise
    
    async def fetch_scheduled_tasks(self, 
                                   session,
                                   page: int = 1,
                                   page_size: int = 20,
                                   search: Optional[str] = None,
                                   is_active: Optional[bool] = None,
                                   filters: Optional[List[Dict]] = None,
                                   time_range: Optional[str] = None,
                                   start_time: Optional[str] = None,
                                   end_time: Optional[str] = None) -> tuple:
        """获取定时任务列表"""
        try:
                # 构建查询条件
                where_conditions = []
                params = {}
                
                if search:
                    where_conditions.append("(task_name ILIKE :search OR description ILIKE :search)")
                    params['search'] = f"%{search}%"
                
                if is_active is not None:
                    where_conditions.append("enabled = :is_active")
                    params['is_active'] = is_active
                
                # 处理时间范围筛选 - 针对下次执行时间
                if time_range or (start_time and end_time):
                    from datetime import datetime, timedelta
                    import dateutil.parser
                    import pytz
                    
                    if start_time and end_time:
                        # 使用自定义时间范围
                        params['start_time'] = dateutil.parser.parse(start_time)
                        params['end_time'] = dateutil.parser.parse(end_time)
                    else:
                        # 根据预设时间范围计算
                        # 使用UTC时间，因为数据库中的next_run_time是UTC时区
                        now = datetime.now(pytz.UTC)
                        time_ranges = {
                            '1h': timedelta(hours=1),
                            '6h': timedelta(hours=6),
                            '24h': timedelta(hours=24),
                            '7d': timedelta(days=7),
                            '30d': timedelta(days=30)
                        }
                        delta = time_ranges.get(time_range, timedelta(hours=24))
                        # 从现在开始到未来的时间范围
                        params['start_time'] = now
                        params['end_time'] = now + delta
                    
                    # 筛选下次执行时间在指定范围内的任务
                    where_conditions.append("next_run_time IS NOT NULL AND next_run_time BETWEEN :start_time AND :end_time")
                
                # 处理高级筛选条件
                if filters:
                    for idx, filter_item in enumerate(filters):
                        if not filter_item.get('enabled', True):
                            continue
                            
                        field = filter_item.get('field')
                        operator = filter_item.get('operator')
                        value = filter_item.get('value')
                        
                        # 映射字段名
                        field_map = {
                            'id': 'id',
                            'scheduler_id': 'scheduler_id',
                            'name': 'task_name',
                            'queue_name': 'queue_name',
                            'schedule_type': 'task_type',
                            'is_active': 'enabled',
                            'description': 'description',
                            'last_run': 'last_run_time',
                            'next_run': 'next_run_time',
                            'created_at': 'created_at',
                            'task_data': 'task_kwargs',  # 任务参数存储在task_kwargs字段
                            'tags': 'tags',
                            'metadata': 'metadata',
                        }
                        
                        db_field = field_map.get(field, field)
                        
                        # 处理不同的操作符
                        if operator == 'is_null':
                            where_conditions.append(f"{db_field} IS NULL")
                        elif operator == 'is_not_null':
                            where_conditions.append(f"{db_field} IS NOT NULL")
                        elif operator in ['eq', 'ne', 'gt', 'lt', 'gte', 'lte']:
                            op_map = {
                                'eq': '=',
                                'ne': '!=',
                                'gt': '>',
                                'lt': '<',
                                'gte': '>=',
                                'lte': '<='
                            }
                            param_name = f'filter_{idx}_value'
                            where_conditions.append(f"{db_field} {op_map[operator]} :{param_name}")
                            params[param_name] = value
                        elif operator == 'contains':
                            param_name = f'filter_{idx}_value'
                            # 对于JSON字段，需要转换为文本进行搜索
                            if db_field in ['task_kwargs', 'tags', 'metadata']:
                                where_conditions.append(f"{db_field}::text ILIKE :{param_name}")
                            else:
                                where_conditions.append(f"{db_field} ILIKE :{param_name}")
                            params[param_name] = f'%{value}%'
                        elif operator == 'starts_with':
                            param_name = f'filter_{idx}_value'
                            where_conditions.append(f"{db_field} ILIKE :{param_name}")
                            params[param_name] = f'{value}%'
                        elif operator == 'ends_with':
                            param_name = f'filter_{idx}_value'
                            where_conditions.append(f"{db_field} ILIKE :{param_name}")
                            params[param_name] = f'%{value}'
                        elif operator in ['in', 'not_in']:
                            if isinstance(value, list):
                                placeholders = []
                                for i, v in enumerate(value):
                                    param_name = f'filter_{idx}_value_{i}'
                                    placeholders.append(f':{param_name}')
                                    params[param_name] = v
                                op = 'IN' if operator == 'in' else 'NOT IN'
                                where_conditions.append(f"{db_field} {op} ({','.join(placeholders)})")
                        elif operator == 'json_key_exists' and db_field in ['task_kwargs', 'tags', 'metadata']:
                            # JSON字段键存在检查
                            param_name = f'filter_{idx}_value'
                            where_conditions.append(f"{db_field}::jsonb ? :{param_name}")
                            params[param_name] = value
                        elif operator == 'json_path_value' and db_field in ['task_kwargs', 'tags', 'metadata']:
                            # JSON路径值匹配 - 使用更简单的路径操作符
                            if '=' in value:
                                path, val = value.split('=', 1)
                                path = path.strip()
                                val = val.strip().strip('"').strip("'")
                                
                                # 处理JSON路径
                                if path.startswith('$.'):
                                    path = path[2:]  # 移除 $.
                                
                                # 特殊处理task_kwargs字段：
                                # 前端显示的是task_data.kwargs.xxx，但数据库中task_kwargs直接存储的就是kwargs的内容
                                # 所以需要移除kwargs.前缀
                                if db_field == 'task_kwargs':
                                    if path.startswith('kwargs.'):
                                        path = path[7:]  # 移除 'kwargs.' 前缀
                                    elif path.startswith('args.'):
                                        # args存储在task_args字段，这里不处理
                                        continue
                                
                                # 分割路径
                                path_parts = path.split('.')
                                param_name = f'filter_{idx}_value'
                                
                                if len(path_parts) == 1:
                                    # 单层路径：使用 ->> 操作符
                                    where_conditions.append(f"{db_field}::jsonb->>'{path_parts[0]}' = :{param_name}")
                                else:
                                    # 多层路径：使用 #>> 操作符
                                    path_str = '{' + ','.join(path_parts) + '}'
                                    where_conditions.append(f"{db_field}::jsonb#>>'{path_str}' = :{param_name}")
                                
                                params[param_name] = val
                
                where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
                
                # 计算总数
                count_query = text(f"""
                    SELECT COUNT(*) as total
                    FROM scheduled_tasks
                    WHERE {where_clause}
                """)
                print(f'{count_query.text=}')
                count_result = await session.execute(count_query, params)
                total = count_result.scalar() or 0
                
                # 获取分页数据
                offset = (page - 1) * page_size
                data_query = text(f"""
                    SELECT 
                        id,
                        scheduler_id,
                        task_name as name,
                        queue_name,
                        task_type as schedule_type,
                        task_args,
                        task_kwargs,
                        cron_expression,
                        interval_seconds,
                        enabled as is_active,
                        description,
                        tags,
                        metadata,
                        last_run_time as last_run,
                        next_run_time as next_run,
                        created_at,
                        updated_at,
                        COALESCE(execution_count, 0) as execution_count
                    FROM scheduled_tasks
                    WHERE {where_clause}
                    ORDER BY created_at DESC, id ASC
                    LIMIT :limit OFFSET :offset
                """)
                params['limit'] = page_size
                params['offset'] = offset
                
                result = await session.execute(data_query, params)
                tasks = []
                for row in result:
                    task = dict(row._mapping)
                    
                    # 构建schedule_config字段
                    if task['schedule_type'] == 'cron':
                        task['schedule_config'] = {'cron_expression': task.get('cron_expression')}
                    elif task['schedule_type'] == 'interval':
                        task['schedule_config'] = {'seconds': float(task.get('interval_seconds', 0))}
                    else:
                        task['schedule_config'] = {}
                    
                    # 合并task_args和task_kwargs为task_data
                    task['task_data'] = {
                        'args': task.get('task_args', []),
                        'kwargs': task.get('task_kwargs', {})
                    }
                    
                    # 删除不需要的字段
                    task.pop('task_args', None)
                    task.pop('task_kwargs', None)
                    task.pop('cron_expression', None)
                    task.pop('interval_seconds', None)
                    task.pop('scheduler_id', None)
                    
                    # 转换时间字段为ISO格式字符串
                    for field in ['last_run', 'next_run', 'created_at', 'updated_at']:
                        if task.get(field):
                            task[field] = task[field].isoformat()
                    
                    tasks.append(task)
                
                return tasks, total
                
        except Exception as e:
            logger.error(f"获取定时任务列表失败: {e}")
            raise
    
    async def create_scheduled_task(self, session, task_data: Dict) -> Dict:
        """创建定时任务"""
        try:
                # 生成scheduler_id
                scheduler_id = f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}_{int(time.time() * 1000) % 100000}"
                
                # 处理schedule_config
                cron_expression = None
                interval_seconds = None
                if task_data['schedule_type'] == 'cron':
                    cron_expression = task_data['schedule_config'].get('cron_expression')
                elif task_data['schedule_type'] == 'interval':
                    interval_seconds = task_data['schedule_config'].get('seconds', 60)
                
                # 处理task_data -> task_args和task_kwargs
                task_args = task_data.get('task_data', {}).get('args', [])
                task_kwargs = task_data.get('task_data', {}).get('kwargs', {})
                
                insert_query = text("""
                    INSERT INTO scheduled_tasks (
                        scheduler_id, task_name, queue_name, task_type,
                        task_args, task_kwargs, cron_expression, interval_seconds,
                        enabled, description
                    ) VALUES (
                        :scheduler_id, :task_name, :queue_name, :task_type,
                        :task_args, :task_kwargs, :cron_expression, :interval_seconds,
                        :enabled, :description
                    )
                    RETURNING *
                """)
                
                params = {
                    'scheduler_id': scheduler_id,
                    'task_name': task_data['name'],
                    'queue_name': task_data['queue_name'],
                    'task_type': task_data['schedule_type'],
                    'task_args': json.dumps(task_args),
                    'task_kwargs': json.dumps(task_kwargs),
                    'cron_expression': cron_expression,
                    'interval_seconds': interval_seconds,
                    'enabled': task_data.get('is_active', True),
                    'description': task_data.get('description')
                }
                
                result = await session.execute(insert_query, params)
                await session.commit()
                
                created_task = dict(result.first()._mapping)
                
                # 转换为前端格式
                created_task['name'] = created_task.pop('task_name', '')
                created_task['is_active'] = created_task.pop('enabled', True)
                created_task['schedule_type'] = created_task.pop('task_type', '')
                
                # 构建schedule_config
                if created_task['schedule_type'] == 'cron':
                    created_task['schedule_config'] = {'cron_expression': created_task.get('cron_expression')}
                elif created_task['schedule_type'] == 'interval':
                    created_task['schedule_config'] = {'seconds': float(created_task.get('interval_seconds', 0))}
                else:
                    created_task['schedule_config'] = {}
                
                # 合并task_args和task_kwargs为task_data
                created_task['task_data'] = {
                    'args': created_task.get('task_args', []),
                    'kwargs': created_task.get('task_kwargs', {})
                }
                
                # 删除不需要的字段
                created_task.pop('task_args', None)
                created_task.pop('task_kwargs', None)
                created_task.pop('cron_expression', None)
                created_task.pop('interval_seconds', None)
                created_task.pop('scheduler_id', None)
                
                # 转换时间字段
                for field in ['last_run_time', 'next_run_time', 'created_at', 'updated_at']:
                    if created_task.get(field):
                        value = created_task.pop(field)
                        # 重命名字段
                        if field == 'last_run_time':
                            created_task['last_run'] = value.isoformat()
                        elif field == 'next_run_time':
                            created_task['next_run'] = value.isoformat()
                        else:
                            created_task[field] = value.isoformat()
                
                return created_task
                
        except Exception as e:
            logger.error(f"创建定时任务失败: {e}")
            raise
    
    async def update_scheduled_task(self, session, task_id: str, task_data: Dict) -> Dict:
        """更新定时任务"""
        try:
                # 处理schedule_config
                cron_expression = None
                interval_seconds = None
                if task_data['schedule_type'] == 'cron':
                    cron_expression = task_data['schedule_config'].get('cron_expression')
                elif task_data['schedule_type'] == 'interval':
                    interval_seconds = task_data['schedule_config'].get('seconds', 60)
                
                # 处理task_data -> task_args和task_kwargs
                task_args = task_data.get('task_data', {}).get('args', [])
                task_kwargs = task_data.get('task_data', {}).get('kwargs', {})
                
                update_query = text("""
                    UPDATE scheduled_tasks SET
                        task_name = :task_name,
                        queue_name = :queue_name,
                        task_type = :task_type,
                        task_args = :task_args,
                        task_kwargs = :task_kwargs,
                        cron_expression = :cron_expression,
                        interval_seconds = :interval_seconds,
                        enabled = :enabled,
                        description = :description,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    RETURNING *
                """)
                
                params = {
                    'id': task_id,
                    'task_name': task_data['name'],
                    'queue_name': task_data['queue_name'],
                    'task_type': task_data['schedule_type'],
                    'task_args': json.dumps(task_args),
                    'task_kwargs': json.dumps(task_kwargs),
                    'cron_expression': cron_expression,
                    'interval_seconds': interval_seconds,
                    'enabled': task_data.get('is_active', True),
                    'description': task_data.get('description')
                }
                
                result = await session.execute(update_query, params)
                await session.commit()
                
                if result.rowcount == 0:
                    return {
                        'success': False,
                        'error': '任务不存在'
                    }
                
                updated_task = dict(result.first()._mapping)
                # 转换时间字段
                for field in ['last_run', 'next_run', 'created_at', 'updated_at']:
                    if updated_task.get(field):
                        updated_task[field] = updated_task[field].isoformat()
                
                return {
                    'success': True,
                    'data': updated_task,
                    'message': '定时任务更新成功'
                }
                
        except Exception as e:
            logger.error(f"更新定时任务失败: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def delete_scheduled_task(self, session, task_id: str) -> bool:
        """删除定时任务"""
        try:
                delete_query = text("""
                    DELETE FROM scheduled_tasks
                    WHERE id = :id
                """)
                
                result = await session.execute(delete_query, {'id': task_id})
                await session.commit()
                
                return result.rowcount > 0
                
        except Exception as e:
            logger.error(f"删除定时任务失败: {e}")
            raise
    
    async def _sync_task_to_redis(self, task_id: str, enabled: bool):
        """同步任务状态到 Redis"""
        try:
            if not self._redis_connector:
                logger.debug("Redis not configured, skipping sync")
                return
                
            redis_client = await self.get_redis_client()
            
            # Redis 中的键名格式（与 scheduler 保持一致）
            # scheduler 使用的前缀格式是 {redis_prefix}:SCHEDULER
            scheduler_prefix = f"{self.redis_prefix}:SCHEDULER"
            zset_key = f"{scheduler_prefix}:tasks"
            task_detail_key = f"{scheduler_prefix}:task:{task_id}"
            
            if enabled:
                # 如果启用，需要重新加载任务到 Redis
                # 获取任务完整信息并转换为 ScheduledTask 对象
                async with self.AsyncSessionLocal() as session:
                    query = text("""
                        SELECT * FROM scheduled_tasks 
                        WHERE id = :id AND next_run_time IS NOT NULL
                    """)
                    result = await session.execute(query, {'id': task_id})
                    task_row = result.first()
                    
                    if task_row and task_row.next_run_time:
                        # 导入必要的类
                        from jettask.scheduler.models import ScheduledTask, TaskType
                        from decimal import Decimal
                        
                        # 处理 interval_seconds 的 Decimal 类型
                        interval_seconds = task_row.interval_seconds
                        if interval_seconds is not None and isinstance(interval_seconds, Decimal):
                            interval_seconds = float(interval_seconds)
                        
                        # 创建 ScheduledTask 对象
                        task = ScheduledTask(
                            id=task_row.id,
                            scheduler_id=task_row.scheduler_id,
                            task_name=task_row.task_name,
                            task_type=TaskType(task_row.task_type) if task_row.task_type else TaskType.INTERVAL,
                            queue_name=task_row.queue_name,
                            task_args=task_row.task_args if isinstance(task_row.task_args, list) else json.loads(task_row.task_args or '[]'),
                            task_kwargs=task_row.task_kwargs if isinstance(task_row.task_kwargs, dict) else json.loads(task_row.task_kwargs or '{}'),
                            cron_expression=task_row.cron_expression,
                            interval_seconds=interval_seconds,
                            next_run_time=task_row.next_run_time,
                            last_run_time=task_row.last_run_time,
                            enabled=task_row.enabled,
                            max_retries=task_row.max_retries or 3,
                            retry_delay=task_row.retry_delay or 60,
                            timeout=task_row.timeout or 300,
                            description=task_row.description,
                            tags=task_row.tags if isinstance(task_row.tags, list) else (json.loads(task_row.tags) if task_row.tags else []),
                            metadata=task_row.metadata if isinstance(task_row.metadata, dict) else (json.loads(task_row.metadata) if task_row.metadata else None),
                            created_at=task_row.created_at,
                            updated_at=task_row.updated_at
                        )
                        
                        # 添加到 ZSET（用于调度）
                        score = task.next_run_time.timestamp()
                        await redis_client.zadd(zset_key, {str(task_id): score})
                        
                        # 存储任务详情（使用 ScheduledTask 的 to_redis_value 方法）
                        await redis_client.setex(
                            task_detail_key,
                            300,  # 5分钟过期
                            task.to_redis_value()
                        )
                        logger.info(f"Task {task_id} re-enabled and synced to Redis")
            else:
                # 如果禁用，从 Redis 中移除
                await redis_client.zrem(zset_key, str(task_id))
                await redis_client.delete(task_detail_key)
                logger.info(f"Task {task_id} disabled and removed from Redis")
                
            await redis_client.close()
            
        except Exception as e:
            # Redis 同步失败不应影响主要操作
            logger.warning(f"Failed to sync task {task_id} to Redis: {e}")
    
    async def toggle_scheduled_task(self, session, task_id: str) -> Dict:
        """切换定时任务状态"""
        try:
                # 先获取当前状态
                get_query = text("SELECT enabled FROM scheduled_tasks WHERE id = :id")
                result = await session.execute(get_query, {'id': task_id})
                row = result.first()
                
                if not row:
                    return None
                print(f'{row.enabled=}')
                # 切换状态
                new_status = not row.enabled
                update_query = text("""
                    UPDATE scheduled_tasks 
                    SET enabled = :enabled, updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    RETURNING id, enabled
                """)
                
                result = await session.execute(update_query, {
                    'id': task_id,
                    'enabled': new_status
                })
                await session.commit()
                
                updated_task = dict(result.first()._mapping)
                
                # 立即同步到 Redis
                await self._sync_task_to_redis(task_id, new_status)
                
                return updated_task
                
        except Exception as e:
            logger.error(f"切换定时任务状态失败: {e}")
            raise
    
    async def get_scheduled_task_by_id(self, session, task_id: str) -> Optional[Dict]:
        """根据ID获取定时任务详情"""
        try:
            query = text("""
                SELECT 
                    id,
                    scheduler_id,
                    task_name,
                    queue_name,
                    task_type,
                    interval_seconds,
                    cron_expression,
                    next_run_time,
                    last_run_time,
                    enabled,
                    task_args,
                    task_kwargs,
                    description,
                    max_retries,
                    retry_delay,
                    timeout,
                    created_at,
                    updated_at
                FROM scheduled_tasks
                WHERE id = :task_id
                LIMIT 1
            """)
            
            result = await session.execute(query, {"task_id": int(task_id)})
            row = result.first()
            
            if row:
                task = dict(row._mapping)
                # 处理JSON字段
                if task.get('task_args') and isinstance(task['task_args'], str):
                    import json
                    try:
                        task['task_args'] = json.loads(task['task_args'])
                    except:
                        task['task_args'] = []
                        
                if task.get('task_kwargs') and isinstance(task['task_kwargs'], str):
                    import json
                    try:
                        task['task_kwargs'] = json.loads(task['task_kwargs'])
                    except:
                        task['task_kwargs'] = {}
                        
                return task
            return None
            
        except Exception as e:
            logger.error(f"获取定时任务详情失败: {e}")
            raise
    
    async def fetch_task_execution_history(self, 
                                          session,
                                          task_id: str,
                                          page: int = 1,
                                          page_size: int = 20) -> tuple:
        """获取定时任务执行历史"""
        try:
                # 计算总数
                count_query = text("""
                    SELECT COUNT(*) as total
                    FROM tasks
                    WHERE scheduled_task_id = :task_id
                """)
                count_result = await session.execute(count_query, {'task_id': task_id})
                total = count_result.scalar() or 0
                
                # 获取分页数据
                offset = (page - 1) * page_size
                data_query = text("""
                    SELECT 
                        id,
                        scheduled_task_id as task_id,
                        status,
                        created_at as scheduled_time,
                        started_at,
                        completed_at as finished_at,
                        error_message,
                        result as task_result,
                        retry_count,
                        execution_time,
                        worker_id
                    FROM tasks
                    WHERE scheduled_task_id = :task_id
                    ORDER BY created_at DESC
                    LIMIT :limit OFFSET :offset
                """)
                
                result = await session.execute(data_query, {
                    'task_id': task_id,
                    'limit': page_size,
                    'offset': offset
                })
                
                history = []
                for row in result:
                    record = dict(row._mapping)
                    # 转换时间字段
                    for field in ['scheduled_time', 'started_at', 'finished_at']:
                        if record.get(field):
                            record[field] = record[field].isoformat()
                    # 计算执行时长（毫秒）
                    if record.get('execution_time'):
                        record['duration_ms'] = int(record['execution_time'] * 1000)
                    history.append(record)
                
                return history, total
                
        except Exception as e:
            logger.error(f"获取任务执行历史失败: {e}")
            raise
    
    async def fetch_task_execution_trend(self, 
                                        session,
                                        task_id: str,
                                        time_range: str = '7d') -> list:
        """获取定时任务执行趋势"""
        try:
                # 根据时间范围计算开始时间
                now = datetime.now(timezone.utc)
                if time_range == '24h':
                    start_time = now - timedelta(hours=24)
                    interval = 'hour'
                elif time_range == '7d':
                    start_time = now - timedelta(days=7)
                    interval = 'day'
                elif time_range == '30d':
                    start_time = now - timedelta(days=30)
                    interval = 'day'
                else:
                    start_time = now - timedelta(days=7)
                    interval = 'day'
                
                # 查询执行趋势（从tasks表）
                trend_query = text(f"""
                    SELECT 
                        date_trunc(:interval, COALESCE(started_at, created_at)) as time,
                        COUNT(*) as total,
                        COUNT(CASE WHEN status = 'success' THEN 1 END) as success,
                        COUNT(CASE WHEN status = 'error' THEN 1 END) as error
                    FROM tasks
                    WHERE scheduled_task_id = :task_id
                        AND COALESCE(started_at, created_at) >= :start_time
                    GROUP BY date_trunc(:interval, COALESCE(started_at, created_at))
                    ORDER BY time ASC
                """)
                
                result = await session.execute(trend_query, {
                    'task_id': task_id,
                    'start_time': start_time,
                    'interval': interval
                })
                
                data = []
                for row in result:
                    record = dict(row._mapping)
                    record['time'] = record['time'].isoformat()
                    data.append(record)
                
                return data
                
        except Exception as e:
            logger.error(f"获取任务执行趋势失败: {e}")
            raise