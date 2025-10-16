"""
命名空间管理器模块

提供单命名空间和多命名空间的消费者管理
"""

from .multi import NamespaceConsumerProcess
from .unified import UnifiedConsumerManager

__all__ = ['NamespaceConsumerProcess', 'UnifiedConsumerManager']
