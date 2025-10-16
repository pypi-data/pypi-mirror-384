"""
统一执行器

整合了单进程和多进程执行模式的统一接口
"""

import asyncio
import multiprocessing
import logging
import os
import time
from collections import deque
from typing import List, Optional

from .core import ExecutionMode, ExecutorCore
from .orchestrator import ProcessConfig, ProcessOrchestrator
from ..worker.lifecycle import WorkerStateManager
from ..utils.rate_limit.manager import RateLimiterManager

logger = logging.getLogger('app')

# Try to use uvloop for better performance
try:
    import uvloop
    uvloop.install()
    logger.debug("Using uvloop for better performance")
except ImportError:
    pass


class UnifiedExecutor:
    """
    统一执行器

    整合AsyncioExecutor和MultiAsyncioExecutor的功能
    支持单进程和多进程两种执行模式

    职责:
    1. 提供统一的执行器接口
    2. 根据模式选择ExecutorCore或ProcessOrchestrator
    3. 管理事件队列和任务分发
    """

    def __init__(self, event_queue, app, concurrency=100,
                 mode: ExecutionMode = ExecutionMode.SINGLE_PROCESS,
                 task_name: str = None):
        """
        初始化统一执行器

        Args:
            event_queue: 事件队列
            app: Application实例
            concurrency: 并发数
            mode: 执行模式
            task_name: 任务名称(单进程模式必需)
        """
        self.event_queue = event_queue
        self.app = app
        self.concurrency = concurrency
        self.mode = mode
        self.task_name = task_name

        # 根据模式初始化核心组件
        if mode == ExecutionMode.SINGLE_PROCESS:
            if not task_name:
                raise ValueError("task_name is required for SINGLE_PROCESS mode")

            self.executor_core = ExecutorCore(
                app=app,
                task_name=task_name,
                concurrency=concurrency
            )
            self.orchestrator = None
            logger.debug(f"UnifiedExecutor initialized in SINGLE_PROCESS mode for task {task_name}")

        elif mode == ExecutionMode.MULTI_PROCESS:
            self.executor_core = None
            self.orchestrator = ProcessOrchestrator(
                app=app,
                num_processes=concurrency
            )
            logger.debug(f"UnifiedExecutor initialized in MULTI_PROCESS mode with {concurrency} processes")

        else:
            raise ValueError(f"Unsupported execution mode: {mode}")

        # 活动任务集合(单进程模式使用)
        self._active_tasks = set()

    def logic(self, *args, **kwargs):
        """
        BaseExecutor接口方法
        在单进程模式下不使用,多进程模式委托给ProcessOrchestrator
        """
        pass

    async def loop(self):
        """主循环 - 单进程模式"""
        if self.mode != ExecutionMode.SINGLE_PROCESS:
            raise RuntimeError("loop() is only for SINGLE_PROCESS mode")

        # 初始化限流器
        self.app.consumer_manager._heartbeat_strategy._ensure_consumer_id()
        worker_id = self.app.consumer_manager._heartbeat_strategy.consumer_id
        registry_manager = self.app.consumer_manager

        if not self.app.worker_state_manager:
            self.app.worker_state_manager = WorkerStateManager(
                redis_client=self.app.ep.async_redis_client,
                redis_prefix=self.executor_core.prefix,
                event_pool=self.app.ep  # 传入 EventPool 实例，启用事件驱动的消息恢复
            )
            await self.app.worker_state_manager.start_listener()
            logger.debug(f"WorkerStateManager started for worker {worker_id}")

        # # 初始化时间同步
        from jettask.utils.time_sync import init_time_sync
        time_sync = await init_time_sync(self.app.ep.async_redis_client)
        logger.debug(f"TimeSync initialized, offset={time_sync.get_offset():.6f}s")

        self.executor_core.rate_limiter_manager = RateLimiterManager(
            redis_client=self.app.ep.async_redis_client,
            worker_id=worker_id,
            redis_prefix=self.executor_core.prefix,
            registry_manager=registry_manager,
            worker_state_manager=self.app.worker_state_manager
        )
        logger.debug(f"RateLimiterManager initialized for worker {worker_id}")

        await self.executor_core.rate_limiter_manager.load_config_from_redis()

        tasks_batch = []
        max_buffer_size = 5000

        try:
            while True:
                # 检查退出信号
                if hasattr(self.app, '_should_exit') and self.app._should_exit:
                    logger.debug("UnifiedExecutor detected shutdown signal")
                    break

                # 检查父进程
                if hasattr(os, 'getppid') and os.getppid() == 1:
                    logger.debug("Parent process died, exiting...")
                    break

                current_time = time.time()

                # 获取事件
                event = None
                try:
                    event = await asyncio.wait_for(self.event_queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    event = None

                if event:
                    event.pop("execute_time", None)
                    tasks_batch.append(event)
                    logger.debug(f"[EVENT] Got event: {event.get('event_id', 'unknown')}, task_name={event.get('event_data', {}).get('_task_name')}")

                # 批量创建任务
                if tasks_batch:
                    for event in tasks_batch:
                        event_data = event.get('event_data', {})
                        event_task_name = event_data.get("_task_name") or event_data.get("name")

                        if not event_task_name:
                            logger.error(f"No task_name in event {event.get('event_id')}")
                            continue

                        # 验证任务名称匹配
                        if event_task_name != self.task_name:
                            logger.error(f"Task name mismatch: {event_task_name} != {self.task_name}")
                            continue

                        # 限流控制
                        logger.debug(f"[TASK] Attempting to acquire rate limit for {self.task_name}, event_id={event.get('event_id')}")
                        rate_limit_token = await self.executor_core.rate_limiter_manager.acquire(
                            task_name=self.task_name,
                            timeout=None
                        )
                        print(f'{rate_limit_token=}')
                        if not rate_limit_token:
                            logger.error(f"Failed to acquire token for {self.task_name}")
                            continue
                        logger.debug(f"[TASK] Successfully acquired rate limit for {self.task_name}, token={rate_limit_token}, starting execution")

                        self.executor_core.batch_counter += 1

                        # 创建任务包装器，在任务完成时自动释放限流许可
                        async def execute_with_release(event_data, token):
                            try:
                                await self.executor_core.execute_task(**event_data)
                            finally:
                                # 无论任务成功还是失败，都释放并发许可
                                await self.executor_core.rate_limiter_manager.release(self.task_name, task_id=token)

                        task = asyncio.create_task(execute_with_release(event, rate_limit_token))
                        self._active_tasks.add(task)
                        task.add_done_callback(self._active_tasks.discard)

                    tasks_batch.clear()

                # 智能缓冲区管理
                buffer_full = (
                    len(self.executor_core.pending_acks) >= max_buffer_size or
                    len(self.executor_core.status_updates) >= max_buffer_size or
                    len(self.executor_core.data_updates) >= max_buffer_size or
                    len(self.executor_core.task_info_updates) >= max_buffer_size
                )

                should_flush_periodic = False
                has_pending_data = (
                    self.executor_core.pending_acks or
                    self.executor_core.status_updates or
                    self.executor_core.data_updates or
                    self.executor_core.task_info_updates
                )

                if has_pending_data:
                    for data_type, config in self.executor_core.pipeline_config.items():
                        time_since_flush = current_time - self.executor_core.last_pipeline_flush[data_type]

                        if data_type == 'ack' and self.executor_core.pending_acks:
                            if time_since_flush >= config['max_delay']:
                                should_flush_periodic = True
                                break
                        elif data_type == 'task_info' and self.executor_core.task_info_updates:
                            if time_since_flush >= config['max_delay']:
                                should_flush_periodic = True
                                break
                        elif data_type == 'status' and self.executor_core.status_updates:
                            if time_since_flush >= config['max_delay']:
                                should_flush_periodic = True
                                break
                        elif data_type == 'data' and self.executor_core.data_updates:
                            if time_since_flush >= config['max_delay']:
                                should_flush_periodic = True
                                break

                if buffer_full or should_flush_periodic:
                    asyncio.create_task(self.executor_core._flush_all_buffers())

                # 智能休眠
                has_events = False
                if isinstance(self.event_queue, deque):
                    has_events = bool(self.event_queue)
                elif isinstance(self.event_queue, asyncio.Queue):
                    has_events = not self.event_queue.empty()

                if has_events:
                    await asyncio.sleep(0)
                else:
                    if has_pending_data:
                        await self.executor_core._flush_all_buffers()
                    await asyncio.sleep(0.001)

        except KeyboardInterrupt:
            logger.debug("UnifiedExecutor received KeyboardInterrupt")
        except Exception as e:
            logger.error(f"UnifiedExecutor loop error: {e}")
        finally:
            await self._cleanup_single_process()

    async def _cleanup_single_process(self):
        """清理单进程模式资源"""
        logger.debug("UnifiedExecutor cleaning up...")

        # 设置停止标志
        if hasattr(self.app.ep, '_stop_reading'):
            self.app.ep._stop_reading = True

        # 取消活动任务
        if self._active_tasks:
            logger.debug(f"Cancelling {len(self._active_tasks)} active tasks...")
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
                    logger.debug("Some tasks did not complete in time")

        # 清理ExecutorCore
        await self.executor_core.cleanup()

        # 清理event_pool
        if hasattr(self.app.ep, 'cleanup'):
            try:
                self.app.ep.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up EventPool: {e}")

        # 标记worker离线
        if self.app.consumer_manager:
            try:
                self.app.consumer_manager.cleanup()
                logger.debug("Worker marked as offline")
            except Exception as e:
                logger.error(f"Error marking worker offline: {e}")

        logger.debug("UnifiedExecutor stopped")

    def start_multi_process(self, queues: List[str], prefetch_multiplier: int = 100, worker_id: str = None, worker_key: str = None):
        """启动多进程模式

        Args:
            queues: 队列列表
            prefetch_multiplier: 预取倍数
            worker_id: Worker ID（主进程生成，子进程复用）
            worker_key: Worker Key（主进程生成，子进程复用）
        """
        if self.mode != ExecutionMode.MULTI_PROCESS:
            raise RuntimeError("start_multi_process() is only for MULTI_PROCESS mode")

        self.orchestrator.start(queues, prefetch_multiplier, worker_id, worker_key)

    def shutdown(self):
        """
        关闭执行器

        根据执行模式调用相应的关闭方法
        """
        if self.mode == ExecutionMode.MULTI_PROCESS:
            if self.orchestrator:
                self.orchestrator.shutdown()
        elif self.mode == ExecutionMode.SINGLE_PROCESS:
            # 单进程模式的清理在 _cleanup_single_process 中处理
            # 这里只是一个占位符，实际清理由事件循环完成
            logger.debug("UnifiedExecutor shutdown called in SINGLE_PROCESS mode")


__all__ = ['UnifiedExecutor']
