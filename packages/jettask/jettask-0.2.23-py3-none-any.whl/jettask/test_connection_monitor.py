#!/usr/bin/env python3
"""
测试 Redis 连接监控功能
"""
import time
import logging
from jettask.utils.db_connector import (
    get_sync_redis_client,
    get_async_redis_client,
    start_connection_monitor,
    stop_connection_monitor,
    print_connection_stats,
)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def test_connection_monitor():
    """测试连接监控功能"""
    print("=" * 80)
    print("测试 Redis 连接监控功能")
    print("=" * 80)

    # 启动监控（间隔10秒，用于测试）
    print("\n1. 启动连接监控（间隔10秒）...")
    start_connection_monitor(interval=10)
    time.sleep(2)

    # 创建一些连接
    print("\n2. 创建同步客户端（文本模式）...")
    sync_client1 = get_sync_redis_client('redis://localhost:6379/0', decode_responses=True)
    time.sleep(1)

    print("\n3. 创建同步客户端（二进制模式）...")
    sync_client2 = get_sync_redis_client('redis://localhost:6379/0', decode_responses=False)
    time.sleep(1)

    print("\n4. 创建异步客户端（文本模式）...")
    async_client1 = get_async_redis_client('redis://localhost:6379/0', decode_responses=True)
    time.sleep(1)

    print("\n5. 创建异步客户端（二进制模式）...")
    async_client2 = get_async_redis_client('redis://localhost:6379/0', decode_responses=False)
    time.sleep(1)

    # 手动打印一次统计信息
    print("\n6. 手动打印连接统计信息...")
    print_connection_stats()

    # 测试客户端复用
    print("\n7. 测试客户端复用（获取相同URL的客户端）...")
    sync_client3 = get_sync_redis_client('redis://localhost:6379/0', decode_responses=True)
    print(f"   客户端是否相同: {sync_client1 is sync_client3}")

    # 等待一个监控周期
    print("\n8. 等待监控线程自动输出（10秒）...")
    time.sleep(12)

    # 停止监控
    print("\n9. 停止连接监控...")
    stop_connection_monitor()
    time.sleep(1)

    print("\n" + "=" * 80)
    print("测试完成！")
    print("=" * 80)


if __name__ == "__main__":
    test_connection_monitor()
