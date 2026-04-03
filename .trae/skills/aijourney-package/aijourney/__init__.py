"""
AIJourney Skill Package

一个独立的Skill工具包，用于自动采集AI编程工具会话数据并生成工作日报。
"""

__version__ = "1.0.0"
__author__ = "AIJourney Team"

from .core import AIJourneySkill, SessionData
from .collectors import (
    BaseCollector,
    register_collector,
    get_all_collectors,
)

__all__ = [
    "AIJourneySkill",
    "SessionData",
    "BaseCollector",
    "register_collector",
    "get_all_collectors",
]
