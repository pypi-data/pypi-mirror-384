"""
简化的离线worker消息恢复模块
"""
import asyncio
import json
import logging
from typing import Dict, List, Optional, Tuple, TYPE_CHECKING
from redis.asyncio.lock import Lock as AsyncLock

import msgpack

if TYPE_CHECKING:
    from jettask.worker.manager import WorkerState

logger = logging.getLogger(__name__)


class OfflineWorkerRecovery:
    """离线worker消息恢复处理器"""

    def __init__(self, async_redis_client, consumer_manager=None, redis_prefix='jettask', worker_prefix='WORKER', queue_formatter=None, queue_registry=None, worker_state: Optional['WorkerState'] = None):
        """
        初始化离线worker消息恢复处理器

        Args:
            async_redis_client: 异步Redis客户端
            consumer_manager: 消费者管理器
            redis_prefix: Redis键前缀
            worker_prefix: Worker键前缀
            queue_formatter: 队列格式化函数
            queue_registry: 队列注册表
            worker_state: WorkerState实例（用于查询Worker状态）
        """
        self.async_redis_client = async_redis_client
        self.consumer_manager = consumer_manager
        self.redis_prefix = redis_prefix
        self.worker_prefix = worker_prefix
        self._stop_recovery = False
        # 队列格式化函数，默认使用 prefix:QUEUE:queue_name 格式
        self.queue_formatter = queue_formatter or (lambda q: f"{self.redis_prefix}:QUEUE:{q}")
        # 通过 consumer_manager 访问 worker_state_manager
        self.worker_state_manager = consumer_manager.app.worker_state_manager if (consumer_manager and hasattr(consumer_manager, 'app') and consumer_manager.app) else None
        # 队列注册表，用于获取优先级队列
        self.queue_registry = queue_registry
        # Worker状态查询器（必须传入）
        self._worker_state: Optional['WorkerState'] = worker_state
        
    async def recover_offline_workers(self,
                                     queue: str,
                                     current_consumer_name: str = None,
                                     event_queue: Optional[asyncio.Queue] = None,
                                     process_message_callback: Optional[callable] = None,
                                     consumer_group_suffix: Optional[str] = None,
                                     event_queue_callback: Optional[callable] = None) -> int:
        """
        恢复指定队列的离线worker的pending消息

        支持优先级队列：
        - 如果 queue_registry 可用，会自动获取基础队列的所有优先级队列并恢复
        - 如果不可用，只恢复指定的队列
        """
        total_recovered = 0
        logger.debug(f'恢复指定队列的离线worker的pending消息: {queue}')

        try:
            # 确定基础队列名（去除优先级后缀）
            base_queue = queue.split(':')[0]

            # 获取需要恢复的所有队列（包括优先级队列）
            queues_to_recover = [queue]

            # 如果 queue_registry 可用，并且是基础队列，获取所有优先级队列
            if self.queue_registry and base_queue == queue:
                try:
                    priority_queues = await self.queue_registry.get_priority_queues_for_base(queue)
                    if priority_queues:
                        logger.debug(f"Found {len(priority_queues)} priority queues for base queue {queue}: {priority_queues}")
                        queues_to_recover.extend(priority_queues)
                    else:
                        logger.debug(f"No priority queues found for base queue {queue}")
                except Exception as e:
                    logger.warning(f"Error getting priority queues for {queue}: {e}, will only recover base queue")

            logger.debug(f"Will recover {len(queues_to_recover)} queue(s): {queues_to_recover}")

            # 只查找一次离线 worker（使用基础队列名，因为 worker 的 queues 字段只存储基础队列）
            offline_workers = await self._find_offline_workers(base_queue)
            if not offline_workers:
                logger.debug(f"No offline workers found for base queue {base_queue}")
                return 0

            logger.info(f"Found {len(offline_workers)} offline workers for base queue {base_queue}, starting recovery...")

            # 对每个离线worker，提前提取 group_infos（使用基础队列）
            workers_with_groups = []
            for worker_key, worker_data in offline_workers:
                group_infos = []
                for key, value in worker_data.items():
                    if key.startswith('group_info:'):
                        try:
                            group_info = json.loads(value)
                            # 使用基础队列名进行比较
                            if group_info.get('queue') == base_queue:
                                group_infos.append(group_info)
                                logger.debug(f"Found group info for base queue {base_queue}: {group_info}")
                        except Exception as e:
                            logger.error(f"Error parsing group_info: {e}")

                workers_with_groups.append((worker_key, worker_data, group_infos))
                logger.info(f"Worker {worker_key} has {len(group_infos)} groups for base queue {base_queue}")

            # 对每个队列（基础队列 + 优先级队列）恢复消息
            for queue_to_recover in queues_to_recover:
                if self._stop_recovery:
                    logger.debug("Stopping recovery due to shutdown signal")
                    break

                logger.info(f"Recovering queue: {queue_to_recover}")

                # 获取当前consumer名称
                consumer_name = current_consumer_name
                if not consumer_name and self.consumer_manager:
                    consumer_name = self.consumer_manager.get_consumer_name(base_queue)

                    # 统一 group_name 架构：所有队列（包括优先级队列）使用同一个 consumer name
                    # 不再需要为优先级队列添加后缀

                if not consumer_name:
                    logger.error(f"Cannot get current consumer name for queue {queue_to_recover}")
                    continue

                logger.info(f"Starting recovery for queue {queue_to_recover} with consumer {consumer_name}")

                # 处理每个离线worker的这个队列的消息（传入预提取的 group_infos）
                for worker_key, worker_data, group_infos in workers_with_groups:
                    if self._stop_recovery:
                        logger.debug("Stopping recovery due to shutdown signal")
                        break

                    logger.info(f"Recovering messages from worker {worker_key} for queue {queue_to_recover}")
                    recovered = await self._recover_worker_messages(
                        queue=queue_to_recover,
                        worker_key=worker_key,
                        worker_data=worker_data,
                        group_infos=group_infos,  # 传入预提取的 group_infos
                        current_consumer_name=consumer_name,
                        event_queue=event_queue,
                        process_message_callback=process_message_callback,
                        consumer_group_suffix=consumer_group_suffix,
                        event_queue_callback=event_queue_callback  # 传入回调函数
                    )

                    total_recovered += recovered

        except Exception as e:
            logger.error(f"Error recovering offline workers for queue {queue}: {e}")
            import traceback
            traceback.print_exc()

        return total_recovered
        
    async def _find_offline_workers(self, queue: str) -> List[Tuple[str, Dict]]:
        """查找指定队列的离线worker

        委托给 WorkerState.find_offline_workers_for_queue() 方法

        注意：worker_state 必须在 OfflineWorkerRecovery 初始化时传入
        """
        if self._worker_state is None:
            raise RuntimeError(
                "WorkerState not provided to OfflineWorkerRecovery. "
                "Please pass worker_state parameter during initialization."
            )

        return await self._worker_state.find_offline_workers_for_queue(
            queue=queue,
            worker_prefix=self.worker_prefix,
            worker_state_manager=self.worker_state_manager
        )
        
    async def _recover_worker_messages(self,
                                      queue: str,
                                      worker_key: str,
                                      worker_data: Dict,
                                      group_infos: List[Dict],
                                      current_consumer_name: str,
                                      event_queue: Optional[asyncio.Queue] = None,
                                      process_message_callback: Optional[callable] = None,
                                      consumer_group_suffix: Optional[str] = None,
                                      event_queue_callback: Optional[callable] = None) -> int:
        """
        恢复单个worker的pending消息

        Args:
            queue: 当前要恢复的队列（可能是基础队列或优先级队列）
            worker_key: Worker的Redis键
            worker_data: Worker的数据
            group_infos: 预提取的group_info列表（已按基础队列过滤）
            current_consumer_name: 当前consumer名称
            event_queue: 事件队列
            process_message_callback: 处理消息的回调
            consumer_group_suffix: Consumer组后缀

        Returns:
            恢复的消息数量
        """
        total_claimed = 0

        try:
            # worker_data 现在已经是解码后的字典
            consumer_id = worker_data.get('consumer_id')

            if not group_infos:
                logger.info(f"No group_info provided for queue {queue} in worker {worker_key}")
                # 即使没有group_info，也要标记为已处理，避免重复扫描
                # 通过 WorkerStateManager 标记消息已转移
                if self.worker_state_manager:
                    worker_id = worker_key.split(':')[-1]
                    await self.worker_state_manager.mark_messages_transferred(worker_id, transferred=True)
                else:
                    await self.async_redis_client.hset(worker_key, 'messages_transferred', 'true')
                return 0

            # 在处理任何group之前，先标记该worker的消息已开始转移
            # 避免其他进程重复处理
            if self.worker_state_manager:
                worker_id = worker_key.split(':')[-1]
                await self.worker_state_manager.mark_messages_transferred(worker_id, transferred=True)
            else:
                await self.async_redis_client.hset(worker_key, 'messages_transferred', 'true')
            logger.info(f"Marked worker {worker_key} as messages_transferred=true")
            
            # 处理每个group_info
            for group_info in group_infos:
                    base_stream_key = group_info.get('stream_key')
                    group_name = group_info.get('group_name')
                    base_offline_consumer_name = group_info.get('consumer_name')
                    task_name = group_info.get('task_name')
                    base_queue = group_info.get('queue')

                    if not all([base_stream_key, group_name, base_offline_consumer_name]):
                        logger.warning(f"Incomplete group_info: {group_info}")
                        continue

                    # 根据当前处理的队列构建正确的 stream_key 和 offline_consumer_name
                    # group_info 中存储的是基础队列的信息（如 robust_bench2）
                    # 如果当前处理的是优先级队列（如 robust_bench2:6），需要添加优先级后缀
                    stream_key = f"{self.redis_prefix}:QUEUE:{queue}"

                    # 构建离线 consumer 的名称
                    # 如果当前处理的是优先级队列，需要添加优先级后缀
                    offline_consumer_name = base_offline_consumer_name
                    # if base_queue and queue != base_queue:
                    #     # 提取优先级后缀（如从 robust_bench2:6 提取 6）
                    #     priority_suffix = queue.rsplit(':', 1)[-1]
                    #     offline_consumer_name = f"{base_offline_consumer_name}:{priority_suffix}"

                    logger.info(f"Recovering task {task_name}: stream={stream_key}, group={group_name}, consumer={offline_consumer_name}")

                    # 跳过自己的consumer，但只有在worker仍然活跃的情况下
                    # 如果worker已经offline（is_alive=false或messages_transferred=true），即使consumer名称相同也应该恢复
                    # 这处理了worker_id被复用的情况
                    is_alive = worker_data.get('is_alive', 'false')
                    if isinstance(is_alive, bytes):
                        is_alive = is_alive.decode('utf-8')
                    is_alive = is_alive.lower() == 'true'

                    messages_transferred = worker_data.get('messages_transferred', 'false')
                    if isinstance(messages_transferred, bytes):
                        messages_transferred = messages_transferred.decode('utf-8')
                    messages_transferred = messages_transferred.lower() == 'true'

                    # 只有在worker活跃且消息未转移时，才跳过同名consumer
                    if current_consumer_name == offline_consumer_name and is_alive and not messages_transferred:
                        logger.info(f"Skipping own active consumer: {offline_consumer_name}")
                        continue
                    elif current_consumer_name == offline_consumer_name:
                        logger.info(f"Recovering same-name consumer from offline worker: {offline_consumer_name} (is_alive={is_alive}, messages_transferred={messages_transferred})")
                    
                    # 使用分布式锁
                    lock_key = f"{self.redis_prefix}:CLAIM:LOCK:{offline_consumer_name}:{group_name}"
                    lock = AsyncLock(
                        self.async_redis_client,
                        lock_key,
                        timeout=30,
                        blocking=False
                    )
                    
                    if not await lock.acquire():
                        logger.info(f"Lock busy for {offline_consumer_name}:{group_name}")
                        continue
                    
                    try:
                        # 获取pending消息数量
                        pending_info = await self.async_redis_client.xpending(
                            stream_key, group_name
                        )
                        logger.info(f"Pending info for {stream_key=} {group_name=} {task_name}: {pending_info=}")

                        total_pending = pending_info.get('pending', 0) if pending_info else 0
                        if total_pending > 0:
                            # 批量处理所有 pending 消息（避免遗漏）
                            batch_size = 100
                            total_claimed_count = 0

                            # 循环直到处理完所有消息
                            while True:
                                # 获取具体的pending消息信息（每次最多 batch_size 条）
                                detailed_pending = await self.async_redis_client.xpending_range(
                                    stream_key, group_name,
                                    min='-', max='+', count=batch_size,
                                    consumername=offline_consumer_name
                                )
                                logger.info(f'{detailed_pending=} {stream_key=} {group_name=} {offline_consumer_name=}')

                                if not detailed_pending:
                                    # 没有更多消息了
                                    break

                                logger.info(f"Found {len(detailed_pending)} pending messages for {task_name} (batch {total_claimed_count // batch_size + 1})")

                                # 批量认领消息
                                message_ids = [msg['message_id'] for msg in detailed_pending]
                                claimed_messages = await self.async_redis_client.xclaim(
                                    stream_key, group_name,
                                    current_consumer_name,
                                    min_idle_time=0,
                                    message_ids=message_ids
                                )

                                if claimed_messages:
                                    logger.info(f"Claimed {len(claimed_messages)} messages for task {task_name} in this batch")
                                    total_claimed_count += len(claimed_messages)

                                    # 获取该任务的 event_queue
                                    # 优先使用 event_queue_callback，其次使用直接传入的 event_queue
                                    task_event_queue = None
                                    if event_queue_callback and task_name:
                                        task_event_queue = event_queue_callback(task_name)
                                    elif event_queue:
                                        task_event_queue = event_queue

                                    # 如果有 event_queue，将消息放入队列
                                    if task_event_queue:
                                        logger.info(f'即将转移 {len(claimed_messages)=} 消息到 {task_name}')
                                        for msg_id, msg_data in claimed_messages:
                                            if isinstance(msg_id, bytes):
                                                msg_id = msg_id.decode('utf-8')

                                            # 解析消息数据
                                            data_field = msg_data.get(b'data') or msg_data.get('data')
                                            if data_field:
                                                try:
                                                    parsed_data = msgpack.unpackb(data_field, raw=False)
                                                    # 添加必要的元数据
                                                    parsed_data['_task_name'] = task_name
                                                    parsed_data['queue'] = queue

                                                    # 构建任务项
                                                    task_item = {
                                                        'queue': queue,
                                                        'event_id': msg_id,
                                                        'event_data': parsed_data,
                                                        'consumer': current_consumer_name,
                                                        'group_name': group_name
                                                    }

                                                    await task_event_queue.put(task_item)
                                                    logger.debug(f"Put recovered message {msg_id} into event_queue for task {task_name}")
                                                except Exception as e:
                                                    logger.error(f"Error processing claimed message: {e}")
                                    else:
                                        logger.warning(f"No event_queue available for task {task_name}, claimed messages will not be executed")

                                    # 更新总计数
                                    total_claimed += len(claimed_messages)

                                    # 如果这批处理的消息数少于 batch_size，说明已经处理完了
                                    if len(detailed_pending) < batch_size:
                                        break
                                else:
                                    # 没有成功 claim 到消息，退出循环
                                    break

                            # 记录总恢复数量
                            if total_claimed_count > 0:
                                logger.info(f"Total claimed {total_claimed_count} messages for {task_name} from {offline_consumer_name}")
                    finally:
                        await lock.release()
            
        except Exception as e:
            import traceback 
            traceback.print_exc()
            logger.error(f"Error recovering messages: {e}")
            
        return total_claimed
        
    async def _get_consumer_groups(self, stream_key: str, suffix: Optional[str] = None) -> List[str]:
        """获取Stream的consumer groups"""
        groups = []
        try:
            # 确保stream_key是字符串类型（如果是bytes会出问题）
            if isinstance(stream_key, bytes):
                stream_key = stream_key.decode('utf-8')
            
            all_groups = await self.async_redis_client.xinfo_groups(stream_key)
            logger.debug(f"Raw groups info for {stream_key}: {all_groups}")
            
            for group_info in all_groups:
                # 二进制Redis客户端返回的字典键是字符串，值是bytes
                group_name = group_info.get('name', b'')
                logger.debug(f"Processing group: {group_info}, group_name type: {type(group_name)}")
                
                # 解码group名称
                if isinstance(group_name, bytes):
                    group_name = group_name.decode('utf-8')
                
                # 过滤空的group名称
                if group_name:
                    if suffix:
                        if group_name.endswith(suffix):
                            groups.append(group_name)
                    else:
                        groups.append(group_name)
                        logger.debug(f"Added group: {group_name}")
        except Exception as e:
            logger.error(f"Error getting consumer groups for {stream_key}: {e}")
        return groups
        
    async def _claim_messages(self, stream_key: str, group_name: str, 
                             old_consumer: str, new_consumer: str) -> List[Tuple[bytes, Dict]]:
        """转移pending消息"""
        all_claimed = []
        last_id = '-'
        
        try:
            # 确保参数是bytes类型
            if isinstance(stream_key, str):
                stream_key = stream_key.encode('utf-8')
            if isinstance(group_name, str):
                group_name = group_name.encode('utf-8')
            
            logger.debug(f"_claim_messages: stream_key={stream_key}, group_name={group_name}, old_consumer={old_consumer}, new_consumer={new_consumer}")
                
            while True:
                # 获取pending消息
                pending_batch = await self.async_redis_client.xpending_range(
                    stream_key, group_name,
                    min=last_id, max='+',
                    count=100
                )
                
                logger.debug(f"Got {len(pending_batch) if pending_batch else 0} pending messages")
                
                if not pending_batch:
                    break
                
                # 过滤出属于旧consumer的消息
                message_ids = []
                for msg in pending_batch:
                    msg_consumer = msg.get('consumer') or msg.get(b'consumer')
                    if isinstance(msg_consumer, bytes):
                        msg_consumer = msg_consumer.decode('utf-8')
                    
                    if msg_consumer == old_consumer:
                        msg_id = msg.get('message_id') or msg.get(b'message_id')
                        message_ids.append(msg_id)
                
                if message_ids:
                    # 使用XCLAIM转移消息
                    logger.debug(f"Claiming {len(message_ids)} messages from {old_consumer} to {new_consumer}")
                    
                    claimed = await self.async_redis_client.xclaim(
                        stream_key, group_name,
                        new_consumer,
                        min_idle_time=0,
                        message_ids=message_ids,
                        force=True
                    )
                    
                    if claimed:
                        all_claimed.extend(claimed)
                
                # 更新游标
                if pending_batch:
                    last_msg_id = pending_batch[-1].get('message_id') or pending_batch[-1].get(b'message_id')
                    if isinstance(last_msg_id, bytes):
                        last_msg_id = last_msg_id.decode('utf-8')
                    # 增加ID以获取下一批
                    parts = last_msg_id.split('-')
                    if len(parts) == 2:
                        last_id = f"{parts[0]}-{int(parts[1]) + 1}"
                    else:
                        break
                else:
                    break
                    
        except Exception as e:
            logger.error(f"Error claiming messages: {e}")
            
        return all_claimed
        
    async def _put_to_event_queue(self, msg_id, msg_data, queue, event_queue, 
                                 consumer, group_name, old_consumer):
        """将转移的消息放入event_queue"""
        try:
            # 解析消息数据
            if b'data' in msg_data:
                event_data = msgpack.unpackb(msg_data[b'data'], raw=False)
            else:
                event_data = msg_data
            
            # 从 group_name 中提取 task_name
            # group_name 的格式是: "jettask:QUEUE:{queue}:{task_name}"
            task_name = None
            if group_name and ':' in group_name:
                parts = group_name.split(':')
                # 查找最后一个非数字部分作为task_name
                for i in range(len(parts) - 1, -1, -1):
                    part = parts[i]
                    # 跳过优先级数字
                    if not part.isdigit() and part not in ['jettask', 'QUEUE', queue]:
                        task_name = part
                        logger.debug(f"Extracted task_name '{task_name}' from group_name '{group_name}'")
                        break
            
            # 如果从group_name提取失败，尝试从consumer名称提取
            if not task_name and ':' in consumer and ':' in group_name:
                # consumer格式可能是: "{consumer_id}:{task_name}" 
                consumer_parts = consumer.split(':')
                if len(consumer_parts) > 1:
                    potential_task = consumer_parts[-1]
                    # 确保不是优先级数字
                    if not potential_task.isdigit():
                        task_name = potential_task
                        logger.debug(f"Extracted task_name '{task_name}' from consumer '{consumer}'")
            
            # 如果还是没有task_name，检查event_data中是否已有
            if not task_name and '_task_name' in event_data:
                task_name = event_data['_task_name']
                logger.debug(f"Using existing _task_name from event_data: '{task_name}'")
            
            # 确保event_data中有_task_name字段
            if task_name:
                event_data['_task_name'] = task_name
                logger.debug(f"Added _task_name '{task_name}' to recovered message")
            else:
                # 如果无法确定task_name，记录警告
                logger.warning(f"Could not determine task_name for recovered message. group_name='{group_name}', consumer='{consumer}'")
            
            # 构建事件
            event = {
                'event_id': msg_id.decode() if isinstance(msg_id, bytes) else msg_id,
                'event_data': event_data,
                'queue': queue,
                'consumer': consumer,
                'group_name': group_name,
                '_recovery': True,
                '_claimed_from': old_consumer
            }
            
            await event_queue.put(event)
            
        except Exception as e:
            logger.error(f"Error putting message to event queue: {e}")
            
    def stop(self):
        """停止恢复处理"""
        self._stop_recovery = True