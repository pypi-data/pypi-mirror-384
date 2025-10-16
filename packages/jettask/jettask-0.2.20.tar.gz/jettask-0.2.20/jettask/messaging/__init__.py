"""
Messaging Module - 消息传递模块
================================

提供统一的消息队列管理、事件池和任务分发功能。

核心组件
--------
- **EventPool**: 事件池核心，负责任务队列管理和消息分发
- **MessageSender**: 消息发送器，支持普通、延迟、优先级消息
- **MessageReader**: 消息读取器，支持消费者组和消息确认
- **DelayedMessageScanner**: 延迟消息扫描器，处理延迟任务
- **QueueRegistry**: 队列注册管理，提供队列发现功能

使用示例
--------
```python
from jettask.messaging import EventPool, MessageSender, MessageReader

# 创建事件池
event_pool = EventPool(
    redis_client=redis_client,
    async_redis_client=async_redis_client,
    queues=['task_queue'],
    redis_prefix='jettask'
)

# 发送消息
sender = MessageSender(async_redis_client, redis_prefix='jettask')
await sender.send_messages('task_queue', [{'task': 'example'}])

# 读取消息
reader = MessageReader(async_redis_client, binary_redis_client, redis_prefix='jettask')
messages = await reader.read_messages('task_queue', 'group1', 'worker1')
```

模块重构历史
------------
- 2025-10-15: Phase 1 & 2 重构完成
  - 从11个文件简化到6个文件
  - 删除未使用的queue_manager、queue_monitor、queue_router等
  - 统一命名：queue_registry → registry, delayed_scanner → scanner
  - 代码量减少29%
"""

from .event_pool import EventPool
from .sender import MessageSender
from .reader import MessageReader
from .scanner import DelayedMessageScanner
from .registry import QueueRegistry

# 向后兼容的别名
DelayQueueScanner = DelayedMessageScanner

__all__ = [
    # 核心组件
    'EventPool',
    'MessageSender',
    'MessageReader',
    'DelayedMessageScanner',
    'QueueRegistry',
    # 向后兼容别名
    'DelayQueueScanner',
]

# 模块版本信息
__version__ = '2.0.0'  # 重构后的新版本
__author__ = 'JetTask Team'
