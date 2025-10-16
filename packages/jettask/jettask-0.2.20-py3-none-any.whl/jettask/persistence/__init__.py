"""PostgreSQL Consumer模块

从Redis队列消费任务并持久化到PostgreSQL数据库。

模块结构：
- consumer.py: 主消费者类（协调器）
- backlog_monitor.py: Stream积压监控
- task_updater.py: 任务状态更新
- offline_recovery.py: 离线Worker恢复
- task_persistence.py: 任务数据持久化
- queue_discovery.py: 队列发现
- message_consumer.py: 消息消费
- maintenance.py: 数据库维护

使用示例：
    from jettask.services.pg_consumer import PostgreSQLConsumer, run_pg_consumer, main

    # 使用Consumer类
    consumer = PostgreSQLConsumer(pg_config, redis_config)
    await consumer.start()

    # 或直接运行
    await run_pg_consumer(pg_config, redis_config)

    # 或使用main函数（从环境变量读取配置）
    main()
"""

import asyncio
import logging
import os

from jettask.webui.config import PostgreSQLConfig, RedisConfig
# ConsumerStrategy 已移除，现在只使用 HEARTBEAT 策略

from .consumer import PostgreSQLConsumer

logger = logging.getLogger(__name__)

# 导出主要类和函数
__all__ = [
    'PostgreSQLConsumer',
    'run_pg_consumer',
    'main'
]


async def run_pg_consumer(
    pg_config: PostgreSQLConfig,
    redis_config: RedisConfig,
    # consumer_strategy 参数已移除，现在只使用 HEARTBEAT 策略
):
    """运行PostgreSQL消费者

    Args:
        pg_config: PostgreSQL配置
        redis_config: Redis配置
        consumer_strategy: 消费者策略
    """
    # 从环境变量读取监控配置
    enable_backlog_monitor = os.getenv('JETTASK_ENABLE_BACKLOG_MONITOR', 'true').lower() == 'true'
    backlog_monitor_interval = int(os.getenv('JETTASK_BACKLOG_MONITOR_INTERVAL', '60'))

    logger.info(f"Backlog monitor config: enabled={enable_backlog_monitor}, interval={backlog_monitor_interval}s")

    consumer = PostgreSQLConsumer(
        pg_config,
        redis_config,
        consumer_strategy=consumer_strategy,
        enable_backlog_monitor=enable_backlog_monitor,
        backlog_monitor_interval=backlog_monitor_interval
    )

    try:
        await consumer.start()
        while True:
            await asyncio.sleep(1)

    except KeyboardInterrupt:
        logger.debug("Received interrupt signal")
    finally:
        await consumer.stop()


def main():
    """主入口函数（从环境变量读取配置）"""
    from dotenv import load_dotenv

    load_dotenv()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    pg_config = PostgreSQLConfig(
        host=os.getenv('JETTASK_PG_HOST', 'localhost'),
        port=int(os.getenv('JETTASK_PG_PORT', '5432')),
        database=os.getenv('JETTASK_PG_DB', 'jettask'),
        user=os.getenv('JETTASK_PG_USER', 'jettask'),
        password=os.getenv('JETTASK_PG_PASSWORD', '123456'),
    )

    redis_config = RedisConfig(
        host=os.getenv('REDIS_HOST', 'localhost'),
        port=int(os.getenv('REDIS_PORT', '6379')),
        db=int(os.getenv('REDIS_DB', '0')),
        password=os.getenv('REDIS_PASSWORD'),
    )

    # 使用 HEARTBEAT 策略（唯一支持的策略）
    logger.debug("Using consumer strategy: HEARTBEAT")

    asyncio.run(run_pg_consumer(pg_config, redis_config))


if __name__ == '__main__':
    main()
