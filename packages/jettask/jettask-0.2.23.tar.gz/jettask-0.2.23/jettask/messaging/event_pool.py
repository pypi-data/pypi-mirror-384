"""
EventPool - 事件池核心实现

负责：
1. 任务队列管理和消息分发
2. 消费者管理和生命周期控制
3. 优先级队列处理
4. 离线Worker恢复机制

核心组件集成：
- MessageSender/Reader: 消息发送和读取（通过container）
- QueueRegistry: 队列注册管理
- ConsumerManager: 消费者生命周期管理
"""

from ..utils.serializer import dumps_str, loads_str
import time
import threading
import logging
import asyncio
import json
from collections import defaultdict, deque, Counter
from typing import List, Optional, TYPE_CHECKING, Union
import traceback
import redis
from redis import asyncio as aioredis

from ..utils.db_connector import get_sync_redis_client, get_async_redis_client

from ..utils.helpers import get_hostname
import os
from jettask.worker.manager import ConsumerManager
from jettask.worker.recovery import OfflineWorkerRecovery
from .scanner import DelayedMessageScanner

logger = logging.getLogger('app')

# Lua脚本：原子地更新Redis hash中的最大值
UPDATE_MAX_OFFSET_LUA = """
local hash_key = KEYS[1]
local field = KEYS[2] 
local new_value = tonumber(ARGV[1])

local current = redis.call('HGET', hash_key, field)
if current == false or tonumber(current) < new_value then
    redis.call('HSET', hash_key, field, new_value)
    return 1
else
    return 0
end
"""

