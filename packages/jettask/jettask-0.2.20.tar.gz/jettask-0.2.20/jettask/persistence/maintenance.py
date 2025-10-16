"""数据库维护模块

负责定期执行数据库维护任务，如ANALYZE等。
"""

import asyncio
import logging
import time
import traceback

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class DatabaseMaintenance:
    """数据库维护处理器

    职责：
    - 定期执行ANALYZE命令更新统计信息
    - 优化查询性能
    """

    def __init__(self, async_session_local: sessionmaker):
        """初始化数据库维护处理器

        Args:
            async_session_local: SQLAlchemy会话工厂
        """
        self.AsyncSessionLocal = async_session_local

        # 维护配置
        self.analyze_interval = 7200  # 每2小时执行一次ANALYZE
        self.last_analyze_time = 0

        self._running = False
        self._maintenance_task = None

    async def start(self):
        """启动维护任务"""
        self._running = True
        self._maintenance_task = asyncio.create_task(self._maintenance_loop())
        logger.debug("DatabaseMaintenance started")

    async def stop(self):
        """停止维护任务"""
        self._running = False

        if self._maintenance_task:
            self._maintenance_task.cancel()
            try:
                await self._maintenance_task
            except asyncio.CancelledError:
                pass

        logger.debug("DatabaseMaintenance stopped")

    async def _maintenance_loop(self):
        """维护循环"""
        while self._running:
            try:
                current_time = time.time()

                # 执行ANALYZE
                if current_time - self.last_analyze_time > self.analyze_interval:
                    async with self.AsyncSessionLocal() as session:
                        logger.debug("Running ANALYZE on tasks and task_runs tables...")
                        await session.execute(text("ANALYZE tasks"))
                        await session.execute(text("ANALYZE task_runs"))
                        await session.commit()
                        logger.debug("ANALYZE completed successfully for both tables")
                        self.last_analyze_time = current_time

                # 每5分钟检查一次
                await asyncio.sleep(300)

            except Exception as e:
                logger.error(f"Error in database maintenance: {e}")
                logger.error(traceback.format_exc())
                await asyncio.sleep(60)
