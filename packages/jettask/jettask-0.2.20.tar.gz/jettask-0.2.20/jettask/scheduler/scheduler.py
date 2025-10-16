"""
定时任务调度器 - 负责从Redis获取任务并触发执行
"""
import asyncio
import time
from redis import asyncio as aioredis
from redis.asyncio.lock import Lock as AsyncLock
import uuid
from typing import Optional, List, TYPE_CHECKING
from datetime import datetime

from ..utils.task_logger import get_task_logger, LogContext
from .task_crud import ScheduledTaskManager
from .models import ScheduledTask, TaskExecutionHistory, TaskType, TaskStatus as ScheduledTaskStatus
from .loader import TaskLoader

# 类型注解导入（避免循环导入）
if TYPE_CHECKING:
    from ..core.app import Jettask


logger = get_task_logger(__name__)


class TaskScheduler:
    """
    任务调度器
    从Redis ZSET中获取到期任务并投递到执行队列
    """
    
    def __init__(
        self,
        app: 'Jettask',  # Jettask实例
        db_manager: ScheduledTaskManager,
        scan_interval: float = 0.1,
        batch_size: int = 100,
        leader_ttl: int = 30
    ):
        """
        初始化调度器
        
        Args:
            app: Jettask应用实例（包含redis_url和redis_prefix）
            db_manager: 数据库管理器
            scan_interval: 扫描间隔（秒）
            batch_size: 每批处理的任务数
            leader_ttl: Leader锁的TTL（秒）
        """
        self.app: 'Jettask' = app
        # 从app获取Redis配置
        self.redis_url = app.redis_url
        self.redis_prefix = f"{app.redis_prefix}:scheduled"  # 使用app的前缀加上scheduled命名空间
        self.db_manager = db_manager
        self.scan_interval = scan_interval
        self.batch_size = batch_size
        self.leader_ttl = leader_ttl
        
        self.redis: Optional[aioredis.Redis] = None
        self.scheduler_id = f"scheduler-{uuid.uuid4().hex[:8]}"
        self.running = False
        self.is_leader = False
        self.leader_lock: Optional[AsyncLock] = None
        
        # 任务加载器
        self.loader = TaskLoader(
            redis_url=self.redis_url,
            db_manager=db_manager,
            redis_prefix=self.redis_prefix,
            sync_interval_cycles=2  # 每2个周期同步一次（约1分钟）
        )
    
    
    def _get_zset_key(self) -> str:
        """获取ZSET键名"""
        return f"{self.redis_prefix}:tasks"
    
    def _get_task_detail_key(self, task_id: int) -> str:
        """获取任务详情键名"""
        return f"{self.redis_prefix}:task:{task_id}"
    
    def _get_leader_key(self) -> str:
        """获取Leader锁键名"""
        return f"{self.redis_prefix}:leader"
    
    def _get_processing_key(self, task_id: int) -> str:
        """获取任务处理中标记键名"""
        return f"{self.redis_prefix}:processing:{task_id}"
    
    async def acquire_leader(self) -> bool:
        """
        尝试获取Leader锁（使用redis-py的AsyncLock）
        
        Returns:
            是否成功获取Leader
        """
        # 如果已经持有锁，检查是否仍然有效
        if self.is_leader and self.leader_lock:
            try:
                # AsyncLock的owned()方法检查是否仍然拥有锁
                if await self.leader_lock.owned():
                    return True
                else:
                    # 锁已经失效
                    self.is_leader = False
                    self.leader_lock = None
            except Exception as e:
                logger.warning(f"Error checking leader lock: {e}")
                self.is_leader = False
                self.leader_lock = None
        
        # 创建或获取锁对象
        if not self.leader_lock:
            self.leader_lock = AsyncLock(
                self.redis,
                self._get_leader_key(),
                timeout=self.leader_ttl,  # 锁的超时时间
                sleep=0.1,  # 重试间隔
                blocking=False,  # 非阻塞模式
                blocking_timeout=None,  # 不等待
                thread_local=False  # 不使用线程本地存储
            )
        
        # 尝试获取锁
        try:
            acquired = await self.leader_lock.acquire(blocking=False)
            if acquired:
                self.is_leader = True
                logger.info(f"Scheduler {self.scheduler_id} acquired leader lock")
                return True
            else:
                # 获取当前锁的信息用于调试
                lock_info = await self.redis.get(self._get_leader_key())
                if lock_info:
                    logger.debug(f"Leader lock is held by another instance, will retry")
                else:
                    logger.debug(f"Leader lock exists but no value, will retry")
                return False
                
        except Exception as e:
            logger.error(f"Error acquiring leader lock: {e}")
            return False
    
    async def renew_leader(self) -> bool:
        """
        续期Leader锁（使用AsyncLock的extend方法）
        
        Returns:
            是否成功续期
        """
        if not self.is_leader or not self.leader_lock:
            return False
        
        try:
            # 使用extend方法续期锁
            await self.leader_lock.extend(self.leader_ttl, replace_ttl=True)
            logger.debug(f"Scheduler {self.scheduler_id} renewed leader lock")
            return True
            
        except Exception as e:
            logger.error(f"Error renewing leader lock: {e}")
            self.is_leader = False
            self.leader_lock = None
            return False
    
    async def release_leader(self, force=False):
        """
        释放Leader锁（使用AsyncLock的release方法）
        
        Args:
            force: 是否强制删除锁（用于CTRL+C退出时）
        """
        if not self.leader_lock and not force:
            return
        
        try:
            # 如果是强制释放且当前是leader，直接删除Redis中的key
            if force and self.is_leader:
                leader_key = self._get_leader_key()
                deleted = await self.redis.delete(leader_key)
                if deleted:
                    logger.info(f"Scheduler {self.scheduler_id} forcefully deleted leader lock key")
                else:
                    logger.debug(f"Leader lock key was already deleted")
            elif self.leader_lock:
                # 正常释放流程：只有当我们拥有锁时才释放
                if await self.leader_lock.owned():
                    await self.leader_lock.release()
                    logger.info(f"Scheduler {self.scheduler_id} released leader lock")
                else:
                    logger.debug(f"Scheduler {self.scheduler_id} does not own the lock")
                    
        except Exception as e:
            logger.warning(f"Error releasing leader lock: {e}")
        finally:
            self.is_leader = False
            self.leader_lock = None
    
    async def get_due_tasks_with_details(self) -> List[tuple]:
        """
        获取到期的任务及其详情（使用Lua脚本原子操作）
        
        Returns:
            任务列表，每个元素为(task_id, score, task_detail_json)
        """
        now = datetime.now().timestamp()
        
        # Lua脚本：原子性地获取到期任务并获取其详情
        lua_script = """
        local zset_key = KEYS[1]
        local detail_prefix = KEYS[2]
        local now = ARGV[1]
        local batch_size = ARGV[2]
        
        -- 获取到期任务
        local due_tasks = redis.call('ZRANGEBYSCORE', zset_key, '-inf', now, 'WITHSCORES', 'LIMIT', 0, batch_size)
        
        if #due_tasks == 0 then
            return {}
        end
        
        local result = {}
        
        -- 遍历任务，获取详情
        for i = 1, #due_tasks, 2 do
            local task_id = due_tasks[i]
            local score = due_tasks[i + 1]
            
            -- 获取任务详情
            local detail_key = detail_prefix .. ':' .. task_id
            local task_detail = redis.call('GET', detail_key)
            
            -- 添加到结果集
            table.insert(result, {task_id, score, task_detail or ''})
        end
        
        return result
        """
        
        # 执行Lua脚本
        result = await self.redis.eval(
            lua_script,
            2,  # KEYS数量
            self._get_zset_key(),  # KEYS[1]
            f"{self.redis_prefix}:task",  # KEYS[2] - 任务详情前缀
            str(now),  # ARGV[1]
            str(self.batch_size)  # ARGV[2]
        )
        
        return result or []
    
    async def get_due_tasks(self) -> List[tuple]:
        """
        获取到期的任务（保留兼容性）
        
        Returns:
            任务ID和分数的列表
        """
        now = datetime.now().timestamp()
        
        # 使用ZRANGEBYSCORE获取到期任务
        tasks = await self.redis.zrangebyscore(
            self._get_zset_key(),
            min='-inf',
            max=now,
            withscores=True,
            start=0,
            num=self.batch_size
        )
        
        return tasks
    
    async def load_task_detail(self, task_id: int) -> Optional[ScheduledTask]:
        """
        加载任务详情
        
        Args:
            task_id: 任务ID
            
        Returns:
            任务对象
        """
        # 先从Redis获取
        task_data = await self.redis.get(self._get_task_detail_key(task_id))
        
        if task_data:
            try:
                task_str = task_data.decode() if isinstance(task_data, bytes) else task_data
                return ScheduledTask.from_redis_value(task_str)
            except Exception as e:
                logger.error(f"Failed to parse task from Redis: {e}")
        
        # Redis中没有，从数据库获取
        task = await self.db_manager.get_task(task_id)
        
        if task:
            # 缓存到Redis
            await self.redis.setex(
                self._get_task_detail_key(task_id),
                300,  # 5分钟过期
                task.to_redis_value()
            )
        
        return task
    
    async def trigger_task(self, task: ScheduledTask) -> str:
        """
        触发任务执行
        
        Args:
            task: 任务对象
            
        Returns:
            事件ID
        """
        with LogContext(task_id=task.id):
            try:
                # 直接使用新的发送方式，无需获取task对象
                from ..core.message import TaskMessage
                
                # 准备kwargs
                kwargs = task.task_kwargs or {}
                # 添加任务名称用于路由
                kwargs['__task_name'] = task.task_name
                kwargs['__scheduled_task_id'] = task.id
                
                # 创建TaskMessage
                # 将timeout、max_retries等参数放入kwargs中传递
                if task.timeout:
                    kwargs['__timeout'] = task.timeout
                if task.max_retries:
                    kwargs['__max_retries'] = task.max_retries
                if task.retry_delay:
                    kwargs['__retry_delay'] = task.retry_delay
                
                msg = TaskMessage(
                    queue=task.queue_name,
                    kwargs=kwargs,
                    priority=task.priority
                )
                
                # 发送任务
                event_ids = await self.app.send_tasks([msg])
                event_id = event_ids[0] if event_ids else None
                
                logger.info(f"Triggered task {task.id} with event_id {event_id}")
                
                # 记录执行历史
                history = TaskExecutionHistory(
                    task_id=task.id,
                    event_id=event_id,
                    scheduled_time=task.next_run_time or datetime.now(),
                    status=ScheduledTaskStatus.PENDING,
                    started_at=datetime.now()
                )
                await self.db_manager.record_execution(history)
                
                return event_id
                
            except Exception as e:
                logger.error(f"Failed to trigger task {task.id}: {e}", exc_info=True)
                
                # 记录失败
                history = TaskExecutionHistory(
                    task_id=task.id,
                    event_id=f"failed-{uuid.uuid4().hex[:8]}",
                    scheduled_time=task.next_run_time or datetime.now(),
                    status=ScheduledTaskStatus.FAILED,
                    error_message=str(e),
                    started_at=datetime.now(),
                    finished_at=datetime.now()
                )
                await self.db_manager.record_execution(history)
                
                raise
    
    async def process_task(self, task_id: int, score: float):
        """
        处理单个任务
        
        Args:
            task_id: 任务ID
            score: 任务分数（执行时间戳）
        """
        # 使用Redis原生锁避免重复处理
        processing_key = self._get_processing_key(task_id)
        processing_lock = AsyncLock(
            self.redis,
            processing_key,
            timeout=60,  # 60秒自动过期
            blocking=False  # 非阻塞
        )
        
        if not await processing_lock.acquire():
            # 任务正在被其他调度器处理
            return
        
        try:
            with LogContext(task_id=task_id, score=score):
                # 加载任务详情
                task = await self.load_task_detail(task_id)
                
                if not task:
                    logger.warning(f"Task {task_id} not found, removing from schedule")
                    await self.redis.zrem(self._get_zset_key(), str(task_id))
                    return
                
                if not task.enabled:
                    logger.info(f"Task {task_id} is disabled, removing from schedule")
                    await self.redis.zrem(self._get_zset_key(), str(task_id))
                    return
                
                # 触发任务
                await self.trigger_task(task)
                
                # 更新下次执行时间
                task.update_next_run_time()
                
                if task.next_run_time:
                    # 更新Redis中的分数
                    new_score = task.next_run_time.timestamp()
                    await self.redis.zadd(self._get_zset_key(), {str(task_id): new_score})
                    
                    # 更新数据库
                    await self.db_manager.update_task_next_run(
                        task_id=task.id,
                        next_run_time=task.next_run_time,
                        last_run_time=task.last_run_time
                    )
                    
                    logger.info(f"Rescheduled task {task_id} for {task.next_run_time}")
                else:
                    # 一次性任务或已完成，从调度中移除
                    await self.redis.zrem(self._get_zset_key(), str(task_id))
                    
                    # 对于一次性任务，禁用以防止被重新加载
                    if task.task_type == TaskType.ONCE or (isinstance(task.task_type, str) and task.task_type == 'once'):
                        # 只更新必要的字段，不覆盖用户设置的其他字段
                        await self.db_manager.disable_once_task(task.id)
                        logger.info(f"One-time task {task_id} completed and disabled")
                    else:
                        logger.info(f"Task {task_id} completed, removed from schedule")
                
        except Exception as e:
            logger.error(f"Failed to process task {task_id}: {e}", exc_info=True)
        finally:
            # 释放处理锁
            try:
                await processing_lock.release()
            except Exception:
                pass  # 锁可能已经过期
    
    async def batch_process_tasks_optimized(self, tasks_with_details: List[tuple]):
        """批量处理任务（优化版，任务详情已包含）"""
        if not tasks_with_details:
            return
        
        # 收集需要触发的任务消息
        bulk_tasks = []
        tasks_to_update = []
        tasks_to_remove = []
        
        for task_data in tasks_with_details:
            # 解析数据
            task_id_str = task_data[0].decode() if isinstance(task_data[0], bytes) else str(task_data[0])
            task_id = int(task_id_str)
            score = float(task_data[1])
            task_detail_json = task_data[2]
            
            # 解析任务详情
            task = None
            if task_detail_json:
                try:
                    task = ScheduledTask.from_redis_value(task_detail_json)
                except Exception as e:
                    logger.error(f"Failed to parse task {task_id} from Redis: {e}")
            
            # 如果Redis中没有详情，从数据库获取
            if not task:
                task = await self.db_manager.get_task(task_id)
                if not task:
                    # 任务不存在，从调度中移除
                    tasks_to_remove.append(str(task_id))
                    continue
            
            
            # 检查任务状态
            if not task.enabled:
                logger.info(f"Task {task_id} is disabled, skipping")
                tasks_to_remove.append(str(task_id))
                continue
            
            # 无需获取task对象，直接准备消息
            bulk_tasks.append(task)
            tasks_to_update.append(task)
        
        # 批量发送任务
        if bulk_tasks:
            # 直接创建TaskMessage对象
            from ..core.message import TaskMessage
            task_messages = []
            for task in bulk_tasks:
                # 准备kwargs
                kwargs = task.task_kwargs or {}
                # 添加任务名称和scheduled_task_id用于路由和跟踪
                kwargs['__task_name'] = task.task_name
                kwargs['__scheduled_task_id'] = task.id
                
                # 将timeout、max_retries等参数放入kwargs中传递
                if task.timeout:
                    kwargs['__timeout'] = task.timeout
                if task.max_retries:
                    kwargs['__max_retries'] = task.max_retries
                if task.retry_delay:
                    kwargs['__retry_delay'] = task.retry_delay
                
                # 创建TaskMessage
                task_msg = TaskMessage(
                    queue=task.queue_name,
                    kwargs=kwargs,
                    priority=task.priority
                )
                task_messages.append(task_msg)
            
            # 使用send_tasks方法发送
            event_ids = await self.app.send_tasks(task_messages)
            logger.info(f"Triggered {len(task_messages)} tasks via send_tasks")
            
            # 准备批量操作的数据
            tasks_for_reschedule = {}  # {task_id: next_timestamp}
            completed_task_ids = []
            
            # 处理每个任务
            for task, event_id in zip(tasks_to_update, event_ids):
                # 更新上次运行时间
                task.last_run_time = datetime.now()
                
                # 更新任务的下次运行时间
                task.update_next_run_time()
                
                # 调试日志
                logger.info(f"Task {task.id} updated: type={task.task_type}, next_run_time={task.next_run_time}")
                
                # 注意：不再这里记录执行历史，因为任务已经通过bulk_write发送到队列
                # 任务记录会由消费者创建，并带有scheduled_task_id
                
                if task.task_type == TaskType.ONCE or (isinstance(task.task_type, str) and task.task_type == 'once') or not task.next_run_time:
                    # 一次性任务或已完成
                    completed_task_ids.append(str(task.id))
                    
                    # 对于一次性任务，禁用任务（但不更新整个对象）
                    if task.task_type == TaskType.ONCE or (isinstance(task.task_type, str) and task.task_type == 'once'):
                        # 稍后单独处理一次性任务的禁用
                        logger.info(f"Will disable one-time task {task.id} after execution")
                else:
                    # 重复任务，准备重新调度（只更新时间字段）
                    next_timestamp = task.next_run_time.timestamp()
                    tasks_for_reschedule[str(task.id)] = next_timestamp
            
            # 注释掉批量记录执行历史，避免ID冲突
            # 执行历史将由消费者在处理任务时记录
            # if execution_histories:
            #     await self.db_manager.batch_record_executions(execution_histories)
            
            # 批量更新任务的下次执行时间（只更新时间字段）
            update_time_tasks = []
            for task in tasks_to_update:
                if task.next_run_time and str(task.id) not in completed_task_ids:
                    update_time_tasks.append((task.id, task.next_run_time, task.last_run_time))
            
            if update_time_tasks:
                await self.db_manager.batch_update_next_run_times(update_time_tasks)
            
            # 处理需要禁用的一次性任务
            once_task_ids = []
            for task in tasks_to_update:
                if (task.task_type == TaskType.ONCE or (isinstance(task.task_type, str) and task.task_type == 'once')) and str(task.id) in completed_task_ids:
                    once_task_ids.append(task.id)
            
            if once_task_ids:
                await self.db_manager.batch_disable_once_tasks(once_task_ids)
            
            # 使用管道批量执行所有Redis操作
            if tasks_for_reschedule or completed_task_ids:
                pipeline = self.redis.pipeline()
                
                # 批量更新Redis调度
                if tasks_for_reschedule:
                    pipeline.zadd(self._get_zset_key(), tasks_for_reschedule)
                
                # 批量移除完成的任务
                if completed_task_ids:
                    pipeline.zrem(self._get_zset_key(), *completed_task_ids)
                
                # 一次性执行所有操作
                await pipeline.execute()
                
                if completed_task_ids:
                    logger.info(f"Removed {len(completed_task_ids)} completed tasks from schedule")
    
    
    async def scan_and_trigger(self):
        """扫描并触发到期任务"""
        if not self.is_leader:
            # 只有Leader才能触发任务
            return
        
        with LogContext(operation="scan_tasks"):
            # 使用优化的方法获取到期任务及详情
            tasks_with_details = await self.get_due_tasks_with_details()
            
            if not tasks_with_details:
                return
            
            logger.info(f"Found {len(tasks_with_details)} due tasks")
            
            # 使用优化的批量处理方法
            await self.batch_process_tasks_optimized(tasks_with_details)
    
    async def run(self):
        """运行调度器主循环"""
        # 建立Redis连接（使用统一的连接池管理）
        if not self.redis:
            from jettask.utils.db_connector import get_async_redis_client

            self.redis = get_async_redis_client(
                redis_url=self.redis_url,
                decode_responses=False
            )
        
        # 连接加载器和数据库管理器
        await self.loader.connect()
        await self.db_manager.connect()
        
        self.running = True
        logger.info(f"Scheduler {self.scheduler_id} started")
        
        # 启动任务加载器
        loader_task = asyncio.create_task(self.loader.run())
        
        # Leader续期任务
        async def renew_leader_loop():
            while self.running:
                if self.is_leader:
                    if not await self.renew_leader():
                        logger.warning("Failed to renew leader, will retry")
                await asyncio.sleep(self.leader_ttl // 2)
        
        renew_task = asyncio.create_task(renew_leader_loop())
        
        # 记录上次尝试获取Leader的时间
        last_leader_attempt = 0
        leader_retry_interval = 5  # 5秒重试一次获取Leader
        
        try:
            while self.running:
                try:
                    # 尝试获取Leader（但不要太频繁）
                    if not self.is_leader:
                        current_time = asyncio.get_event_loop().time()
                        if current_time - last_leader_attempt >= leader_retry_interval:
                            logger.debug(f"Scheduler {self.scheduler_id} attempting to acquire leader...")
                            acquired = await self.acquire_leader()
                            last_leader_attempt = current_time
                            
                            if acquired:
                                logger.info(f"Scheduler {self.scheduler_id} became leader")
                            else:
                                logger.debug(f"Scheduler {self.scheduler_id} will retry acquiring leader in {leader_retry_interval}s")
                    
                    # 扫描并触发任务（只有Leader执行）
                    if self.is_leader:
                        await self.scan_and_trigger()
                    
                except Exception as e:
                    logger.error(f"Scheduler cycle error: {e}", exc_info=True)
                
                # 根据是否是Leader使用不同的睡眠时间
                if self.is_leader:
                    await asyncio.sleep(self.scan_interval)  # Leader正常扫描间隔
                else:
                    await asyncio.sleep(1)  # 非Leader短暂睡眠，但不会频繁尝试获取锁
                
        finally:
            # 停止子任务
            self.loader.stop()
            renew_task.cancel()
            
            # 等待子任务结束，但设置超时避免卡住
            try:
                await asyncio.wait_for(loader_task, timeout=2.0)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            
            try:
                await asyncio.wait_for(renew_task, timeout=0.5)
            except (asyncio.TimeoutError, asyncio.CancelledError):
                pass
            
            # 强制释放Leader锁（确保CTRL+C时清理）
            await self.release_leader(force=True)
            
            # 关闭连接
            await self.loader.disconnect()
            await self.db_manager.disconnect()
            
            if self.redis:
                await self.redis.close()
                self.redis = None
            
            logger.info(f"Scheduler {self.scheduler_id} stopped")
    
    def stop(self):
        """停止调度器"""
        self.running = False
        logger.info(f"Scheduler {self.scheduler_id} stop() called, setting running=False")