class EventPool(object):
    STATE_MACHINE_NAME = "STATE_MACHINE"
    TIMEOUT = 60 * 5

    def __init__(
        self,
        redis_client: redis.StrictRedis,
        async_redis_client: aioredis.StrictRedis,
        queues: list = None,
        redis_url: str = None,
        consumer_strategy: str = None,
        consumer_config: dict = None,
        redis_prefix: str = None,
        app=None,  # 添加app参数
    ) -> None:
        self.redis_client = redis_client
        self.async_redis_client = async_redis_client
        # 创建用于二进制数据的Redis客户端（用于Stream操作）
        # 直接使用全局客户端实例（单例）
        self.binary_redis_client = get_sync_redis_client(redis_url, decode_responses=False)
        self.async_binary_redis_client = get_async_redis_client(redis_url, decode_responses=False)
        
        self.queues = queues
        self._redis_url = redis_url or 'redis://localhost:6379/0'
        self.redis_prefix = redis_prefix or 'jettask'
        self.app = app  # 保存app引用
        
        # 初始化消费者管理器
        # consumer_strategy 参数已移除，现在只使用 HEARTBEAT 策略
        # 确保配置中包含队列信息、redis_url和redis_prefix
        manager_config = consumer_config or {}
        manager_config['queues'] = queues or []
        manager_config['redis_prefix'] = redis_prefix or 'jettask'
        manager_config['redis_url'] = redis_url or 'redis://localhost:6379/0'
        
        # 保存consumer_config供后续使用
        self.consumer_config = manager_config
        
        self.consumer_manager = ConsumerManager(
            redis_client=redis_client,
            config=manager_config,
            app=app
        )

        # 创建并注入 HeartbeatConsumerStrategy（兼容性层）
        from jettask.worker.lifecycle import HeartbeatConsumerStrategy
        import os
        heartbeat_strategy = HeartbeatConsumerStrategy(
            redis_client=redis_client,
            config=manager_config,
            app=app
        )
        self.consumer_manager.set_heartbeat_strategy(heartbeat_strategy)

        # 创建队列注册表，用于恢复优先级队列
        from jettask.messaging.registry import QueueRegistry
        self.queue_registry = QueueRegistry(
            redis_client=self.redis_client,
            async_redis_client=self.async_redis_client,
            redis_prefix=self.redis_prefix
        )

        # 创建带前缀的队列名称映射
        self.prefixed_queues = {}

        # 优先级队列管理（简化：直接从Redis读取，不再使用缓存）

        # 用于跟踪广播消息
        self._broadcast_message_tracker = {}
        
        self.solo_routing_tasks = {}
        self.solo_running_state = {}
        self.solo_urgent_retry = {}
        self.batch_routing_tasks = {}
        self.task_scheduler = {}
        self.running_task_state_mappings = {}
        self.delay_tasks = []
        self.solo_agg_task = {}
        self.rlock = threading.RLock()
        self._claimed_message_ids = set()  # 跟踪已认领的消息ID，防止重复处理
        self._stop_reading = False  # 用于控制停止读取的标志
        self._queue_stop_flags = {queue: False for queue in (queues or [])}  # 每个队列的停止标志
        # 延迟任务分布式锁的key
        self._delay_lock_key = f"{self.redis_prefix}:DELAY_LOCK"

        # 初始化延迟消息扫描器（带优先级队列发现回调和消费者组确保回调）
        scan_interval = manager_config.get('scan_interval', 0.05)
        self.delayed_scanner = DelayedMessageScanner(
            async_binary_redis_client=self.async_binary_redis_client,
            redis_prefix=self.redis_prefix,
            scan_interval=scan_interval,
            batch_size=100,
            priority_discovery_callback=self._discover_priority_queues_for_scanner,
            ensure_consumer_group_callback=self._ensure_consumer_group_for_scanner
        )

        # 延迟任务列表和锁（用于与扫描器通信）
        self._delayed_tasks_lists = {}
        self._delayed_tasks_locks = {}
    
    def _put_task(self, event_queue: Union[deque, asyncio.Queue], task, urgent: bool = False):
        """统一的任务放入方法"""
        # 如果是deque，使用原有逻辑
        if isinstance(event_queue, deque):
            if urgent:
                event_queue.appendleft(task)
            else:
                event_queue.append(task)
        # 如果是asyncio.Queue，则暂时只能按顺序放入（Queue不支持优先级）
        elif isinstance(event_queue, asyncio.Queue):
            # 对于asyncio.Queue，我们需要在async上下文中操作
            # 这里先保留接口，具体实现在async方法中
            pass
    
    async def _async_put_task(self, event_queue: asyncio.Queue, task, urgent: bool = False):
        """异步任务放入方法"""
        await event_queue.put(task)

    def init_routing(self):
        for queue in self.queues:
            self.solo_agg_task[queue] = defaultdict(list)
            self.solo_routing_tasks[queue] = defaultdict(list)
            self.solo_running_state[queue]  = defaultdict(bool)
            self.batch_routing_tasks[queue]  = defaultdict(list)
            self.task_scheduler[queue] = defaultdict(int)
            self.running_task_state_mappings[queue] = defaultdict(dict)
            
    def get_prefixed_queue_name(self, queue: str) -> str:
        """为队列名称添加前缀"""
        return f"{self.redis_prefix}:QUEUE:{queue}"
    
    
    def get_redis_client(self, asyncio: bool = False, binary: bool = False):
        """获取Redis客户端
        
        Args:
            asyncio: 是否使用异步客户端
            binary: 是否使用二进制客户端（用于Stream操作）
        """
        if binary:
            return self.async_binary_redis_client if asyncio else self.binary_redis_client
        return self.async_redis_client if asyncio else self.redis_client

    def _batch_send_event_sync(self, prefixed_queue, messages: List[dict], pipe):
        """批量发送事件（同步）"""
        # 使用Lua脚本批量发送消息并添加自增offset
        lua_script = """
        local stream_key = KEYS[1]
        local prefix = ARGV[1]
        local results = {}

        -- 使用Hash存储所有队列的offset
        local offsets_hash = prefix .. ':QUEUE_OFFSETS'

        -- 从stream_key中提取队列名（去掉prefix:QUEUE:前缀）
        local queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

        -- 将队列添加到全局队列注册表（包括所有队列，包括优先级队列）
        local queues_registry_key = prefix .. ':REGISTRY:QUEUES'
        redis.call('SADD', queues_registry_key, queue_name)

        -- 从ARGV[2]开始，每个参数是一个消息的data
        for i = 2, #ARGV do
            local data = ARGV[i]

            -- 使用HINCRBY原子递增offset（如果不存在会自动创建并设为1）
            local current_offset = redis.call('HINCRBY', offsets_hash, queue_name, 1)

            -- 添加消息到Stream（包含offset字段）
            local stream_id = redis.call('XADD', stream_key, '*',
                'data', data,
                'offset', current_offset)

            table.insert(results, stream_id)
        end

        return results
        """

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            # 确保消息格式正确
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        # 获取同步Redis客户端
        client = self.get_redis_client(asyncio=False, binary=True)

        # 执行Lua脚本
        results = client.eval(
            lua_script,
            1,  # 1个KEY
            prefixed_queue,  # KEY[1]: stream key
            *lua_args  # ARGV: prefix, data1, data2, ...
        )

        # 解码所有返回的Stream ID
        return [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]

    async def _batch_send_event(self, prefixed_queue, messages: List[dict], pipe):
        """批量发送事件（异步）"""
        # 使用Lua脚本批量发送消息并添加自增offset
        lua_script = """
        local stream_key = KEYS[1]
        local prefix = ARGV[1]
        local results = {}

        -- 使用Hash存储所有队列的offset
        local offsets_hash = prefix .. ':QUEUE_OFFSETS'

        -- 从stream_key中提取队列名（去掉prefix:QUEUE:前缀）
        local queue_name = string.gsub(stream_key, '^' .. prefix .. ':QUEUE:', '')

        -- 将队列添加到全局队列注册表（包括所有队列，包括优先级队列）
        local queues_registry_key = prefix .. ':REGISTRY:QUEUES'
        redis.call('SADD', queues_registry_key, queue_name)

        -- 从ARGV[2]开始，每个参数是一个消息的data
        for i = 2, #ARGV do
            local data = ARGV[i]

            -- 使用HINCRBY原子递增offset（如果不存在会自动创建并设为1）
            local current_offset = redis.call('HINCRBY', offsets_hash, queue_name, 1)

            -- 添加消息到Stream（包含offset字段）
            local stream_id = redis.call('XADD', stream_key, '*',
                'data', data,
                'offset', current_offset)

            table.insert(results, stream_id)
        end

        return results
        """

        # 准备Lua脚本参数
        lua_args = [self.redis_prefix.encode() if isinstance(self.redis_prefix, str) else self.redis_prefix]

        for message in messages:
            # 确保消息格式正确
            if 'data' in message:
                data = message['data'] if isinstance(message['data'], bytes) else dumps_str(message['data'])
            else:
                data = dumps_str(message)
            lua_args.append(data)

        # 获取异步Redis客户端（不使用pipe，直接使用client）
        client = self.get_redis_client(asyncio=True, binary=True)

        # 执行Lua脚本
        results = await client.eval(
            lua_script,
            1,  # 1个KEY
            prefixed_queue,  # KEY[1]: stream key
            *lua_args  # ARGV: prefix, data1, data2, ...
        )

        # 解码所有返回的Stream ID
        return [r.decode('utf-8') if isinstance(r, bytes) else r for r in results]
    
    def is_urgent(self, routing_key):
        is_urgent = self.solo_urgent_retry.get(routing_key, False)
        if is_urgent == True:
            del self.solo_urgent_retry[routing_key]
        return is_urgent
    
    async def scan_priority_queues(self, base_queue: str) -> list:
        """扫描Redis中的优先级队列
        
        Args:
            base_queue: 基础队列名（不带优先级后缀）
        
        Returns:
            按优先级排序的队列列表
        """
        pattern = f"{self.redis_prefix}:QUEUE:{base_queue}:*"
        
        try:
            # 使用 QueueRegistry 获取优先级队列，避免 scan
            from jettask.messaging.registry import QueueRegistry
            registry = QueueRegistry(
                redis_client=self.redis_client,
                async_redis_client=self.async_redis_client,
                redis_prefix=self.redis_prefix
            )
            
            # 获取基础队列的所有优先级队列
            priority_queue_names = await registry.get_priority_queues_for_base(base_queue)
            priority_queues = set(priority_queue_names)
            
            # 如果没有优先级队列，检查是否有带优先级后缀的队列
            if not priority_queues:
                all_queues = await registry.get_all_queues()
                for queue in all_queues:
                    if queue.startswith(f"{base_queue}:"):
                        priority_queues.add(queue)
            
            # 添加基础队列（无优先级）
            priority_queues.add(base_queue)
            
            # 按优先级排序（数字越小优先级越高）
            sorted_queues = []
            for q in priority_queues:
                if ':' in q:
                    base, priority = q.rsplit(':', 1)
                    if base == base_queue and priority.isdigit():
                        sorted_queues.append((int(priority), q))
                    else:
                        sorted_queues.append((float('inf'), q))  # 非数字优先级放最后
                else:
                    sorted_queues.append((float('inf'), q))  # 无优先级放最后
            
            sorted_queues.sort(key=lambda x: x[0])
            return [q[1] for q in sorted_queues]
            
        except Exception as e:
            import traceback
            logger.error(f"Error scanning priority queues for {base_queue}: {e}\n{traceback.format_exc()}")
            return [base_queue]  # 返回基础队列作为fallback
    
    async def _ensure_consumer_group_and_record_info(
        self,
        prefixed_queue: str,
        task_name: str,
        consumer_name: str = None,
        base_group_name: str = None
    ) -> str:
        """统一的方法：创建 consumer group 并记录 group_info

        Args:
            prefixed_queue: 带前缀的队列名（如 "test5:QUEUE:robust_bench2:6"）
            task_name: 任务名
            consumer_name: consumer 名称（可选，如果不提供会自动获取）
            base_group_name: 基础队列的 group_name（可选，优先级队列会使用这个）

        Returns:
            str: 使用的 group_name
        """
        # 提取实际队列名和基础队列名
        actual_queue_name = prefixed_queue.replace(f"{self.redis_prefix}:QUEUE:", "")
        if ':' in actual_queue_name and actual_queue_name.rsplit(':', 1)[1].isdigit():
            base_queue = actual_queue_name.rsplit(':', 1)[0]
            is_priority_queue = True
        else:
            base_queue = actual_queue_name
            is_priority_queue = False

        # 如果没有提供 consumer_name，从基础队列获取
        if consumer_name is None:
            consumer_name = self.consumer_manager.get_consumer_name(base_queue)

        # 所有队列（包括优先级队列）都使用基础队列的 group_name
        if base_group_name:
            # 优先级队列使用传入的基础 group_name
            group_name = base_group_name
        else:
            # 基础队列：构建自己的 group_name
            base_prefixed_queue = self.get_prefixed_queue_name(base_queue)
            group_name = f"{base_prefixed_queue}:{task_name}"

        # 创建 consumer group
        try:
            await self.async_redis_client.xgroup_create(
                name=prefixed_queue,
                groupname=group_name,
                id="0",
                mkstream=True
            )
            logger.debug(f"Created consumer group {group_name} for queue {prefixed_queue}")
        except Exception as e:
            if "BUSYGROUP" in str(e):
                logger.debug(f"Consumer group {group_name} already exists for queue {prefixed_queue}")
            else:
                logger.warning(f"Error creating consumer group {group_name} for {prefixed_queue}: {e}")

        # 只为基础队列记录 group_info（优先级队列共享基础队列的 group_info）
        if not is_priority_queue and self.consumer_manager:
            await self.consumer_manager.record_group_info_async(
                actual_queue_name, task_name, group_name, consumer_name
            )

        return group_name

    async def _discover_priority_queues_for_scanner(self, base_queue: str) -> list:
        """为Scanner提供的优先级队列发现回调（返回不带前缀的队列名）

        Args:
            base_queue: 基础队列名（不带前缀）

        Returns:
            优先级队列列表（不带前缀，例如 ['queue:1', 'queue:3']）
        """
        from jettask.messaging.registry import QueueRegistry
        registry = QueueRegistry(self.redis_client, self.async_redis_client, self.redis_prefix)

        # 获取基础队列的所有优先级队列
        priority_queue_names = await registry.get_priority_queues_for_base(base_queue)

        # 过滤出带数字后缀的优先级队列
        priority_queues = []
        for pq_name in priority_queue_names:
            if ':' in pq_name and pq_name.rsplit(':', 1)[1].isdigit():
                priority_queues.append(pq_name)

        # 按优先级排序（数字越小优先级越高）
        return sorted(priority_queues, key=lambda x: int(x.split(':')[-1]))

    async def _ensure_consumer_group_for_scanner(self, queue: str) -> None:
        """为Scanner提供的消费者组确保回调（当发现新的优先级队列时调用）

        Args:
            queue: 队列名（不带前缀，可能包含优先级后缀，如 'robust_bench2:6'）
        """
        try:
            # 获取带前缀的队列名
            prefixed_queue = self.get_prefixed_queue_name(queue)

            # 提取基础队列名（移除优先级后缀）
            if ':' in queue and queue.rsplit(':', 1)[1].isdigit():
                base_queue = queue.rsplit(':', 1)[0]
            else:
                base_queue = queue

            # 如果当前队列在监听的队列列表中，为所有注册的 task 创建消费者组
            if base_queue in self.queues:
                # 从 app 获取所有已注册的 task
                if self.app and hasattr(self.app, '_tasks'):
                    for task_name in self.app._tasks.keys():
                        # 使用统一的方法创建 consumer group 并记录 group_info
                        await self._ensure_consumer_group_and_record_info(
                            prefixed_queue, task_name
                        )
                        logger.info(f"Ensured consumer group for task {task_name} on queue {prefixed_queue}")
                else:
                    logger.warning(f"App or tasks not available, cannot ensure consumer groups for {queue}")
            else:
                logger.debug(f"Queue {base_queue} not in monitored queues, skipping consumer group creation")

        except Exception as e:
            logger.error(f"Error ensuring consumer group for queue {queue}: {e}", exc_info=True)

    async def get_priority_queues_direct(self, base_queue: str) -> list:
        """直接从Redis获取优先级队列列表（不使用缓存）

        Args:
            base_queue: 基础队列名

        Returns:
            优先级队列列表（已加上前缀）
        """
        # 直接从注册表获取优先级队列
        from jettask.messaging.registry import QueueRegistry
        registry = QueueRegistry(self.redis_client, self.async_redis_client, self.redis_prefix)

        # 获取基础队列的所有优先级队列
        priority_queue_names = await registry.get_priority_queues_for_base(base_queue)
        priority_queues = []

        for pq_name in priority_queue_names:
            # 只添加优先级队列（带数字后缀的）
            if ':' in pq_name and pq_name.rsplit(':', 1)[1].isdigit():
                # 构建完整的队列名
                prefixed_pq = f"{self.redis_prefix}:QUEUE:{pq_name}"
                priority_queues.append(prefixed_pq)

        # 按优先级排序（数字越小优先级越高）
        return sorted(priority_queues, key=lambda x: int(x.split(':')[-1]) if x.split(':')[-1].isdigit() else float('inf'))
  
    
    @classmethod
    def separate_by_key(cls, lst):
        groups = {}
        for item in lst:
            key = item[0]['routing_key']
            if key not in groups:
                groups[key] = []
            groups[key].append(item)
        result = []
        group_values = list(groups.values())
        while True:
            exists_data = False
            for values in group_values:
                try:
                    result.append(values.pop(0))
                    exists_data = True
                except:
                    pass
            if not exists_data:
                break
        return result
    
    async def _unified_task_checker(self, event_queue: asyncio.Queue, checker_type: str = 'solo_agg'):
        """统一的任务检查器，减少代码重复"""
        last_solo_running_state = defaultdict(dict)
        last_wait_time = defaultdict(int)
        queue_batch_tasks = defaultdict(list)
        left_queue_batch_tasks = defaultdict(list)
        
        # 延迟任务专用状态
        delay_tasks = getattr(self, 'delay_tasks', []) if checker_type == 'delay' else []
        
        while True:
            has_work = False
            current_time = time.time()
            
            if checker_type == 'delay':
                # 延迟任务逻辑
                put_count = 0
                need_del_index = []
                for i in range(len(delay_tasks)):
                    schedule_time = delay_tasks[i][0]
                    task = delay_tasks[i][1]
                    if schedule_time <= current_time:
                        try:
                            await self._async_put_task(event_queue, task)
                            need_del_index.append(i)
                            put_count += 1
                            has_work = True
                        except IndexError:
                            pass
                for i in need_del_index:
                    del delay_tasks[i]
                    
            elif checker_type == 'solo_agg':
                # Solo聚合任务逻辑
                for queue in self.queues:
                    for agg_key, tasks in self.solo_agg_task[queue].items():
                        if not tasks:
                            continue
                            
                        has_work = True
                        need_del_index = []
                        need_lock_routing_keys = []
                        sort_by_tasks = self.separate_by_key(tasks)
                        max_wait_time = 5
                        max_records = 3
                        
                        for index, (routing, task) in enumerate(sort_by_tasks):
                            routing_key = routing['routing_key']
                            max_records = routing.get('max_records', 1)
                            max_wait_time = routing.get('max_wait_time', 0)
                            
                            with self.rlock:
                                if self.solo_running_state[queue].get(routing_key, 0) > 0:
                                    continue
                                    
                            if len(queue_batch_tasks[queue] + left_queue_batch_tasks[queue]) >= max_records:
                                break 
                                
                            task["routing"] = routing

                            if self.is_urgent(routing_key):
                                left_queue_batch_tasks[queue].append(task)
                            else:
                                queue_batch_tasks[queue].append(task)
                            need_lock_routing_keys.append(routing_key)
                            need_del_index.append(index)

                        for routing_key, count in Counter(need_lock_routing_keys).items():
                            with self.rlock:
                                self.solo_running_state[queue][routing_key] = count
                                
                        if last_solo_running_state[queue] != self.solo_running_state[queue]:
                            last_solo_running_state[queue] = self.solo_running_state[queue].copy()
                            
                        tasks = [task for index, task in enumerate(sort_by_tasks) if index not in need_del_index]
                        self.solo_agg_task[queue][agg_key] = tasks
                        
                        if (len(queue_batch_tasks[queue] + left_queue_batch_tasks[queue]) >= max_records or 
                            (last_wait_time[queue] and last_wait_time[queue] < current_time - max_wait_time)):
                            for task in queue_batch_tasks[queue]:
                                await self._async_put_task(event_queue, task)
                            for task in left_queue_batch_tasks[queue]:
                                await self._async_put_task(event_queue, task)    
                            queue_batch_tasks[queue] = []
                            left_queue_batch_tasks[queue] = []
                            last_wait_time[queue] = 0
                        elif last_wait_time[queue] == 0:
                            last_wait_time[queue] = current_time
            
            # 统一的睡眠策略
            sleep_time = self._get_optimal_sleep_time(has_work, checker_type)
            await asyncio.sleep(sleep_time)
    
    def _get_optimal_sleep_time(self, has_work: bool, checker_type: str) -> float:
        """获取最优睡眠时间"""
        if checker_type == 'delay':
            return 0.001 if has_work else 1.0
        elif has_work:
            return 0.001  # 有工作时极短休眠
        else:
            return 0.01   # 无工作时短暂休眠
    
    
    async def async_check_solo_agg_tasks(self, event_queue: asyncio.Queue):
        """异步版本的聚合任务检查"""
        await self._unified_task_checker(event_queue, checker_type='solo_agg')
    
    async def check_solo_agg_tasks(self, event_queue: asyncio.Queue):
        """聚合任务检查"""
        await self._unified_task_checker(event_queue, checker_type='solo_agg')
    
    def check_sole_tasks(self, event_queue: Union[deque, asyncio.Queue]):
        agg_task_mappings = {queue:  defaultdict(list) for queue in self.queues}
        agg_wait_task_mappings = {queue:  defaultdict(float) for queue in self.queues}
        task_max_wait_time_mapping = {}
        make_up_for_index_mappings = {queue:  defaultdict(int) for queue in self.queues} 
        while True:
            put_count = 0
            for queue in self.queues:
                agg_task = agg_task_mappings[queue]
                for routing_key, tasks in self.solo_routing_tasks[queue].items():
                    schedule_time = self.task_scheduler[queue][routing_key]
                    if tasks:
                        for task in tasks:
                            prev_routing = task[0]
                            if agg_key:= prev_routing.get('agg_key'):
                                if not self.running_task_state_mappings[queue][agg_key]:
                                    self.solo_running_state[queue][routing_key] = False
                                    break 
                    if (
                        schedule_time <= time.time()
                        and self.solo_running_state[queue][routing_key] == False
                    ) :
                            try:
                                routing, task = tasks.pop(0)
                            except IndexError:
                                continue
                            task["routing"] = routing
                            
                            agg_key = routing.get('agg_key')
                            if agg_key is not None:
                                start_time = agg_wait_task_mappings[queue][agg_key]
                                if not start_time:
                                    agg_wait_task_mappings[queue][agg_key] = time.time()
                                    start_time = agg_wait_task_mappings[queue][agg_key]
                                agg_task[agg_key].append(task)
                                max_wait_time = routing.get('max_wait_time', 3)
                                task_max_wait_time_mapping[agg_key] = max_wait_time
                                if len(agg_task[agg_key])>=routing.get('max_records', 100) or time.time()-start_time>=max_wait_time:
                                    logger.debug(f'{agg_key=} {len(agg_task[agg_key])} 已满，准备发车！{routing.get("max_records", 100)} {time.time()-start_time} {max_wait_time}')
                                    for task in agg_task[agg_key]:
                                        task['routing']['version'] = 1
                                        self.running_task_state_mappings[queue][agg_key][task['event_id']] = time.time()
                                        self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                                    agg_task[agg_key] = []
                                    make_up_for_index_mappings[queue][agg_key] = 0 
                                    agg_wait_task_mappings[queue][agg_key] = 0
                            else:
                                self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                            self.solo_running_state[queue][routing_key] = True
                            put_count += 1
                for agg_key in agg_task.keys():
                    if not agg_task[agg_key]:
                        continue
                    start_time = agg_wait_task_mappings[queue][agg_key]
                    max_wait_time = task_max_wait_time_mapping[agg_key]
                    if make_up_for_index_mappings[queue][agg_key]>= len(agg_task[agg_key])-1:
                        make_up_for_index_mappings[queue][agg_key] = 0
                    routing = agg_task[agg_key][make_up_for_index_mappings[queue][agg_key]]['routing']
                    routing_key = routing['routing_key']
                    self.solo_running_state[queue][routing_key] = False
                    make_up_for_index_mappings[queue][agg_key] += 1
                    if time.time()-start_time>=max_wait_time:
                        logger.debug(f'{agg_key=} {len(agg_task[agg_key])}被迫发车！ {time.time()-start_time} {max_wait_time}')
                        for task in agg_task[agg_key]:
                            task['routing']['version'] = 1
                            self.running_task_state_mappings[queue][agg_key][task['event_id']] = time.time()
                            self._put_task(event_queue, task, urgent=self.is_urgent(routing_key))
                        agg_task[agg_key] = []
                        make_up_for_index_mappings[queue][agg_key] = 0
                        agg_wait_task_mappings[queue][agg_key] = 0
            # 优化：根据处理任务数量动态调整休眠时间
            if not put_count:
                time.sleep(0.001)
            elif put_count < 5:
                time.sleep(0.0005)  # 少量任务时极短休眠
                
    async def check_batch_tasks(self, event_queue: asyncio.Queue):
        """批量任务检查 - 已简化为统一检查器"""
        # 批量任务逻辑已整合到其他检查器中，这个函数保留以兼容
        await asyncio.sleep(0.1)

    async def check_delay_tasks(self, event_queue: asyncio.Queue):
        """延迟任务检查"""
        await self._unified_task_checker(event_queue, checker_type='delay')

    def _handle_redis_error(self, error: Exception, consecutive_errors: int, queue: str = None) -> tuple[bool, int]:
        """处理Redis错误的通用方法
        返回: (should_recreate_connection, new_consecutive_errors)
        """
        if isinstance(error, redis.exceptions.ConnectionError):
            logger.error(f'Redis连接错误: {error}')
            logger.error(traceback.format_exc())
            consecutive_errors += 1
            if consecutive_errors >= 5:
                logger.error(f'连续连接失败{consecutive_errors}次，重新创建连接')
                return True, 0
            return False, consecutive_errors
            
        elif isinstance(error, redis.exceptions.ResponseError):
            if "NOGROUP" in str(error) and queue:
                logger.warning(f'队列 {queue} 或消费者组不存在')
                return False, consecutive_errors
            else:
                logger.error(f'Redis错误: {error}')
                logger.error(traceback.format_exc())
                consecutive_errors += 1
                return False, consecutive_errors
        else:
            logger.error(f'意外错误: {error}')
            logger.error(traceback.format_exc())
            consecutive_errors += 1
            return False, consecutive_errors

    def _process_message_common(self, event_id: str, event_data: dict, queue: str, event_queue, is_async: bool = False, consumer_name: str = None, group_name: str = None):
        """通用的消息处理逻辑，供同步和异步版本使用"""
        # 检查消息是否已被认领，防止重复处理
        if event_id in self._claimed_message_ids:
            logger.debug(f"跳过已认领的消息 {event_id}")
            return event_id
        
        # 解析消息中的实际数据
        # event_data 格式: {b'data': b'{"name": "...", "event_id": "...", ...}'}
        actual_event_id = event_id  # 默认使用Stream ID
        parsed_event_data = None  # 解析后的数据
        
        # 检查是否有data字段（Stream消息格式）
        if 'data' in event_data or b'data' in event_data:
            data_field = event_data.get('data') or event_data.get(b'data')
            if data_field:
                try:
                    # 直接解析二进制数据，不需要解码
                    if isinstance(data_field, bytes):
                        parsed_data = loads_str(data_field)
                    else:
                        parsed_data = data_field
                    # 检查是否有原始的event_id（延迟任务会有）
                    if 'event_id' in parsed_data:
                        actual_event_id = parsed_data['event_id']
                    # 使用解析后的数据作为event_data
                    parsed_event_data = parsed_data
                except (ValueError, UnicodeDecodeError):
                    pass  # 解析失败，使用默认的Stream ID
        
        # 如果成功解析了数据，使用解析后的数据；否则使用原始数据
        final_event_data = parsed_event_data if parsed_event_data is not None else event_data
        
        routing = final_event_data.get("routing")
        
        # 从消息体中获取实际的队列名（可能包含优先级后缀）
        # 这确保ACK使用正确的stream key
        actual_queue = final_event_data.get('queue', queue)

        # 如果没有传入group_name，使用默认值（prefixed_queue）
        if not group_name:
            prefixed_queue = self.get_prefixed_queue_name(queue)
            group_name = prefixed_queue

        # 提取并确保 offset 在 event_data 中（关键：确保延迟任务的 offset 能被传递到 executor）
        offset = None
        if 'offset' in final_event_data:
            try:
                offset = int(final_event_data['offset'])
            except (ValueError, TypeError):
                pass
        # 如果 final_event_data 中没有 offset，从原始 event_data 中提取（Stream 消息格式）
        elif 'offset' in event_data or b'offset' in event_data:
            offset_field = event_data.get('offset') or event_data.get(b'offset')
            if offset_field:
                try:
                    offset = int(offset_field)
                    # 将 offset 添加到 final_event_data 中，确保 executor 能提取
                    final_event_data['offset'] = offset
                except (ValueError, TypeError):
                    pass

        task_item = {
            "queue": actual_queue,  # 使用消息体中的实际队列名（可能包含优先级）
            "event_id": actual_event_id,
            "event_data": final_event_data,  # 使用解析后的数据（包含 offset）
            "consumer": consumer_name,  # 添加消费者信息
            "group_name": group_name,  # 添加group_name用于ACK
        }
        
        push_flag = True
        if routing:
            # routing 现在直接是对象，不需要反序列化
            if agg_key := routing.get('agg_key'):
                self.solo_agg_task[queue][agg_key].append(
                    [routing, task_item]
                )
                push_flag = False
        
        if push_flag:
            if is_async:
                # 这里不能直接await，需要返回一个标记
                return ('async_put', task_item)
            else:
                self._put_task(event_queue, task_item)
        
        return event_id
    
    async def _start_offline_worker_processor_with_restart(self, queue: str):
        """启动带自动重启机制的离线worker处理器"""
        async def supervisor():
            """监督器任务，负责重启失败的处理器"""
            restart_count = 0
            max_restarts = 10

            while not self._stop_reading and restart_count < max_restarts:
                try:
                    logger.debug(f"Starting offline worker processor for queue {queue} (attempt {restart_count + 1})")
                    await self._process_offline_workers(queue)
                    # 如果正常退出（stop_reading为True），则不重启
                    if self._stop_reading:
                        logger.debug(f"Offline worker processor for queue {queue} stopped normally")
                        break
                except asyncio.CancelledError:
                    logger.debug(f"Offline worker processor for queue {queue} cancelled")
                    break
                except Exception as e:
                    restart_count += 1
                    import traceback 
                    logger.error(f"Offline worker processor for queue {queue} crashed: {e}")
                    logger.error(traceback.format_exc())
                    if restart_count < max_restarts:
                        wait_time = min(restart_count * 5, 30)  # 递增等待时间，最多30秒
                        logger.debug(f"Restarting offline worker processor for queue {queue} in {wait_time} seconds...")
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"Offline worker processor for queue {queue} failed {max_restarts} times, giving up")
            
        # 创建监督器任务
        asyncio.create_task(supervisor())

    async def _execute_recovery_for_queue(self, queue: str, log_prefix: str = "Recovery") -> int:
        """
        执行单个队列的消息恢复（封装通用逻辑）

        Args:
            queue: 队列名称
            log_prefix: 日志前缀，用于区分调用场景（如"Recovery Event"或"Recovery Fallback"）

        Returns:
            int: 恢复的消息数量
        """
        # 获取该队列的恢复器（如果已创建）
        recovery_key = f"recovery_{queue}"
        recovery = getattr(self, recovery_key, None)

        if not recovery:
            # 创建新的恢复器
            recovery = OfflineWorkerRecovery(
                async_redis_client=self.async_binary_redis_client,
                redis_prefix=self.redis_prefix,
                worker_prefix='WORKER',
                consumer_manager=self.consumer_manager,
                queue_registry=self.queue_registry,
                worker_state=self.app.worker_state if self.app else None
            )
            setattr(self, recovery_key, recovery)

        # 获取当前 consumer
        # 统一 group_name 架构：所有队列（包括优先级队列）使用同一个 consumer name
        base_queue = queue
        if ':' in queue and queue.rsplit(':', 1)[-1].isdigit():
            base_queue = queue.rsplit(':', 1)[0]

        try:
            current_consumer = self.consumer_manager.get_consumer_name(base_queue)
            # 不再为优先级队列添加后缀
        except Exception as e:
            logger.warning(f"[{log_prefix}] Failed to get consumer for queue {queue}: {e}")
            raise

        # 创建一个回调函数，根据 task_name 获取对应的 event_queue
        def get_event_queue_by_task(task_name: str):
            """根据 task_name 获取对应的 event_queue"""
            event_queue_dict = getattr(self, '_event_queue_dict', None)
            if event_queue_dict:
                return event_queue_dict.get(task_name)
            return None

        # 执行恢复（传入 event_queue_callback）
        recovered = await recovery.recover_offline_workers(
            queue=queue,
            event_queue=None,  # 保持为 None，通过 callback 传递
            current_consumer_name=current_consumer,
            event_queue_callback=get_event_queue_by_task  # 传入回调函数
        )

        return recovered

    async def handle_worker_offline_event(self, worker_id: str, queues: list = None):
        """
        处理 Worker 离线事件（事件驱动）
        当收到 Worker 离线通知时立即处理消息转移

        Args:
            worker_id: 离线的 Worker ID
            queues: Worker 负责的队列列表（可选，如果不提供则从 Redis 读取）
        """
        try:
            logger.info(f"[Recovery Event] Received offline event for worker {worker_id}")

            # 如果没有提供队列列表，从 Redis 读取
            if not queues:
                worker_key = f"{self.redis_prefix}:WORKER:{worker_id}"
                worker_data = await self.async_redis_client.hgetall(worker_key)
                if worker_data:
                    queues_str = worker_data.get(b'queues', b'').decode('utf-8') if isinstance(worker_data.get(b'queues'), bytes) else worker_data.get('queues', '')
                    queues = queues_str.split(',') if queues_str else []

            if not queues:
                logger.warning(f"[Recovery Event] No queues found for worker {worker_id}, skipping recovery")
                return

            # 获取 event_queue 字典（从 EventPool 保存的引用中）
            event_queue_dict = getattr(self, '_event_queue_dict', None)
            if not event_queue_dict:
                logger.warning(f"[Recovery Event] No event_queue_dict available, recovered messages will not be executed")

            # 为每个队列触发恢复
            for queue in queues:
                if not queue.strip():
                    continue

                logger.info(f"[Recovery Event] Triggering recovery for worker {worker_id} on queue {queue}")

                try:
                    # 使用封装的方法执行恢复
                    recovered = await self._execute_recovery_for_queue(queue, log_prefix="Recovery Event")

                    if recovered > 0:
                        logger.info(f"[Recovery Event] Recovered {recovered} messages from worker {worker_id} on queue {queue}")
                    else:
                        logger.debug(f"[Recovery Event] No messages to recover from worker {worker_id} on queue {queue}")
                except Exception as e:
                    logger.warning(f"[Recovery Event] Failed to recover queue {queue}: {e}")
                    continue

        except Exception as e:
            logger.error(f"[Recovery Event] Error handling offline event for worker {worker_id}: {e}", exc_info=True)

    async def _process_offline_workers(self, queue: str):
        """定期检测离线worker并使用XCLAIM转移其pending消息（兜底机制）"""
        logger.debug(f"Started offline worker processor for queue {queue}")

        # 等待consumer manager初始化
        base_queue = queue
        if ':' in queue and queue.rsplit(':', 1)[-1].isdigit():
            base_queue = queue.rsplit(':', 1)[0]

        wait_times = [0.1, 0.2, 0.4, 0.8, 1.6, 3.2]
        for wait_time in wait_times:
            try:
                current_consumer = self.consumer_manager.get_consumer_name(base_queue)
                if current_consumer:
                    if base_queue != queue:
                        current_consumer = f"{current_consumer}:{queue.rsplit(':', 1)[-1]}"
                    logger.debug(f"Consumer manager initialized for queue {queue}, consumer: {current_consumer}")
                    break
            except Exception as e:
                logger.debug(f"Consumer manager not ready yet, waiting {wait_time}s: {e}")
                await asyncio.sleep(wait_time)

        logger.debug(f"Offline worker processor for queue {queue} is now active")

        # 扫描间隔（拉长到30秒，作为兜底）
        scan_interval = 30

        scan_count = 0
        while not self._stop_reading:
            try:
                scan_count += 1
                # 每10次扫描记录一次日志（现在是5分钟一次）
                # if scan_count % 10 == 1:
                logger.debug(f"[Recovery Fallback] Periodic scan active for queue {queue} (scan #{scan_count})")

                # 使用封装的方法执行兜底扫描
                recovered = await self._execute_recovery_for_queue(queue, log_prefix="Recovery Fallback")

                if recovered > 0:
                    logger.warning(f"[Recovery Fallback] Found {recovered} messages in fallback scan for queue {queue} - event-driven recovery may have missed them")

            except Exception as e:
                logger.error(f"Error in offline worker processor for queue {queue}: {e}", exc_info=True)

            # 等待下一次扫描
            await asyncio.sleep(scan_interval)

        logger.debug(f"Stopped offline worker processor for queue {queue}")

    async def _perform_self_recovery(self, queues: set, event_queue: dict):
        """
        在worker启动时执行"自我恢复"

        场景：Worker复用了离线worker ID，但此时worker已经变为在线状态(is_alive=true)，
        周期性扫描只查找is_alive=false的worker，会漏掉当前worker之前的pending消息。

        解决方案：主动恢复"当前worker"的pending消息，无论is_alive状态如何。

        Args:
            queues: 需要恢复的队列集合（包括优先级队列）
            event_queue: 事件队列字典
        """
        logger.info("[Recovery Self] Starting self-recovery for current worker...")

        # 获取当前 worker ID
        current_worker_id = None
        if self.app and hasattr(self.app, 'worker_id'):
            current_worker_id = self.app.worker_id

        if not current_worker_id:
            logger.debug("[Recovery Self] No worker_id available, skipping self-recovery")
            return

        worker_key = f"{self.redis_prefix}:WORKER:{current_worker_id}"
        logger.info(f"[Recovery Self] Checking pending messages for worker: {current_worker_id}")

        # event_queue callback
        def get_event_queue_by_task(task_name: str):
            """根据 task_name 获取对应的 event_queue"""
            if event_queue:
                return event_queue.get(task_name)
            return None

        total_recovered = 0

        # 按队列恢复消息
        for queue in queues:
            try:
                # 获取基础队列名
                base_queue = queue
                if ':' in queue and queue.rsplit(':', 1)[-1].isdigit():
                    base_queue = queue.rsplit(':', 1)[0]

                # 等待 consumer manager 初始化
                current_consumer = None
                for _ in range(5):
                    try:
                        current_consumer = self.consumer_manager.get_consumer_name(base_queue)
                        if current_consumer:
                            # 优先级队列需要添加后缀
                            if base_queue != queue:
                                priority_suffix = queue.rsplit(':', 1)[-1]
                                current_consumer = f"{current_consumer}:{priority_suffix}"
                            break
                    except:
                        pass
                    await asyncio.sleep(0.1)

                if not current_consumer:
                    logger.warning(f"[Recovery Self] Cannot get consumer for queue {queue}, skipping")
                    continue

                # 构建 stream_key
                stream_key = f"{self.redis_prefix}:QUEUE:{queue}"

                # 获取 group_info
                worker_data = await self.async_redis_client.hgetall(worker_key)
                if not worker_data:
                    logger.debug(f"[Recovery Self] Worker {current_worker_id} has no data")
                    continue

                # 解码 worker_data
                decoded_worker_data = {}
                for k, v in worker_data.items():
                    key = k.decode('utf-8') if isinstance(k, bytes) else k
                    value = v.decode('utf-8') if isinstance(v, bytes) else v
                    decoded_worker_data[key] = value

                # 提取 group_info
                group_infos = []
                for key, value in decoded_worker_data.items():
                    if key.startswith('group_info:'):
                        try:
                            group_info = json.loads(value)
                            if group_info.get('queue') == base_queue:
                                group_infos.append(group_info)
                        except Exception as e:
                            logger.error(f"[Recovery Self] Error parsing group_info: {e}")

                if not group_infos:
                    logger.debug(f"[Recovery Self] No group_info for queue {queue}")
                    continue

                # 尝试恢复每个 group 的 pending 消息
                for group_info in group_infos:
                    try:
                        task_name = group_info.get('task_name')
                        group_name = group_info.get('group_name')

                        if not task_name or not group_name:
                            continue

                        # 构建离线 consumer 名称
                        # 统一 group_name 架构：所有队列使用同一个 consumer name
                        offline_consumer_name = group_info.get('consumer_name')

                        # 检查是否有 pending 消息
                        pending_info = await self.async_binary_redis_client.xpending(stream_key, group_name)
                        if not pending_info or pending_info.get('pending', 0) == 0:
                            continue

                        # 查询详细的 pending 消息
                        detailed_pending = await self.async_binary_redis_client.xpending_range(
                            stream_key, group_name,
                            min='-', max='+', count=100,
                            consumername=offline_consumer_name
                        )

                        if not detailed_pending:
                            continue

                        logger.info(
                            f"[Recovery Self] Found {len(detailed_pending)} pending messages "
                            f"for worker {current_worker_id}, queue {queue}, task {task_name}"
                        )

                        # 认领消息
                        message_ids = [msg['message_id'] for msg in detailed_pending]
                        claimed_messages = await self.async_binary_redis_client.xclaim(
                            stream_key, group_name, current_consumer,
                            min_idle_time=0,  # 立即认领
                            message_ids=message_ids
                        )

                        if claimed_messages:
                            logger.info(
                                f"[Recovery Self] Claimed {len(claimed_messages)} messages "
                                f"from {offline_consumer_name} to {current_consumer}"
                            )

                            # 将消息放入 event_queue
                            task_event_queue = get_event_queue_by_task(task_name)
                            if task_event_queue:
                                for msg_id, msg_data in claimed_messages:
                                    if isinstance(msg_id, bytes):
                                        msg_id = msg_id.decode('utf-8')

                                    data_field = msg_data.get(b'data') or msg_data.get('data')
                                    if data_field:
                                        try:
                                            import msgpack
                                            parsed_data = msgpack.unpackb(data_field, raw=False)
                                            parsed_data['_task_name'] = task_name
                                            parsed_data['queue'] = queue

                                            task_item = {
                                                'queue': queue,
                                                'event_id': msg_id,
                                                'event_data': parsed_data,
                                                'consumer': current_consumer,
                                                'group_name': group_name
                                            }

                                            await task_event_queue.put(task_item)
                                            total_recovered += 1
                                        except Exception as e:
                                            logger.error(f"[Recovery Self] Error processing message: {e}")
                            else:
                                logger.warning(f"[Recovery Self] No event_queue for task {task_name}")

                    except Exception as e:
                        logger.error(f"[Recovery Self] Error recovering group {group_info}: {e}", exc_info=True)

            except Exception as e:
                logger.error(f"[Recovery Self] Error recovering queue {queue}: {e}", exc_info=True)

        if total_recovered > 0:
            logger.info(f"[Recovery Self] Self-recovery completed: recovered {total_recovered} messages")
        else:
            logger.info("[Recovery Self] Self-recovery completed: no pending messages found")

    async def _update_read_offset(self, queue: str, group_name: str, offset: int):
        """更新已读取的offset（只更新最大值）

        Args:
            queue: 队列名（不带前缀，可能包含优先级后缀，如 "robust_bench2:8"）
            group_name: consumer group名称（格式：{prefix}:QUEUE:{base_queue}:{task_name}）
            offset: 读取的offset值
        """
        try:
            if offset is None:
                return

            read_offset_key = f"{self.redis_prefix}:READ_OFFSETS"

            # 从 group_name 中提取 task_name（最后一段）
            task_name = group_name.split(':')[-1]

            # 构建 field：队列名（含优先级）+ 任务名
            # 例如：robust_bench2:8:benchmark_task
            field = f"{queue}:{task_name}"

            # 使用Lua脚本原子地更新最大offset
            await self.async_redis_client.eval(
                UPDATE_MAX_OFFSET_LUA,
                2,  # keys数量
                read_offset_key,  # KEYS[1]
                field,  # KEYS[2]
                offset  # ARGV[1]
            )
            logger.debug(f"Updated read offset for {field}: {offset}")
        except Exception as e:
            logger.error(f"Error updating read offset: {e}")
    
    async def listening_event(self, event_queue: dict, prefetch_multiplier: int = 1):
        """监听事件 - 为每个task创建独立的consumer group

        Args:
            event_queue: dict[str, asyncio.Queue] - 按task_name隔离的队列字典
            prefetch_multiplier: 预取倍数
        """
        # 验证参数类型
        if not isinstance(event_queue, dict):
            raise TypeError(f"event_queue must be a dict[str, asyncio.Queue], got {type(event_queue)}")

        # 保存 event_queue 字典的引用，供事件驱动的恢复使用
        self._event_queue_dict = event_queue

        logger.info(f"Using task-isolated event queue mode for tasks: {list(event_queue.keys())}")

        # 创建一个字典来存储每个队列的延迟任务 - 使用list + Lock更高效
        for queue in self.queues:
            self._delayed_tasks_lists[queue] = []
            self._delayed_tasks_locks[queue] = asyncio.Lock()

        # 保存所有创建的任务，以便清理时能够取消它们
        self._background_tasks = []

        # group信息将在每个task监听时记录
        
        async def listen_event_by_task(queue, task_name):
            """为单个任务监听事件"""
            # 恢复读取历史 pending 消息的逻辑
            check_backlog = {}  # {queue_name: bool} - 首次读取 pending 消息
            lastid = {}  # 每个队列的lastid - 首次为 "0"，后续为 ">"
            consecutive_errors = 0
            max_consecutive_errors = 5

            # 获取当前task使用的event_queue
            task_event_queue = event_queue.get(task_name)
            if not task_event_queue:
                logger.error(f"No event queue found for task {task_name}")
                return

            # 获取任务对象
            task = self.app._tasks.get(task_name)
            if not task:
                logger.error(f"Task {task_name} not found")
                return

            # 定义必要的变量
            prefixed_queue = self.get_prefixed_queue_name(queue)
            consumer_name = self.consumer_manager.get_consumer_name(queue)
            # 使用函数名作为group_name，实现任务隔离（用于后续消息处理）
            group_name = f"{prefixed_queue}:{task_name}"

            # 直接获取所有优先级队列（包括默认队列）
            priority_queues = await self.get_priority_queues_direct(queue)
            all_queues = [prefixed_queue] + priority_queues  # 默认队列 + 优先级队列

            # 为基础队列创建 consumer group 并记录 group_info
            base_group_name = await self._ensure_consumer_group_and_record_info(
                prefixed_queue, task_name, consumer_name
            )

            # 为优先级队列创建 consumer group（共享基础队列的 group_name）
            for pq in priority_queues:
                await self._ensure_consumer_group_and_record_info(
                    pq, task_name, consumer_name, base_group_name=base_group_name
                )

            # ✅ 初始化每个队列：首次读取 pending 消息（从 "0" 开始）
            for q in all_queues:
                lastid[q] = "0"  # 首次读取历史消息
                check_backlog[q] = True  # 首次读取 pending 消息
            
            # 获取该队列的延迟任务列表和锁
            delayed_list = self._delayed_tasks_lists.get(queue)
            delayed_lock = self._delayed_tasks_locks.get(queue)
            
            # 记录上次优先级队列更新时间和上次group_info检查时间
            last_priority_update = time.time()
            last_group_info_check = time.time()

            while not self._stop_reading:
                # 定期直接从Redis获取优先级队列（每1秒检查一次）
                current_time = time.time()
                if current_time - last_priority_update >= 1:  # 简化为固定1秒间隔
                    new_priority_queues = await self.get_priority_queues_direct(queue)

                    # 如果优先级队列有变化，更新本地变量
                    if new_priority_queues != priority_queues:
                        logger.debug(f"Priority queues updated for {queue}: {priority_queues} -> {new_priority_queues}")
                        priority_queues = new_priority_queues
                        all_queues = [prefixed_queue] + priority_queues

                        # 为新的优先级队列创建consumer group（共享基础队列的 group_name）
                        for q in all_queues:
                            if q not in lastid:  # 这是新队列
                                await self._ensure_consumer_group_and_record_info(
                                    q, task_name, consumer_name, base_group_name=group_name
                                )
                                logger.debug(f"Ensured consumer group for new priority queue {q}")

                                # ✅ 初始化新队列：读取历史 pending 消息
                                lastid[q] = "0"
                                check_backlog[q] = True

                    last_priority_update = current_time

                # 定期检查并恢复group_info（每10秒检查一次）
                if current_time - last_group_info_check >= 10:
                    # 检查worker key中是否缺失group_info
                    if self.consumer_manager:
                        worker_key = self.consumer_manager._heartbeat_strategy._worker_key
                        try:
                            # 检查第一个队列的group_info是否存在
                            first_queue = all_queues[0] if all_queues else prefixed_queue
                            first_group_name = f"{first_queue}:{task_name}"
                            field_name = f"group_info:{first_group_name}"

                            group_info_exists = await self.async_redis_client.hexists(worker_key, field_name)

                            # 如果group_info不存在，说明worker key可能被重建了，需要恢复group_info
                            if not group_info_exists:
                                logger.info(f"Detected missing group_info for task {task_name}, restoring...")

                                # 恢复基础队列的 group_info
                                await self._ensure_consumer_group_and_record_info(prefixed_queue, task_name, consumer_name)

                                # 为优先级队列重新创建 consumer group（共享基础队列的 group_name）
                                for pq in priority_queues:
                                    await self._ensure_consumer_group_and_record_info(
                                        pq, task_name, consumer_name, base_group_name=group_name
                                    )

                                logger.info(f"Restored group_info and consumer groups for {len(all_queues)} queues for task {task_name}")
                        except Exception as e:
                            logger.error(f"Error checking/restoring group_info: {e}", exc_info=True)

                    last_group_info_check = current_time
                
                # 批量获取并处理延迟任务（使用list更高效）
                if delayed_list:
                    # 原子地交换list内容
                    async with delayed_lock:
                        if delayed_list:
                            # 快速拷贝并清空原list
                            tasks_to_process = delayed_list.copy()
                            delayed_list.clear()
                        else:
                            tasks_to_process = []
                    
                    # 处理所有延迟任务
                    if tasks_to_process:
                        my_tasks = []  # 属于当前task的任务
                        other_tasks = []  # 属于其他task的任务
                        
                        for delayed_task in tasks_to_process:
                            # Scanner 返回的格式：{'event_id': '...', 'queue': '...'}
                            # 没有 data 字段，需要通过 XCLAIM 获取

                            # 注意：新版本Scanner只返回消息ID，不返回数据
                            # 数据将在后续通过XCLAIM获取
                            task_data = delayed_task.get('data', None)

                            # 如果task_data存在（兼容旧版本Scanner）
                            if task_data:
                                if isinstance(task_data, str):
                                    import json
                                    task_data = json.loads(task_data)

                                # 检查消息是否指定了目标task
                                target_tasks = task_data.get('_target_tasks', None)
                                if target_tasks and task_name not in target_tasks:
                                    # 这个消息不是给当前task的
                                    other_tasks.append(delayed_task)
                                    continue

                            # 当前task处理这个任务
                            # task_data可能为None，会在后续通过XCLAIM获取
                            my_tasks.append((delayed_task, task_data))
                        
                        # 处理属于当前task的所有任务
                        # 按队列分组延迟任务的 offset（因为可能来自不同的优先级队列）
                        max_offsets_by_queue = {}

                        for delayed_task, task_data in my_tasks:
                            event_id = delayed_task.get('event_id', f"delayed-{time.time()}")

                            # 获取任务来自哪个队列（可能包含优先级后缀）
                            task_queue = delayed_task.get('queue', queue)

                            # 如果task_data为None，说明Scanner只返回了消息ID
                            # 需要使用XCLAIM从Stream中claim消息并转移所有权
                            if task_data is None:
                                prefixed_queue = self.get_prefixed_queue_name(task_queue)
                                try:
                                    # 使用XCLAIM转移消息所有权
                                    # min_idle_time设为0，强制claim
                                    claimed_messages = await self.async_binary_redis_client.xclaim(
                                        name=prefixed_queue,
                                        groupname=group_name,
                                        consumername=consumer_name,
                                        min_idle_time=0,  # 立即claim，不管idle时间
                                        message_ids=[event_id]
                                    )

                                    if not claimed_messages:
                                        logger.warning(f"Failed to claim delayed message {event_id} from queue {task_queue}")
                                        continue

                                    # 解析claimed消息
                                    claimed_msg = claimed_messages[0]  # [(stream_id, fields)]
                                    if isinstance(claimed_msg, (list, tuple)) and len(claimed_msg) >= 2:
                                        fields = claimed_msg[1]

                                        # 将fields转换为字典
                                        task_data_dict = {}
                                        if isinstance(fields, dict):
                                            task_data_dict = fields
                                        elif isinstance(fields, list):
                                            for j in range(0, len(fields), 2):
                                                if j + 1 < len(fields):
                                                    key = fields[j]
                                                    value = fields[j + 1]
                                                    task_data_dict[key] = value

                                        # 解析data字段
                                        data_field = task_data_dict.get('data') or task_data_dict.get(b'data')
                                        if data_field:
                                            task_data = loads_str(data_field)

                                            # 提取 offset 字段（关键：确保延迟任务的 offset 能被记录）
                                            offset_field = task_data_dict.get('offset') or task_data_dict.get(b'offset')
                                            if offset_field:
                                                try:
                                                    offset_value = int(offset_field) if isinstance(offset_field, (int, str)) else int(offset_field.decode())
                                                    task_data['offset'] = offset_value
                                                except (ValueError, TypeError, AttributeError):
                                                    logger.debug(f"Failed to extract offset from claimed message {event_id}")
                                        else:
                                            logger.warning(f"No data field in claimed message {event_id}")
                                            continue
                                    else:
                                        logger.warning(f"Invalid claimed message format for {event_id}")
                                        continue

                                except Exception as e:
                                    logger.error(f"Error claiming delayed message {event_id}: {e}", exc_info=True)
                                    continue

                            task_data['_task_name'] = task_name

                            # 记录延迟精度（用于调试）
                            if 'execute_at' in task_data:
                                delay_error = time.time() - task_data['execute_at']
                                if abs(delay_error) > 0.1:  # 超过100ms才记录
                                    logger.debug(f'延迟任务 {event_id} 执行误差: {delay_error*1000:.1f}ms')

                            # 收集每个队列的最大offset
                            if 'offset' in task_data:
                                try:
                                    message_offset = int(task_data['offset'])
                                    if task_queue not in max_offsets_by_queue or message_offset > max_offsets_by_queue[task_queue]:
                                        max_offsets_by_queue[task_queue] = message_offset
                                except (ValueError, TypeError):
                                    pass

                            # 所有队列（包括优先级队列）都使用基础队列的 group_name
                            result = self._process_message_common(
                                event_id, task_data, task_queue, task_event_queue,
                                is_async=True, consumer_name=consumer_name, group_name=group_name
                            )
                            if isinstance(result, tuple) and result[0] == 'async_put':
                                await self._async_put_task(task_event_queue, result[1])

                        # 批量更新每个队列的最大offset（所有队列使用同一个 group_name）
                        for task_queue, max_offset in max_offsets_by_queue.items():
                            asyncio.create_task(self._update_read_offset(task_queue, group_name, max_offset))
                        
                        # 把不属于当前task的任务放回list
                        if other_tasks:
                            async with delayed_lock:
                                delayed_list.extend(other_tasks)
                
                # 处理正常的Stream消息（支持优先级队列）
                # 实现真正的优先级消费：
                # 1. 先检查event_queue是否已满
                # 2. 优先从高优先级队列读取
                # 3. 只有高优先级队列空了才读取低优先级
                # 4. 不超过prefetch_multiplier限制
                
                # 检查内存队列是否已满
                current_queue_size = task_event_queue.qsize() if hasattr(task_event_queue, 'qsize') else 0
                if current_queue_size >= prefetch_multiplier:
                    # 内存队列已满，等待处理
                    await asyncio.sleep(0.01)  # 短暂等待
                    continue
                
                messages = []
                messages_needed = prefetch_multiplier - current_queue_size  # 还能读取的消息数
                
                if messages_needed <= 0:
                    # 不需要读取更多消息
                    await asyncio.sleep(0.01)
                    continue
                
                # 优化：预先检查哪些队列有待读取的消息，避免在空队列上浪费时间
                # ✅ 但如果队列需要读取 pending 消息（check_backlog=True），则跳过该队列的 offset 检查
                queues_with_messages = []

                try:
                    # 批量获取已发送和已读取的offset
                    queue_offsets_key = f"{self.redis_prefix}:QUEUE_OFFSETS"
                    read_offsets_key = f"{self.redis_prefix}:READ_OFFSETS"

                    # 使用pipeline批量获取offset
                    pipe = self.async_redis_client.pipeline()

                    # 获取所有队列的已发送offset
                    for q in all_queues:
                        # 从队列名中提取实际的队列名（去掉前缀）
                        actual_queue = q.replace(f"{self.redis_prefix}:QUEUE:", "")
                        pipe.hget(queue_offsets_key, actual_queue)

                    # 提取 task_name（从 group_name 中）
                    task_name = group_name.split(':')[-1]

                    # 获取所有队列的已读取offset
                    for q in all_queues:
                        actual_queue = q.replace(f"{self.redis_prefix}:QUEUE:", "")
                        # field 格式：队列名（含优先级）:任务名
                        field = f"{actual_queue}:{task_name}"
                        pipe.hget(read_offsets_key, field)

                    results = await pipe.execute()

                    # 分析结果，确定哪些队列有待读取的消息
                    half_len = len(all_queues)
                    for i, q in enumerate(all_queues):
                        # ✅ 如果该队列需要读取 pending 消息，直接加入列表，跳过 offset 检查
                        if check_backlog.get(q, False):
                            queues_with_messages.append(q)
                            logger.debug(f"Queue {q} needs to read pending messages, skipping offset check")
                            continue

                        sent_offset = results[i]  # 已发送的offset
                        read_offset = results[half_len + i]  # 已读取的offset

                        # 转换为整数
                        sent = int(sent_offset) if sent_offset else 0
                        read = int(read_offset) if read_offset else 0

                        # 如果已发送的offset大于已读取的offset，说明有消息待读取
                        if sent > read:
                            queues_with_messages.append(q)
                            logger.debug(f"Queue {q} has {sent - read} unread messages (sent={sent}, read={read})")

                    # 如果没有队列有消息，记录下来（不再使用原始队列列表避免空读）
                    if not queues_with_messages:
                        logger.debug("No queues have unread messages, will wait for new messages")

                except Exception as e:
                    # 出错时回退到原始逻辑
                    logger.debug(f"Failed to check queue offsets: {e}")
                    queues_with_messages = all_queues
                
                # print(f'{queues_with_messages=}')
                # 按优先级顺序读取有消息的队列
                for q in queues_with_messages:
                    if messages_needed <= 0:
                        break  # 已经读取足够的消息
                    
                    q_bytes = q.encode() if isinstance(q, str) else q
                    # 针对具体队列检查是否需要读取历史消息
                    if check_backlog.get(q, True):
                        myid = lastid.get(q, "0-0")
                    else:
                        myid = ">"
                    myid_bytes = myid.encode() if isinstance(myid, str) else myid
                    
                    try:
                        # print(f'{myid_bytes=} {consumer_name=} {check_backlog=} {q_bytes=}')
                        # 所有队列（包括优先级队列）都使用基础队列的 group_name
                        # 从当前优先级队列读取（最多读取messages_needed个）
                        q_messages = await self.async_binary_redis_client.xreadgroup(
                            groupname=group_name,
                            consumername=consumer_name,
                            streams={q_bytes: myid_bytes},
                            count=messages_needed,  # 只读取需要的数量
                            block=100  # 非阻塞
                        )
                        if q_messages:
                            logger.info(f"Read messages from {q}: {len(q_messages[0][1]) if q_messages else 0} messages")
                            # if check_backlog.get(q, True):
                            #     print(f'先处理历史消息：{q_bytes=} {group_name=} {q_messages=}')
                            # 记录从哪个队列读取的
                            messages.extend(q_messages)
                            messages_read = len(q_messages[0][1]) if q_messages else 0
                            messages_needed -= messages_read
                            
                            # 如果高优先级队列还有消息，继续从该队列读取
                            # 直到该队列空了或者达到prefetch限制
                            if messages_read > 0 and messages_needed > 0:
                                # 该队列可能还有更多消息，下次循环继续优先从这个队列读
                                # 但现在先处理已读取的消息
                                break  # 跳出for循环，处理已有消息
                            
                    except Exception as e:
                        if "NOGROUP" in str(e):
                            # consumer group 不存在（可能是 Redis 被清空了），重新创建
                            logger.warning(f"NOGROUP error for queue {q}, recreating consumer group...")
                            try:
                                # 为队列创建 consumer group（共享基础队列的 group_name）
                                await self._ensure_consumer_group_and_record_info(
                                    q, task_name, consumer_name, base_group_name=group_name
                                )
                                logger.info(f"Recreated consumer group for queue {q}")

                                # 重新初始化这个队列的 lastid 和 check_backlog
                                lastid[q] = "0"
                                check_backlog[q] = True

                                # 确保这个队列在 all_queues 中（可能因 Redis 清空而丢失）
                                if q not in all_queues:
                                    all_queues.append(q)
                                    # 同时更新 priority_queues（如果是优先级队列）
                                    if q != prefixed_queue and q not in priority_queues:
                                        priority_queues.append(q)
                                        logger.info(f"Re-added queue {q} to all_queues after NOGROUP recovery")
                            except Exception as recreate_error:
                                logger.error(f"Failed to recreate consumer group for {q}: {recreate_error}")
                        else:
                            logger.debug(f"Error reading from queue {q}: {e}")
                        continue
    
                
                try:
                    # logger.debug(f'{group_name=} {consumer_name=} {block_time=}')
                    consecutive_errors = 0
                    # if check_backlog and messages:
                    #     logger.debug(f'先消费之前的消息 {group_name=} ')
                    # logger.debug(f'{check_backlog=} {messages=}')
                    
                    # 上报已投递的offset（用于积压监控）
                    try:
                        from jettask.utils.stream_backlog import report_delivered_offset
                        # 对每个stream的消息上报offset
                        for msg in messages:
                            stream_name = msg[0]
                            if isinstance(stream_name, bytes):
                                stream_name = stream_name.decode('utf-8')
                            # 提取队列名（去掉前缀）
                            queue_name = stream_name.replace(f"{self.redis_prefix}:STREAM:", "")
                            await report_delivered_offset(
                                self.async_redis_client,
                                self.redis_prefix,
                                queue_name,
                                group_name,
                                [msg]
                            )
                    except Exception as e:
                        # 监控失败不影响主流程
                        logger.debug(f"Failed to report delivered offset: {e}")
                    
                    # 收集需要跳过的消息ID
                    skip_message_ids = []
                    
                    # 用于记录每个队列的最大offset（批量更新）
                    max_offsets_per_queue = {}
                    
                    for message in messages:
                        # print(f'{message=}')
                        # message[0]是stream名称，message[1]是消息列表
                        stream_name = message[0]
                        if isinstance(stream_name, bytes):
                            stream_name = stream_name.decode('utf-8')
                        
                        # 根据这个具体队列的消息数量，更新该队列的check_backlog状态
                        if len(message[1]) == 0:
                            # 这个队列没有历史消息了，下次读取最新消息
                            check_backlog[stream_name] = False
                        
                        for event in message[1]:
                            event_id = event[0]
                            # 更新对应队列的lastid
                            lastid[stream_name] = event_id
                            # 将bytes类型的event_id转换为字符串
                            if isinstance(event_id, bytes):
                                event_id = event_id.decode('utf-8')
                            event_data = event[1]
                            
                            # 解析消息内容，决定是否处理
                            should_process = True
                            
                            try:
                                # 解析data字段中的消息
                                if b'data' in event_data or 'data' in event_data:
                                    data_field = event_data.get(b'data') or event_data.get('data')
                                    
                                    # 直接解析二进制数据，不需要解码
                                    parsed_data = loads_str(data_field)

                                    # 跳过延迟任务（延迟任务由延迟扫描器处理）
                                    # 但如果任务已到期，或者正在从 pending 恢复，则应该处理
                                    if parsed_data.get('is_delayed') == 1:
                                        # 检查是否已到期
                                        execute_at = parsed_data.get('execute_at')
                                        current_time = time.time()

                                        if execute_at and execute_at > current_time:
                                            # 未到期，跳过（由Scanner处理）
                                            should_process = False
                                            continue

                                        # 已到期或无execute_at字段，继续处理
                                        # 这种情况可能是：
                                        # 1. 延迟任务已到期，正在被执行
                                        # 2. 从 pending 恢复的已到期任务
                                        logger.debug(f"Processing expired delayed task {event_id}")
                                    
                                    # 每个task都有独立的consumer group
                                    # 检查消息是否指定了目标task（用于精确路由）
                                    target_tasks = parsed_data.get('_target_tasks', None)
                                    if target_tasks and task_name not in target_tasks:
                                        # 这个消息指定了其他task处理
                                        should_process = False
                                    
                                    if should_process:
                                        # 添加task_name到数据中（用于执行器识别任务）
                                        parsed_data['_task_name'] = task_name
                                        
                                        # 提取offset字段（如果存在）
                                        offset_field = event_data.get(b'offset') or event_data.get('offset')
                                        message_offset = None
                                        if offset_field:
                                            # 将offset添加到parsed_data中
                                            if isinstance(offset_field, bytes):
                                                offset_field = offset_field.decode('utf-8')
                                            parsed_data['offset'] = offset_field
                                            try:
                                                message_offset = int(offset_field)
                                            except (ValueError, TypeError):
                                                pass
                                        
                                        # 更新event_data
                                        event_data.clear()
                                        for key, value in parsed_data.items():
                                            event_data[key] = value
                                        
                                        # 收集每个队列的最大offset（不要每条消息都记录）
                                        if message_offset is not None:
                                            # 从stream_name提取实际的队列名
                                            actual_queue_name = stream_name.replace(f"{self.redis_prefix}:QUEUE:", "")
                                            # 更新该队列的最大offset
                                            if actual_queue_name not in max_offsets_per_queue:
                                                max_offsets_per_queue[actual_queue_name] = message_offset
                                            else:
                                                max_offsets_per_queue[actual_queue_name] = max(max_offsets_per_queue[actual_queue_name], message_offset)
                                        
                                        logger.debug(f"Task {task_name} will process message {event_id}")
                                else:
                                    # 没有data字段，跳过消息
                                    should_process = False
                            except Exception as e:
                                logger.error(f"Task {task_name}: Error parsing message data: {e}")
                            
                            if should_process:
                                # 处理消息 - 消息会被放入队列，由执行器处理并ACK
                                # 使用消息体中的实际队列名（可能包含优先级）
                                actual_queue = event_data.get('queue', queue)

                                # 统一 group_name 架构：所有队列（包括优先级队列）使用同一个 consumer name
                                # 不再需要为优先级队列添加后缀
                                result = self._process_message_common(
                                    event_id, event_data, actual_queue, task_event_queue,
                                    is_async=True, consumer_name=consumer_name, group_name=group_name
                                )
                                if isinstance(result, tuple) and result[0] == 'async_put':
                                    await self._async_put_task(task_event_queue, result[1])
                                    logger.debug(f"Put task {event_id} into task_event_queue")
                                # 注意：这里不ACK，由执行器在处理完成后ACK
                            else:
                                # 不属于当前task的消息，收集起来批量ACK
                                skip_message_ids.append(event_id)
                            
                    
                    # 批量ACK不需要的消息（所有队列使用同一个 group_name）
                    if skip_message_ids:
                        group_name_bytes = group_name.encode() if isinstance(group_name, str) else group_name
                        for q in all_queues:
                            q_bytes = q.encode() if isinstance(q, str) else q
                            try:
                                await self.async_binary_redis_client.xack(q_bytes, group_name_bytes, *skip_message_ids)
                            except:
                                pass  # 忽略ACK错误
                        logger.debug(f"Task {task_name} batch ACKed {len(skip_message_ids)} skipped messages")

                    # 批量更新每个队列的最大已读取offset（所有队列使用同一个 group_name）
                    if max_offsets_per_queue:
                        for queue_name, max_offset in max_offsets_per_queue.items():
                            asyncio.create_task(self._update_read_offset(queue_name, group_name, max_offset))
                        logger.debug(f"Updated read offsets for {len(max_offsets_per_queue)} queues")
                        
                except Exception as e:
                    error_msg = str(e)
                    # import traceback
                    # traceback.print_exc()
                    logger.error(f"Error in task listener {task_name}: {e}")
                    
                    # 特殊处理：如果是NOGROUP错误，尝试重新创建consumer group
                    if "NOGROUP" in error_msg:
                        logger.warning(f"Detected NOGROUP error for {task_name}, attempting to recreate consumer groups...")
                        try:
                            # 为所有队列创建consumer group并记录group_info（使用统一方法）
                            for q in all_queues:
                                await self._ensure_consumer_group_and_record_info(q, task_name, consumer_name)
                            logger.info(f"Recreated consumer groups for {len(all_queues)} queues for task {task_name}")

                            # 重新初始化所有队列的 lastid 和 check_backlog
                            for q in all_queues:
                                lastid[q] = "0"
                                check_backlog[q] = True

                            # 重新创建成功，重置错误计数器
                            consecutive_errors = 0
                            continue
                        except Exception as create_error:
                            logger.error(f"Failed to recreate consumer groups for {task_name}: {create_error}")
                    
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        logger.error(f"Too many errors for task {task_name}, restarting...")
                        consecutive_errors = 0
                    await asyncio.sleep(min(consecutive_errors, 5))
        
        logger.debug(f"Starting event listeners for queues: {self.queues}")
        tasks = []
        
        if not (self.app and hasattr(self.app, '_tasks_by_queue')):
            raise RuntimeError("No app or tasks registered, cannot start listeners")
        
        # 为每个队列注册延迟任务回调
        async def handle_expired_tasks(queue: str, tasks: list):
            """处理到期的延迟任务"""
            if tasks:
                async with self._delayed_tasks_locks[queue]:
                    self._delayed_tasks_lists[queue].extend(tasks)

        for queue in self.queues:
            # 创建队列专用的回调函数
            import functools
            callback = functools.partial(handle_expired_tasks, queue)
            self.delayed_scanner.register_callback(queue, callback)

        # 启动延迟消息扫描器
        await self.delayed_scanner.start(self.queues)
        logger.info(f"Delayed message scanner started for queues: {self.queues}")
        
        # 为每个队列启动离线worker处理器（带自动重启）
        # 包括优先级队列
        all_recovery_queues = set(self.queues)
        for base_queue in self.queues:
            # 扫描优先级队列
            priority_queues = await self.scan_priority_queues(base_queue)
            for pq in priority_queues:
                if pq != base_queue:  # 不重复添加基础队列
                    all_recovery_queues.add(pq)
        
        # ✅ 在启动离线worker处理器之前，先触发一次"自我恢复"
        # 这是为了处理"复用worker ID"的场景：
        # - Worker复用离线worker ID后，会立即变为在线状态
        # - 但此时该worker之前的pending消息还未恢复
        # - 周期性扫描只查找is_alive=false的worker，会漏掉刚复用的worker
        # - 因此需要在启动时主动恢复"当前worker"的pending消息
        # logger.info("[Recovery] Performing initial self-recovery check on startup...")
        # try:
        #     await self._perform_self_recovery(all_recovery_queues, event_queue)
        # except Exception as e:
        #     logger.error(f"Error during initial self-recovery: {e}", exc_info=True)

        # 为所有队列（包括优先级队列）启动离线worker处理器
        for queue in all_recovery_queues:
            logger.debug(f"Starting offline worker processor for queue: {queue}")
            offline_processor_task = asyncio.create_task(
                self._start_offline_worker_processor_with_restart(queue)  # 移除 event_queue 参数
            )
            tasks.append(offline_processor_task)
            self._background_tasks.append(offline_processor_task)
        
        # # 为每个task创建独立的listener
        for queue in self.queues:
            task_names = self.app._tasks_by_queue.get(queue, [])
            if not task_names:
                raise RuntimeError(f"No tasks registered for queue '{queue}'. Cannot start worker without tasks.")
            
            for task_name in task_names:
                logger.debug(f"Starting listener for task: {task_name} on queue: {queue}")
                task = asyncio.create_task(listen_event_by_task(queue, task_name))
                tasks.append(task)
                self._background_tasks.append(task)
        
        try:
            # 等待所有任务
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            logger.debug("listening_event tasks cancelled, cleaning up...")

            # 停止延迟消息扫描器
            await self.delayed_scanner.stop()

            # 取消所有后台任务
            for task in self._background_tasks:
                if not task.done():
                    task.cancel()
            # 等待所有任务完成（使用return_exceptions=True避免再次抛出异常）
            if self._background_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._background_tasks, return_exceptions=True),
                        timeout=0.2
                    )
                except asyncio.TimeoutError:
                    logger.debug("Some background tasks did not complete in time")
            raise
    
    # 注意：延迟任务扫描逻辑已迁移到 DelayedMessageScanner 独立模块
    # 旧的 _scan_and_load_delayed_tasks_to_list 和 _scan_and_load_delayed_tasks 方法已删除
    
    async def _claim_delayed_tasks(self, queue: str, event_queue: asyncio.Queue, prefetch_multiplier: int):
        """处理延迟队列中的到期任务"""
        try:
            # 检查队列大小，如果已满则不处理
            if event_queue.qsize() >= max(prefetch_multiplier // 2, 1):
                return
            
            current_time = time.time()
            delayed_queue_key = f"{self.redis_prefix}:DELAYED_QUEUE:{queue}"
            consumer_name = self.consumer_manager.get_consumer_name(queue)
            prefixed_queue = self.get_prefixed_queue_name(queue)
            
            # 计算需要获取的任务数量
            count_to_claim = max(1, prefetch_multiplier - event_queue.qsize())
            
            # Lua脚本：原子性地获取到期任务、认领、删除成功认领的任务
            lua_script = """
            local delayed_queue_key = KEYS[1]
            local stream_key = KEYS[2]
            local group_name = KEYS[3]
            local consumer_name = ARGV[1]
            local current_time = ARGV[2]
            local limit = ARGV[3]
            
            -- 获取到期的任务ID（这些是Stream消息ID）
            local expired_tasks = redis.call('ZRANGEBYSCORE', delayed_queue_key, 0, current_time, 'LIMIT', 0, limit)
            
            if #expired_tasks == 0 then
                return {}
            end
            
            local successfully_claimed = {}
            local claimed_messages = {}
            
            -- 尝试认领每个任务
            for i, task_id in ipairs(expired_tasks) do
                -- 先检查消息的pending信息
                local pending_info = redis.call('XPENDING', stream_key, group_name, task_id, task_id, 1)
                
                if #pending_info > 0 then
                    -- pending_info[1] 格式: {id, consumer, idle_time, delivery_count}
                    local idle_time = pending_info[1][3]
                    
                    -- 只认领空闲时间超过1秒的消息（避免认领刚被读取的消息）
                    if idle_time > 1000 then
                        -- 使用XCLAIM认领消息
                        local claim_result = redis.call('XCLAIM', stream_key, group_name, consumer_name, 0, task_id)
                        
                        if #claim_result > 0 then
                            -- 认领成功，记录任务ID
                            table.insert(successfully_claimed, task_id)
                            -- 保存认领到的消息内容
                            for j, msg in ipairs(claim_result) do
                                table.insert(claimed_messages, msg)
                            end
                        end
                    end
                else
                    -- 消息不在pending列表中，可能还没被读取，跳过
                    -- 但保留在ZSET中，等待正常读取
                end
            end
            
            -- 只删除成功认领的任务
            if #successfully_claimed > 0 then
                redis.call('ZREM', delayed_queue_key, unpack(successfully_claimed))
            end
            
            -- 返回认领到的消息
            return claimed_messages
            """
            
            # 注册Lua脚本（如果还没有注册）
            if not hasattr(self, '_atomic_claim_script'):
                self._atomic_claim_script = self.async_redis_client.register_script(lua_script)
            
            # 执行Lua脚本
            try:
                claimed_messages = await self._atomic_claim_script(
                    keys=[delayed_queue_key, prefixed_queue, prefixed_queue],
                    args=[consumer_name, str(current_time), str(count_to_claim)]
                )
                
                if not claimed_messages:
                    return
                    
                # claimed_messages 是嵌套列表，每个元素是 [msg_id, msg_data_fields]
                # 其中 msg_data_fields 是扁平的键值对列表
                for claimed_message in claimed_messages:
                    if isinstance(claimed_message, list) and len(claimed_message) >= 2:
                        msg_id = claimed_message[0]
                        msg_data_fields = claimed_message[1]
                        
                        # 解析消息数据
                        msg_data = {}
                        if isinstance(msg_data_fields, list):
                            for j in range(0, len(msg_data_fields), 2):
                                if j + 1 < len(msg_data_fields):
                                    key = msg_data_fields[j]
                                    value = msg_data_fields[j + 1]
                                    # 保持bytes格式以匹配正常消息处理
                                    if isinstance(key, str):
                                        key = key.encode()
                                    if isinstance(value, str):
                                        value = value.encode()
                                    msg_data[key] = value
                        
                        # 清除延迟标记
                        if b'data' in msg_data:
                            data_field = msg_data.get(b'data')
                            if data_field:
                                try:
                                    # 直接解析二进制数据
                                    parsed_data = loads_str(data_field)
                                    # 清除延迟标记，避免再次被延迟
                                    parsed_data['is_delayed'] = 0
                                    # dumps_str 现在直接返回二进制
                                    updated_data = dumps_str(parsed_data)
                                    msg_data[b'data'] = updated_data
                                except:
                                    pass
                        
                        # 处理消息
                        result = self._process_message_common(
                            msg_id, msg_data, queue, event_queue,
                            is_async=True, consumer_name=consumer_name
                        )
                        if isinstance(result, tuple) and result[0] == 'async_put':
                            await self._async_put_task(event_queue, result[1])
                        
                        logger.debug(f"Claimed and processed delayed task {msg_id} from queue {queue}")
                
                logger.debug(f"Processed {len(claimed_messages)} delayed tasks for queue {queue}")
                
            except Exception as e:
                logger.error(f"Error executing atomic claim script: {e}")
                    
        except Exception as e:
            logger.error(f"Error processing delayed tasks for queue {queue}: {e}")
            # 错误不应该阻塞主流程
    def read_pending(self, groupname: str, queue: str, asyncio: bool = False):
        client = self.get_redis_client(asyncio, binary=True)
        prefixed_queue = self.get_prefixed_queue_name(queue)
        return client.xpending(prefixed_queue, groupname)

    def ack(self, queue, event_id, asyncio: bool = False):
        client = self.get_redis_client(asyncio, binary=True)
        prefixed_queue = self.get_prefixed_queue_name(queue)
        result = client.xack(prefixed_queue, prefixed_queue, event_id)
        # 清理已认领的消息ID
        if event_id in self._claimed_message_ids:
            self._claimed_message_ids.remove(event_id)
        return result
    def _safe_redis_operation(self, operation, *args, max_retries=3, **kwargs):
        """
        安全的Redis操作，带有重试机制

        注意：Redis连接池已配置为无限重试（InfiniteRetry），会自动处理连接失败。
        这里的重试主要用于处理应用层面的临时错误。
        """
        for attempt in range(max_retries):
            try:
                return operation(*args, **kwargs)
            except (redis.exceptions.TimeoutError, redis.exceptions.ConnectionError) as e:
                if attempt == max_retries - 1:
                    logger.error(f"Redis操作失败，已重试{max_retries}次: {e}")
                    raise

                logger.warning(f"Redis操作失败，第{attempt + 1}次重试: {e}")
                # 不需要手动重新创建连接，连接池会自动重试
                time.sleep(min(2 ** attempt, 5))  # 指数退避，最多5秒
    
    def cleanup(self):
        """清理EventPool资源"""
        # 立即设置停止标志，阻止后台任务继续处理
        self._stop_reading = True
        
        # 只有在有实际资源需要清理时才打印日志
        has_active_resources = False
        
        # 检查是否有活跃的消费者管理器
        if hasattr(self, 'consumer_manager') and self.consumer_manager:
            # 检查消费者管理器是否真的有活动
            if hasattr(self.consumer_manager, '_heartbeat_strategy'):
                strategy = self.consumer_manager._heartbeat_strategy
                if strategy and hasattr(strategy, 'consumer_id') and strategy.consumer_id:
                    has_active_resources = True
        
        if has_active_resources:
            logger.debug("Cleaning up EventPool resources...")
            self.consumer_manager.cleanup()
            logger.debug("EventPool cleanup completed")
        else:
            # 静默清理
            if hasattr(self, 'consumer_manager') and self.consumer_manager:
                self.consumer_manager.cleanup()