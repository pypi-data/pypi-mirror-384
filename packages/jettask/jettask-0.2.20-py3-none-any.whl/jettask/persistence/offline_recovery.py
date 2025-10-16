"""离线Worker恢复模块

负责恢复离线PG_CONSUMER的消息，包括TASK_CHANGES流的离线消息。
"""

import asyncio
import logging
import msgpack
import traceback
from typing import Optional

from redis.asyncio import Redis
from jettask.worker.recovery import OfflineWorkerRecovery

logger = logging.getLogger(__name__)


class OfflineRecoveryHandler:
    """离线Worker恢复处理器

    职责：
    - 启动离线worker恢复服务
    - 恢复TASK_CHANGES stream的离线消息
    - 处理恢复的消息并更新任务状态
    """

    def __init__(
        self,
        redis_client: Redis,
        redis_prefix: str,
        consumer_id: str,
        task_updater: 'TaskUpdater'  # 类型提示使用字符串避免循环导入
    ):
        """初始化离线恢复处理器

        Args:
            redis_client: Redis异步客户端
            redis_prefix: Redis键前缀
            consumer_id: 消费者ID
            task_updater: 任务更新器实例（用于处理恢复的消息）
        """
        self.redis_client = redis_client
        self.redis_prefix = redis_prefix
        self.consumer_id = consumer_id
        self.task_updater = task_updater

        # 创建 WorkerState 实例（用于查询 Worker 状态）
        from jettask.worker.manager import WorkerState
        self.worker_state = WorkerState(
            redis_client=None,  # persistence 模块使用异步客户端
            async_redis_client=redis_client,
            redis_prefix=redis_prefix
        )

        # 创建离线worker恢复器（用于恢复TASK_CHANGES stream的离线消息）
        # 注意：这里不传入consumer_manager，因为需要在start时初始化
        self.offline_recovery = None

        self._running = False
        self._recovery_task = None

    def set_consumer_manager(self, consumer_manager):
        """设置ConsumerManager（延迟初始化）

        Args:
            consumer_manager: ConsumerManager实例
        """
        self.offline_recovery = OfflineWorkerRecovery(
            async_redis_client=self.redis_client,
            redis_prefix=self.redis_prefix,
            worker_prefix='PG_CONSUMER',  # 使用PG_CONSUMER前缀
            consumer_manager=consumer_manager,
            worker_state=self.worker_state  # 传入在 __init__ 中创建的 WorkerState
        )

    async def start(self):
        """启动离线恢复服务"""
        if not self.offline_recovery:
            logger.warning("OfflineRecovery not initialized, please call set_consumer_manager first")
            return

        self._running = True
        self._recovery_task = asyncio.create_task(self._recovery_loop())
        logger.debug("OfflineRecoveryHandler started")

    async def stop(self):
        """停止离线恢复服务"""
        self._running = False

        if self.offline_recovery:
            self.offline_recovery.stop()  # stop() 不是异步方法

        if self._recovery_task:
            self._recovery_task.cancel()
            try:
                await self._recovery_task
            except asyncio.CancelledError:
                pass

        logger.debug("OfflineRecoveryHandler stopped")

    async def _recovery_loop(self):
        """离线恢复循环"""
        while self._running:
            try:
                total_recovered = 0

                # 恢复TASK_CHANGES stream的消息
                recovered = await self._recover_task_changes_offline_messages()
                if recovered > 0:
                    logger.debug(f"Recovered {recovered} TASK_CHANGES messages")
                    total_recovered += recovered

                if total_recovered > 0:
                    logger.debug(f"Total recovered {total_recovered} messages in this cycle")

                # 每1秒扫描一次
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"Error in offline recovery service: {e}")
                await asyncio.sleep(10)

    async def _recover_task_changes_offline_messages(self) -> int:
        """恢复TASK_CHANGES stream的离线消息"""
        # 使用 OfflineWorkerRecovery 的标准接口
        try:
            # 为TASK_CHANGES定义自定义的队列格式化器
            def task_changes_formatter(queue):
                # 对于TASK_CHANGES，直接返回stream key（不加QUEUE:前缀）
                if queue == 'TASK_CHANGES':
                    return f"{self.redis_prefix}:TASK_CHANGES"
                else:
                    return f"{self.redis_prefix}:QUEUE:{queue}"

            # 创建专门用于TASK_CHANGES的恢复器
            task_changes_recovery = OfflineWorkerRecovery(
                async_redis_client=self.redis_client,
                redis_prefix=self.redis_prefix,
                worker_prefix='PG_CONSUMER',
                queue_formatter=task_changes_formatter,
                worker_state=self.worker_state  # 传入在 __init__ 中创建的 WorkerState
            )

            # 调用标准的恢复方法
            # TASK_CHANGES作为队列名传入，会被正确处理
            recovered = await task_changes_recovery.recover_offline_workers(
                queue='TASK_CHANGES',  # 这个队列名会用于查找离线worker
                current_consumer_name=self.consumer_id,
                process_message_callback=self._process_recovered_task_change_v2
            )

            return recovered

        except Exception as e:
            logger.error(f"Error in recover_task_changes_offline_messages: {e}")
            return 0

    async def _process_recovered_task_change_v2(self, msg_id, msg_data, queue, consumer_id):
        """处理恢复的TASK_CHANGES消息（符合OfflineWorkerRecovery的回调接口）"""
        try:
            logger.debug(f'处理恢复的TASK_CHANGES消息（符合OfflineWorkerRecovery的回调接口） {msg_data=}')
            # 解析消息 - 现在使用task_id而不是event_id
            if b'task_id' in msg_data:
                # 使用msgpack解压task_id
                compressed_task_id = msg_data[b'task_id']
                task_key = msgpack.unpackb(compressed_task_id)
                task_key = task_key.decode('utf-8') if isinstance(task_key, bytes) else str(task_key)

                # 从完整的task_key格式提取stream_id
                # 格式: namespace:TASK:stream_id:queue_name
                stream_id = None
                if ':TASK:' in task_key:
                    parts = task_key.split(':TASK:')
                    if len(parts) == 2:
                        # 再从右边部分提取stream_id
                        right_parts = parts[1].split(':')
                        if right_parts:
                            stream_id = right_parts[0]  # 提取stream_id

                if stream_id:
                    logger.debug(f"Processing recovered TASK_CHANGES message: {stream_id} from offline worker {consumer_id}")
                    # 更新任务状态 - 传入(stream_id, task_key)元组
                    # 使用task_updater的内部方法
                    await self.task_updater._update_tasks_by_event([(stream_id, task_key)])
                else:
                    logger.warning(f"Cannot extract stream_id from task_key: {task_key}")

                # ACK消息
                change_stream_key = f"{self.redis_prefix}:TASK_CHANGES"
                consumer_group = f"{self.redis_prefix}_changes_consumer"
                await self.redis_client.xack(change_stream_key, consumer_group, msg_id)

        except Exception as e:
            logger.error(f"Error processing recovered task change {msg_id}: {e}")
            logger.error(traceback.format_exc())
