"""
任务加载器 - 负责从数据库加载任务到Redis
"""
import asyncio
from redis import asyncio as aioredis
from typing import Optional, Set
from datetime import datetime, timedelta
import json

from ..utils.task_logger import get_task_logger, LogContext
from .task_crud import ScheduledTaskManager
from .models import ScheduledTask


logger = get_task_logger(__name__)


class TaskLoader:
    """
    任务加载器
    定期从数据库加载即将执行的任务到Redis ZSET
    """
    
    def __init__(
        self,
        redis_url: str,
        db_manager: ScheduledTaskManager,
        redis_prefix: str = "jettask:scheduled",
        lookahead_minutes: int = 5,
        load_interval: int = 30,
        sync_interval_cycles: int = 2  # 每几个周期同步一次
    ):
        """
        初始化加载器
        
        Args:
            redis_url: Redis连接URL
            db_manager: 数据库管理器
            redis_prefix: Redis键前缀
            lookahead_minutes: 向前查看的分钟数（加载未来N分钟的任务）
            load_interval: 加载间隔（秒）
            sync_interval_cycles: 每几个周期与数据库同步一次（默认2个周期=1分钟）
        """
        self.sync_interval_cycles = sync_interval_cycles
        self.redis_url = redis_url
        self.db_manager = db_manager
        self.redis_prefix = redis_prefix
        self.lookahead_minutes = lookahead_minutes
        self.load_interval = load_interval
        
        self.redis: Optional[aioredis.Redis] = None
        self.running = False
        self.loaded_tasks: Set[str] = set()  # 已加载的任务ID
    
    async def connect(self):
        """建立Redis连接（使用统一的连接池管理）"""
        if not self.redis:
            from jettask.utils.db_connector import get_async_redis_client

            self.redis = get_async_redis_client(
                redis_url=self.redis_url,
                decode_responses=False
            )
    
    async def disconnect(self):
        """关闭Redis连接"""
        if self.redis:
            await self.redis.close()
            self.redis = None
    
    def _get_zset_key(self) -> str:
        """获取ZSET键名"""
        return f"{self.redis_prefix}:tasks"
    
    def _get_task_detail_key(self, task_id: int) -> str:
        """获取任务详情键名"""
        return f"{self.redis_prefix}:task:{task_id}"
    
    async def load_tasks(self) -> int:
        """
        从数据库加载任务到Redis
        
        Returns:
            加载的任务数量
        """
        with LogContext(operation="load_tasks"):
            try:
                # 获取即将执行的任务
                tasks = await self.db_manager.get_ready_tasks(
                    batch_size=1000,
                    lookahead_seconds=self.lookahead_minutes * 60
                )
                
                if not tasks:
                    logger.debug("No tasks to load")
                    return 0
                
                # 批量添加到Redis
                pipe = self.redis.pipeline()
                loaded_count = 0
                
                for task in tasks:
                    if not task.enabled or not task.next_run_time:
                        continue
                    
                    task_id = task.id
                    score = task.next_run_time.timestamp()
                    
                    # 添加到ZSET（用于调度）
                    pipe.zadd(self._get_zset_key(), {str(task_id): score})  # Redis ZSET 需要字符串键
                    
                    # 存储任务详情
                    pipe.setex(
                        self._get_task_detail_key(task_id),
                        self.lookahead_minutes * 60 + 60,  # 过期时间比lookahead稍长
                        task.to_redis_value()
                    )
                    
                    self.loaded_tasks.add(task_id)
                    loaded_count += 1
                
                await pipe.execute()
                
                logger.info(f"Loaded {loaded_count} tasks to Redis", 
                           extra={'extra_fields': {'task_count': loaded_count}})
                
                return loaded_count
                
            except Exception as e:
                logger.error(f"Failed to load tasks: {e}", exc_info=True)
                raise
    
    async def remove_task(self, task_id: int):
        """
        从Redis中移除任务
        
        Args:
            task_id: 任务ID
        """
        pipe = self.redis.pipeline()
        pipe.zrem(self._get_zset_key(), str(task_id))
        pipe.delete(self._get_task_detail_key(task_id))
        await pipe.execute()
        
        self.loaded_tasks.discard(task_id)
        
        logger.info(f"Removed task {task_id} from Redis")
    
    async def update_task_score(self, task_id: int, next_run_time: datetime):
        """
        更新任务在ZSET中的分数（下次执行时间）
        
        Args:
            task_id: 任务ID
            next_run_time: 下次执行时间
        """
        score = next_run_time.timestamp()
        await self.redis.zadd(self._get_zset_key(), {str(task_id): score})
        
        logger.debug(f"Updated task {task_id} score to {score}")
    
    async def cleanup_expired(self):
        """清理过期的任务"""
        # 移除已过期很久的任务（比如1小时前的）
        cutoff_time = datetime.now() - timedelta(hours=1)
        cutoff_score = cutoff_time.timestamp()
        
        removed = await self.redis.zremrangebyscore(
            self._get_zset_key(),
            '-inf',
            cutoff_score
        )
        
        if removed:
            logger.info(f"Cleaned up {removed} expired tasks from Redis")
    
    async def sync_with_db(self):
        """
        与数据库同步任务状态
        检查Redis中的任务是否仍然有效
        """
        # 获取Redis中所有任务ID
        redis_tasks = await self.redis.zrange(self._get_zset_key(), 0, -1)
        redis_task_ids = {int(task_id.decode() if isinstance(task_id, bytes) else task_id) 
                         for task_id in redis_tasks}  # 转换为整数
        
        # 批量检查这些任务在数据库中的状态
        for task_id in redis_task_ids:
            db_task = await self.db_manager.get_task(task_id)  # task_id 现在是整数
            
            if not db_task or not db_task.enabled:
                # 任务已删除或禁用，从Redis移除
                await self.remove_task(task_id)
            elif db_task.next_run_time:
                # 更新执行时间
                await self.update_task_score(task_id, db_task.next_run_time)
    
    async def run(self):
        """运行加载器主循环"""
        self.running = True
        logger.info("Task loader started")
        
        # 主循环
        cycle_count = 0
        first_run = True
        
        while self.running:
            try:
                # 确定本次循环的类型
                if first_run:
                    cycle_type = "initial_load"
                    logger.info("Performing initial task load...")
                else:
                    cycle_type = "load"
                
                with LogContext(cycle=cycle_type):
                    # 加载任务
                    await self.load_tasks()
                    
                    # 初始加载时执行同步
                    if first_run:
                        await self.sync_with_db()
                        first_run = False
                    else:
                        cycle_count += 1
                        
                        # 每2个周期同步一次数据库（默认1分钟）
                        if cycle_count % self.sync_interval_cycles == 0:
                            await self.sync_with_db()
                        
                        # 每5个周期清理一次过期任务
                        if cycle_count % 5 == 0:
                            await self.cleanup_expired()
                        
                        # 重置计数器，避免溢出
                        if cycle_count >= 100:
                            cycle_count = 0
                
            except Exception as e:
                logger.error(f"Loader cycle error: {e}", exc_info=True)
            
            # 等待间隔（放在循环末尾）
            if self.running:  # 只有在继续运行时才等待
                await asyncio.sleep(self.load_interval)
        
        logger.info("Task loader stopped")
    
    def stop(self):
        """停止加载器"""
        self.running = False