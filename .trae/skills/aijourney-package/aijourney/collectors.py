"""
采集器模块

提供基础采集器类和装饰器
"""

from .core import BaseCollector, register_collector, get_all_collectors

__all__ = ["BaseCollector", "register_collector", "get_all_collectors"]
