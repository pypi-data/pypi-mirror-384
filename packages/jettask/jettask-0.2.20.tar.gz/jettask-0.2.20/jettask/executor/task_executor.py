"""
任务执行器

职责：
1. 从事件队列获取消息
2. 执行任务并管理生命周期
3. 限流控制和批处理
"""

import asyncio
import logging
import time
import os
from typing import Set
from collections import deque

from .core import ExecutorCore
from ..worker.lifecycle import WorkerStateManager
from ..utils.rate_limit.manager import RateLimiterManager

logger = logging.getLogger('app')


class TaskExecutor:
    """
    任务执行器 - 负责单个任务类型的执行

    这是真正执行任务的核心组件，无论是在单进程还是多进程模式下。

    职责：
    1. 从 event_queue 获取消息
    2. 应用限流控制
    3. 执行任务
    4. 批处理管道优化
    """

    def __init__(self, event_queue, app, task_name: str, concurrency: int = 100):
        """
        初始化任务执行器

        Args:
            event_queue: asyncio.Queue，接收待执行的消息
            app: Application 实例（或 MinimalApp）
            task_name: 任务名称
            concurrency: 并发数（实际由限流器控制）
        """
        self.event_queue = event_queue
        self.app = app
        self.task_name = task_name
        self.concurrency = concurrency

        # 核心组件
        self.executor_core = ExecutorCore(
            app=app,
            task_name=task_name,
            concurrency=concurrency
        )

        # 活动任务集合
        self._active_tasks: Set[asyncio.Task] = set()

        # Pipeline 配置
        self.max_buffer_size = 5000

        logger.debug(f"TaskExecutor initialized for task '{task_name}'")

    async def initialize(self):
        """
        初始化执行器组件

        在开始执行前调用，初始化限流器、WorkerState 等
        """
        # 确保有 consumer_id
        self.app.consumer_manager._heartbeat_strategy._ensure_consumer_id()
        worker_id = self.app.consumer_manager._heartbeat_strategy.consumer_id
        registry_manager = self.app.consumer_manager

        # 初始化 WorkerStateManager（如果尚未初始化）
        if not self.app.worker_state_manager:
            self.app.worker_state_manager = WorkerStateManager(
                redis_client=self.app.ep.async_redis_client,
                redis_prefix=self.executor_core.prefix,
                event_pool=self.app.ep
            )
            await self.app.worker_state_manager.start_listener()
            logger.debug(f"WorkerStateManager started for worker {worker_id}")

        # 初始化时间同步
        from jettask.utils.time_sync import init_time_sync
        time_sync = await init_time_sync(self.app.ep.async_redis_client)
        logger.debug(f"TimeSync initialized, offset={time_sync.get_offset():.6f}s")

        # 初始化限流器
        self.executor_core.rate_limiter_manager = RateLimiterManager(
            redis_client=self.app.ep.async_redis_client,
            worker_id=worker_id,
            redis_prefix=self.executor_core.prefix,
            registry_manager=registry_manager,
            worker_state_manager=self.app.worker_state_manager
        )
        logger.debug(f"RateLimiterManager initialized for worker {worker_id}")

        # 加载限流配置
        await self.executor_core.rate_limiter_manager.load_config_from_redis()

    async def run(self):
        """
        执行主循环

        持续从 event_queue 获取消息并执行，直到收到停止信号
        """
        logger.info(f"TaskExecutor started for task '{self.task_name}'")

        tasks_batch = []

        try:
            while True:
                # 检查退出信号
                if hasattr(self.app, '_should_exit') and self.app._should_exit:
                    logger.debug(f"TaskExecutor[{self.task_name}] detected shutdown signal")
                    break

                # 检查父进程（防止孤儿进程）
                if hasattr(os, 'getppid') and os.getppid() == 1:
                    logger.warning(f"TaskExecutor[{self.task_name}] parent died, exiting")
                    break

                current_time = time.time()

                # 获取事件（带超时）
                event = None
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    pass

                if event:
                    event.pop("execute_time", None)
                    tasks_batch.append(event)
                    logger.debug(
                        f"[{self.task_name}] Got event: {event.get('event_id', 'unknown')}"
                    )

                # 批量处理任务
                if tasks_batch:
                    await self._process_batch(tasks_batch)
                    tasks_batch.clear()

                # 智能缓冲区管理
                if self._should_flush_buffers(current_time):
                    asyncio.create_task(self.executor_core._flush_all_buffers())

                # 智能休眠
                await self._smart_sleep()

        except asyncio.CancelledError:
            logger.info(f"TaskExecutor[{self.task_name}] cancelled")
        except Exception as e:
            logger.error(f"TaskExecutor[{self.task_name}] error: {e}", exc_info=True)
        finally:
            await self.cleanup()

    async def _process_batch(self, tasks_batch):
        """处理一批任务"""
        for event in tasks_batch:
            event_data = event.get('event_data', {})
            event_task_name = event_data.get("_task_name") or event_data.get("name")

            if not event_task_name:
                logger.error(f"No task_name in event {event.get('event_id')}")
                continue

            # 验证任务名称
            if event_task_name != self.task_name:
                logger.error(
                    f"Task name mismatch: {event_task_name} != {self.task_name}"
                )
                continue

            # 限流控制
            logger.debug(
                f"[{self.task_name}] Acquiring rate limit, event_id={event.get('event_id')}"
            )

            rate_limit_token = await self.executor_core.rate_limiter_manager.acquire(
                task_name=self.task_name,
                timeout=None
            )

            if not rate_limit_token:
                logger.error(f"Failed to acquire token for {self.task_name}")
                continue

            logger.debug(
                f"[{self.task_name}] Acquired token={rate_limit_token}, starting execution"
            )

            self.executor_core.batch_counter += 1

            # 创建任务并自动释放限流许可
            async def execute_with_release(event_data, token):
                try:
                    await self.executor_core.execute_task(**event_data)
                finally:
                    await self.executor_core.rate_limiter_manager.release(
                        self.task_name, task_id=token
                    )

            task = asyncio.create_task(execute_with_release(event, rate_limit_token))
            self._active_tasks.add(task)
            task.add_done_callback(self._active_tasks.discard)

    def _should_flush_buffers(self, current_time: float) -> bool:
        """判断是否需要刷新缓冲区"""
        # 检查缓冲区是否满
        buffer_full = (
            len(self.executor_core.pending_acks) >= self.max_buffer_size or
            len(self.executor_core.status_updates) >= self.max_buffer_size or
            len(self.executor_core.data_updates) >= self.max_buffer_size or
            len(self.executor_core.task_info_updates) >= self.max_buffer_size
        )

        if buffer_full:
            return True

        # 检查是否有待处理数据
        has_pending_data = (
            self.executor_core.pending_acks or
            self.executor_core.status_updates or
            self.executor_core.data_updates or
            self.executor_core.task_info_updates
        )

        if not has_pending_data:
            return False

        # 检查是否超时
        for data_type, config in self.executor_core.pipeline_config.items():
            time_since_flush = current_time - self.executor_core.last_pipeline_flush[data_type]

            if data_type == 'ack' and self.executor_core.pending_acks:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'task_info' and self.executor_core.task_info_updates:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'status' and self.executor_core.status_updates:
                if time_since_flush >= config['max_delay']:
                    return True
            elif data_type == 'data' and self.executor_core.data_updates:
                if time_since_flush >= config['max_delay']:
                    return True

        return False

    async def _smart_sleep(self):
        """智能休眠 - 根据队列状态决定休眠时间"""
        has_events = False

        if isinstance(self.event_queue, deque):
            has_events = bool(self.event_queue)
        elif isinstance(self.event_queue, asyncio.Queue):
            has_events = not self.event_queue.empty()

        if has_events:
            # 有待处理事件，立即继续
            await asyncio.sleep(0)
        else:
            # 无事件，稍作休眠
            has_pending = (
                self.executor_core.pending_acks or
                self.executor_core.status_updates or
                self.executor_core.data_updates or
                self.executor_core.task_info_updates
            )

            if has_pending:
                # 有待刷新的数据，先刷新
                await self.executor_core._flush_all_buffers()

            await asyncio.sleep(0.001)

    async def cleanup(self):
        """清理资源"""
        logger.info(f"TaskExecutor[{self.task_name}] cleaning up")

        # 设置停止标志
        if hasattr(self.app.ep, '_stop_reading'):
            self.app.ep._stop_reading = True

        # 取消活动任务
        if self._active_tasks:
            logger.debug(
                f"TaskExecutor[{self.task_name}] cancelling {len(self._active_tasks)} active tasks"
            )
            for task in self._active_tasks:
                if not task.done():
                    task.cancel()

            if self._active_tasks:
                try:
                    await asyncio.wait_for(
                        asyncio.gather(*self._active_tasks, return_exceptions=True),
                        timeout=0.2
                    )
                except asyncio.TimeoutError:
                    logger.warning(
                        f"TaskExecutor[{self.task_name}] some tasks did not complete in time"
                    )

        # 清理 ExecutorCore
        await self.executor_core.cleanup()

        logger.info(f"TaskExecutor[{self.task_name}] stopped")


__all__ = ['TaskExecutor']
