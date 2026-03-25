"""
SumAll 采集器模块

自动导入并注册所有采集器
"""

from .base import (
    BaseCollector,
    SessionData,
    Message,
    register_collector,
    get_collector,
    get_all_collectors,
    get_all_collector_instances,
    clear_collectors,
)

# 导入所有采集器（触发注册）
from .claude_code import ClaudeCodeCollector
from .codebuddy import CodeBuddyCollector
from .vscode import VSCodeCollector
from .idea import IDEACollector

__all__ = [
    # 基类
    "BaseCollector",
    "SessionData",
    "Message",
    # 注册函数
    "register_collector",
    "get_collector",
    "get_all_collectors",
    "get_all_collector_instances",
    "clear_collectors",
    # 采集器
    "ClaudeCodeCollector",
    "CodeBuddyCollector",
    "VSCodeCollector",
    "IDEACollector",
]
