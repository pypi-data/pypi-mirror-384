"""
任务执行器

负责任务的执行、超时控制、错误处理
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
import traceback
from datetime import datetime

from .task_registry import TaskRegistry, TaskDefinition

logger = logging.getLogger('app')


class TaskExecutor:
    """
    任务执行器

    职责：
    1. 任务执行
    2. 超时控制
    3. 错误处理
    4. 结果存储

    从ExecutorCore提取的纯任务执行逻辑
    """

    def __init__(self,
                 task_registry: TaskRegistry,
                 data_access=None,
                 retry_manager=None):
        """
        初始化任务执行器

        Args:
            task_registry: 任务注册器
            data_access: 数据访问层（可选）
            retry_manager: 重试管理器（可选）
        """
        self.registry = task_registry
        self.data_access = data_access
        self.retry_manager = retry_manager

        logger.debug("TaskExecutor initialized")

    async def execute(self, message: dict) -> Any:
        """
        执行任务

        Args:
            message: 任务消息
                - task_name: 任务名称
                - task_id: 任务ID
                - args: 位置参数
                - kwargs: 关键字参数

        Returns:
            Any: 任务执行结果

        Raises:
            ValueError: 任务不存在
            asyncio.TimeoutError: 任务超时
            Exception: 任务执行错误
        """
        task_name = message.get('task_name')
        task_id = message.get('task_id')
        args = message.get('args', [])
        kwargs = message.get('kwargs', {})

        logger.debug(f"Executing task: {task_name} (id: {task_id})")

        # 获取任务定义
        task_def = self.registry.get(task_name)
        if not task_def:
            error_msg = f"Task {task_name} not found in registry"
            logger.error(error_msg)
            raise ValueError(error_msg)

        # 执行任务（带超时）
        try:
            # 记录开始时间
            start_time = datetime.now()

            # 执行任务
            if asyncio.iscoroutinefunction(task_def.func):
                # 异步任务
                result = await asyncio.wait_for(
                    task_def.func(*args, **kwargs),
                    timeout=task_def.timeout
                )
            else:
                # 同步任务，在线程池中执行
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(None, task_def.func, *args, **kwargs),
                    timeout=task_def.timeout
                )

            # 计算执行时间
            execution_time = (datetime.now() - start_time).total_seconds()

            logger.info(
                f"Task {task_name} (id: {task_id}) completed "
                f"in {execution_time:.2f}s"
            )

            # 保存成功结果
            if self.data_access:
                await self.data_access.save_task_result(
                    task_id=task_id,
                    status='completed',
                    result=result,
                    execution_time=execution_time
                )

            return result

        except asyncio.TimeoutError:
            # 超时处理
            logger.error(
                f"Task {task_name} (id: {task_id}) timeout "
                f"after {task_def.timeout}s"
            )
            await self._handle_timeout(task_id, task_def, message)
            raise

        except Exception as e:
            # 错误处理
            logger.error(
                f"Task {task_name} (id: {task_id}) failed: {e}\n"
                f"{traceback.format_exc()}"
            )
            await self._handle_error(task_id, task_def, message, e)
            raise

    async def _handle_timeout(self,
                             task_id: str,
                             task_def: TaskDefinition,
                             message: dict):
        """
        处理超时

        Args:
            task_id: 任务ID
            task_def: 任务定义
            message: 任务消息
        """
        # 保存超时状态
        if self.data_access:
            await self.data_access.save_task_result(
                task_id=task_id,
                status='timeout',
                result=None,
                error=f"Task timeout after {task_def.timeout}s"
            )

        # 重试逻辑
        if task_def.max_retries > 0 and self.retry_manager:
            current_retry = message.get('retry_count', 0)
            if current_retry < task_def.max_retries:
                logger.info(
                    f"Scheduling retry for task {task_def.name} "
                    f"(attempt {current_retry + 1}/{task_def.max_retries})"
                )
                await self.retry_manager.schedule_retry(
                    task_id=task_id,
                    task_def=task_def,
                    message=message,
                    retry_count=current_retry + 1,
                    delay=task_def.retry_delay
                )

    async def _handle_error(self,
                           task_id: str,
                           task_def: TaskDefinition,
                           message: dict,
                           error: Exception):
        """
        处理错误

        Args:
            task_id: 任务ID
            task_def: 任务定义
            message: 任务消息
            error: 错误对象
        """
        # 保存失败状态
        if self.data_access:
            await self.data_access.save_task_result(
                task_id=task_id,
                status='failed',
                result=None,
                error=str(error),
                traceback=traceback.format_exc()
            )

        # 重试逻辑
        if task_def.max_retries > 0 and self.retry_manager:
            current_retry = message.get('retry_count', 0)
            if current_retry < task_def.max_retries:
                logger.info(
                    f"Scheduling retry for task {task_def.name} "
                    f"(attempt {current_retry + 1}/{task_def.max_retries})"
                )
                await self.retry_manager.schedule_retry(
                    task_id=task_id,
                    task_def=task_def,
                    message=message,
                    retry_count=current_retry + 1,
                    delay=task_def.retry_delay
                )
            else:
                logger.error(
                    f"Task {task_def.name} failed after {task_def.max_retries} retries"
                )

    async def batch_update_status(self, status_updates: List[dict]):
        """
        批量更新任务状态

        Args:
            status_updates: 状态更新列表
                - task_id: 任务ID
                - status: 状态
                - result: 结果（可选）
                - error: 错误信息（可选）
        """
        if not self.data_access:
            logger.warning("No data_access configured, skipping batch status update")
            return

        for update in status_updates:
            try:
                await self.data_access.update_task_status(
                    task_id=update['task_id'],
                    status=update['status'],
                    result=update.get('result'),
                    error=update.get('error')
                )
            except Exception as e:
                logger.error(f"Error updating task status: {e}")

    async def execute_batch(self, messages: List[dict]) -> List[Dict[str, Any]]:
        """
        批量执行任务

        Args:
            messages: 任务消息列表

        Returns:
            List[Dict]: 执行结果列表
                - task_id: 任务ID
                - status: 状态（completed/failed/timeout）
                - result: 结果（可选）
                - error: 错误信息（可选）
        """
        results = []

        # 并发执行所有任务
        tasks = []
        for message in messages:
            task = asyncio.create_task(self._execute_with_result(message))
            tasks.append(task)

        # 等待所有任务完成
        task_results = await asyncio.gather(*tasks, return_exceptions=True)

        # 整理结果
        for i, task_result in enumerate(task_results):
            message = messages[i]
            task_id = message.get('task_id')

            if isinstance(task_result, Exception):
                # 任务失败
                if isinstance(task_result, asyncio.TimeoutError):
                    status = 'timeout'
                    error = 'Task timeout'
                else:
                    status = 'failed'
                    error = str(task_result)

                results.append({
                    'task_id': task_id,
                    'status': status,
                    'result': None,
                    'error': error
                })
            else:
                # 任务成功
                results.append({
                    'task_id': task_id,
                    'status': 'completed',
                    'result': task_result,
                    'error': None
                })

        return results

    async def _execute_with_result(self, message: dict) -> Any:
        """
        执行任务并返回结果（用于批量执行）

        Args:
            message: 任务消息

        Returns:
            Any: 任务执行结果

        Raises:
            Exception: 任务执行错误
        """
        try:
            return await self.execute(message)
        except Exception:
            raise  # 让gather捕获异常
