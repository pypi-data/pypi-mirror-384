"""
Redis Stream积压监控模块
用于监控任务队列的积压情况
"""

import asyncio
import redis.asyncio as redis
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
import os

logger = logging.getLogger(__name__)


class StreamBacklogMonitor:
    """Stream积压监控器"""
    
    def __init__(self, redis_url: str = None, pg_url: str = None, redis_prefix: str = "JETTASK"):
        """
        初始化监控器
        
        Args:
            redis_url: Redis连接URL
            pg_url: PostgreSQL连接URL  
            redis_prefix: Redis键前缀
        """
        self.redis_url = redis_url or os.getenv('JETTASK_REDIS_URL', 'redis://localhost:6379/0')
        self.pg_url = pg_url or os.getenv('JETTASK_PG_URL', 'postgresql+asyncpg://jettask:123456@localhost:5432/jettask')
        self.redis_prefix = redis_prefix
        
        self.redis_client = None
        self.engine = None
        self.AsyncSessionLocal = None
        
    async def initialize(self):
        """初始化连接（使用统一的连接池管理）"""
        # 初始化Redis连接
        from jettask.utils.db_connector import get_async_redis_client

        self.redis_client = get_async_redis_client(
            redis_url=self.redis_url,
            decode_responses=True
        )

        # 初始化PostgreSQL连接
        self.engine = create_async_engine(self.pg_url, echo=False)
        self.AsyncSessionLocal = sessionmaker(self.engine, class_=AsyncSession, expire_on_commit=False)
        
    async def close(self):
        """关闭连接"""
        if self.redis_client:
            await self.redis_client.close()
        if self.engine:
            await self.engine.dispose()
    
    async def update_delivered_offset(self, stream_name: str, group_name: str, messages: List[Tuple]):
        """
        更新消费组的已投递offset
        
        Args:
            stream_name: Stream名称（队列名）
            group_name: 消费者组名
            messages: 消息列表
        """
        if not messages:
            return
            
        try:
            # 从消息中提取最大的offset
            max_offset = 0
            for _, msg_list in messages:
                for msg_id, msg_data in msg_list:
                    if b'offset' in msg_data:
                        offset = int(msg_data[b'offset'])
                        max_offset = max(max_offset, offset)
            
            if max_offset > 0:
                # 更新Redis中的last_delivered_offset
                key = f"{self.redis_prefix}:GROUP:{stream_name}:{group_name}:last_delivered_offset"
                
                # 使用Lua脚本确保只更新更大的值
                lua_script = """
                local current = redis.call('GET', KEYS[1])
                if not current or tonumber(ARGV[1]) > tonumber(current) then
                    redis.call('SET', KEYS[1], ARGV[1])
                end
                return redis.call('GET', KEYS[1])
                """
                
                await self.redis_client.eval(lua_script, 1, key, str(max_offset))
                logger.debug(f"Updated delivered offset for {stream_name}:{group_name} to {max_offset}")
                
        except Exception as e:
            logger.error(f"Failed to update delivered offset: {e}")
    
    async def update_acked_offset(self, stream_name: str, group_name: str, acked_messages: List):
        """
        更新消费组的已确认offset
        
        Args:
            stream_name: Stream名称
            group_name: 消费者组名
            acked_messages: 已确认的消息列表
        """
        if not acked_messages:
            return
            
        try:
            # 提取最大的已确认offset
            max_offset = 0
            for msg in acked_messages:
                if 'offset' in msg:
                    offset = int(msg['offset'])
                    max_offset = max(max_offset, offset)
            
            if max_offset > 0:
                # 更新Redis中的last_acked_offset
                key = f"{self.redis_prefix}:GROUP:{stream_name}:{group_name}:last_acked_offset"
                
                # 使用Lua脚本确保只更新更大的值
                lua_script = """
                local current = redis.call('GET', KEYS[1])
                if not current or tonumber(ARGV[1]) > tonumber(current) then
                    redis.call('SET', KEYS[1], ARGV[1])
                end
                return redis.call('GET', KEYS[1])
                """
                
                await self.redis_client.eval(lua_script, 1, key, str(max_offset))
                logger.debug(f"Updated acked offset for {stream_name}:{group_name} to {max_offset}")
                
        except Exception as e:
            logger.error(f"Failed to update acked offset: {e}")
    
    async def collect_metrics(self, namespace: str = "default", stream_names: List[str] = None) -> Dict:
        """
        采集指定stream的积压指标
        使用 TASK_OFFSETS 和 QUEUE_OFFSETS 进行精确计算
        
        Args:
            namespace: 命名空间
            stream_names: 要监控的stream列表，None表示监控所有
            
        Returns:
            采集的指标数据
        """
        metrics = {}
        
        try:
            # 获取所有队列的最新offset (QUEUE_OFFSETS)
            queue_offsets_key = f"{namespace}:QUEUE_OFFSETS"
            queue_offsets = await self.redis_client.hgetall(queue_offsets_key)
            
            # 获取所有任务组的消费offset (TASK_OFFSETS)
            task_offsets_key = f"{namespace}:TASK_OFFSETS"
            task_offsets = await self.redis_client.hgetall(task_offsets_key)
            
            # 如果没有指定stream，从QUEUE_OFFSETS中获取所有队列
            if not stream_names:
                stream_names = list(queue_offsets.keys())
            
            # 对每个stream采集指标
            for stream_name in stream_names:
                # 使用实际的Stream键格式
                stream_key = f"{self.redis_prefix.lower()}:QUEUE:{stream_name}"
                
                # 获取队列的最新offset
                last_published_offset = int(queue_offsets.get(stream_name, 0))
                
                # 获取stream信息
                try:
                    stream_info = await self.redis_client.xinfo_stream(stream_key)
                except:
                    # Stream可能不存在
                    continue
                
                # 获取所有消费者组信息
                try:
                    groups = await self.redis_client.xinfo_groups(stream_key)
                except:
                    groups = []
                
                stream_metrics = {
                    'namespace': namespace,
                    'stream_name': stream_name,
                    'last_published_offset': last_published_offset,
                    'groups': {}
                }
                
                # 对每个消费者组采集指标
                for group in groups:
                    group_name = group['name']
                    pending_count = group['pending']  # Redis Stream中的pending数量（已投递未ACK）

                    # 从TASK_OFFSETS获取该组的消费offset
                    # 从 group_name 中提取 task_name（最后一段）
                    task_name = group_name.split(':')[-1]
                    # 构建 field：队列名（含优先级）+ 任务名
                    # 例如：robust_bench2:8:benchmark_task
                    task_offset_key = f"{stream_name}:{task_name}"
                    last_acked_offset = int(task_offsets.get(task_offset_key, 0))
                    print(f'{task_offset_key=} {last_acked_offset=}')
                    # 计算各种积压指标
                    # 1. 总积压 = 队列最新offset - 消费组已确认的offset
                    total_backlog = max(0, last_published_offset - last_acked_offset)
                    
                    # 2. 未投递的积压 = 总积压 - pending数量
                    #    pending_count 是已经投递给消费者但还未ACK的消息数量
                    backlog_undelivered = max(0, total_backlog - pending_count)
                    
                    # 3. 已投递未确认 = pending数量（这是Redis Stream统计的）
                    backlog_delivered_unacked = pending_count
                    
                    # 4. 已投递的offset = 已确认offset + pending数量
                    last_delivered_offset = last_acked_offset + pending_count
                    
                    stream_metrics['groups'][group_name] = {
                        'last_delivered_offset': last_delivered_offset,  # 已投递的最新offset
                        'last_acked_offset': last_acked_offset,          # 已确认的最新offset
                        'pending_count': pending_count,                  # 已投递未确认的数量
                        'backlog_undelivered': backlog_undelivered,      # 未投递的积压
                        'backlog_delivered_unacked': backlog_delivered_unacked,  # 已投递未确认的积压
                        'backlog_unprocessed': total_backlog            # 总积压（未投递+已投递未确认）
                    }
                
                # 如果没有消费组但有队列offset，也记录
                if not stream_metrics['groups'] and last_published_offset > 0:
                    stream_metrics['groups']['_total'] = {
                        'last_delivered_offset': 0,
                        'last_acked_offset': 0,
                        'pending_count': 0,
                        'backlog_undelivered': last_published_offset,
                        'backlog_unprocessed': last_published_offset
                    }
                
                metrics[stream_name] = stream_metrics
                
        except Exception as e:
            logger.error(f"Failed to collect metrics: {e}")
            import traceback
            traceback.print_exc()
            
        return metrics
    
    async def save_metrics(self, metrics: Dict):
        """
        将采集的指标保存到数据库
        
        Args:
            metrics: 采集的指标数据
        """
        if not metrics:
            return
            
        try:
            async with self.AsyncSessionLocal() as session:
                # 准备插入数据
                records = []
                timestamp = datetime.now(timezone.utc)
                
                for stream_name, stream_data in metrics.items():
                    # 保存每个消费组的数据
                    for group_name, group_data in stream_data.get('groups', {}).items():
                        record = {
                            'namespace': stream_data['namespace'],
                            'stream_name': stream_name,
                            'consumer_group': group_name,
                            'last_published_offset': stream_data['last_published_offset'],
                            'last_delivered_offset': group_data['last_delivered_offset'],
                            'last_acked_offset': group_data['last_acked_offset'],
                            'pending_count': group_data['pending_count'],
                            'backlog_undelivered': group_data['backlog_undelivered'],
                            'backlog_unprocessed': group_data['backlog_unprocessed'],
                            'backlog_delivered_unacked': group_data.get('backlog_delivered_unacked', group_data['pending_count']),
                            'created_at': timestamp
                        }
                        records.append(record)
                    
                    # 如果没有消费组，也保存stream级别的数据
                    if not stream_data.get('groups'):
                        record = {
                            'namespace': stream_data['namespace'],
                            'stream_name': stream_name,
                            'consumer_group': None,
                            'last_published_offset': stream_data['last_published_offset'],
                            'last_delivered_offset': 0,
                            'last_acked_offset': 0,
                            'pending_count': 0,
                            'backlog_undelivered': stream_data['last_published_offset'],
                            'backlog_unprocessed': stream_data['last_published_offset'],
                            'created_at': timestamp
                        }
                        records.append(record)
                
                # 批量插入
                if records:
                    insert_sql = text("""
                        INSERT INTO stream_backlog_monitor 
                        (namespace, stream_name, consumer_group, last_published_offset, 
                         last_delivered_offset, last_acked_offset, pending_count,
                         backlog_undelivered, backlog_unprocessed, created_at)
                        VALUES 
                        (:namespace, :stream_name, :consumer_group, :last_published_offset,
                         :last_delivered_offset, :last_acked_offset, :pending_count,
                         :backlog_undelivered, :backlog_unprocessed, :created_at)
                    """)
                    # 注意：backlog_delivered_unacked 可以从 pending_count 推导，所以不单独存储
                    
                    await session.execute(insert_sql, records)
                    await session.commit()
                    logger.info(f"Saved {len(records)} monitoring records")
                    
        except Exception as e:
            logger.error(f"Failed to save metrics: {e}")
    
    async def run_collector(self, interval: int = 60):
        """
        运行采集器
        
        Args:
            interval: 采集间隔（秒）
        """
        await self.initialize()
        
        logger.info(f"Starting backlog monitor collector with {interval}s interval")
        
        try:
            while True:
                try:
                    # 采集指标
                    metrics = await self.collect_metrics()
                    
                    # 保存到数据库
                    await self.save_metrics(metrics)
                    
                    # 等待下一次采集
                    await asyncio.sleep(interval)
                    
                except Exception as e:
                    logger.error(f"Collector error: {e}")
                    await asyncio.sleep(interval)
                    
        except KeyboardInterrupt:
            logger.info("Stopping collector...")
        finally:
            await self.close()

# 辅助函数 - 供其他模块调用
async def report_delivered_offset(redis_client, redis_prefix: str, queue: str, group_name: str, messages: List):
    """
    上报已投递的offset（供event_pool调用）
    这个函数已弃用，改为直接更新TASK_OFFSETS
    """
    pass  # 现在offset更新在executor中完成

async def report_queue_offset(redis_client, redis_prefix: str, queue: str, offset: int):
    """
    上报队列的最新offset（供发送消息时调用）
    这个功能已经在发送时通过Lua脚本自动完成
    """
    pass  # 现在offset更新在发送时通过Lua脚本完成

if __name__ == "__main__":
    # 测试运行采集器
    monitor = StreamBacklogMonitor()
    asyncio.run(monitor.run_collector(interval=30))