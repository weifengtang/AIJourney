"""
基础采集器模块

定义统一的采集器接口和数据结构
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Any


@dataclass
class Message:
    """消息数据结构"""
    role: str  # user, assistant, system
    content: str
    timestamp: datetime


@dataclass
class SessionData:
    """会话数据结构"""
    session_id: str
    source: str  # 数据源标识：claude_code, codebuddy, git_commits
    project_path: str
    start_time: datetime
    end_time: datetime
    title: str
    summary: str
    messages: List[Message]
    files_modified: List[str]
    tokens_input: int
    tokens_output: int


class BaseCollector(ABC):
    """基础采集器抽象类"""
    
    name: str = "base"
    version: str = "1.0.0"
    priority: int = 50  # 优先级，数值越小优先级越高
    
    @abstractmethod
    def get_data_path(self) -> Path:
        """获取数据源路径"""
        pass
    
    @abstractmethod
    def collect(self, target_date: date) -> List[SessionData]:
        """
        采集指定日期的会话数据
        
        Args:
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        pass
    
    def validate(self) -> bool:
        """
        验证数据源是否可用
        
        Returns:
            是否可用
        """
        data_path = self.get_data_path()
        return data_path.exists()
    
    def get_name(self) -> str:
        """获取采集器名称"""
        return self.name
    
    def get_version(self) -> str:
        """获取采集器版本"""
        return self.version
    
    def get_priority(self) -> int:
        """获取采集器优先级"""
        return self.priority


# 采集器注册表
_collectors: Dict[str, BaseCollector] = {}


def register_collector(cls):
    """
    装饰器：注册采集器类
    
    Args:
        cls: 采集器类
    
    Returns:
        装饰后的类
    """
    if not issubclass(cls, BaseCollector):
        raise ValueError("必须继承 BaseCollector")
    
    instance = cls()
    _collectors[instance.name] = instance
    return cls


def get_collector(name: str) -> Optional[BaseCollector]:
    """
    根据名称获取采集器实例
    
    Args:
        name: 采集器名称
    
    Returns:
        采集器实例，如果不存在返回 None
    """
    return _collectors.get(name)


def get_all_collectors() -> List[BaseCollector]:
    """获取所有已注册的采集器"""
    return sorted(_collectors.values(), key=lambda c: c.priority)


def collect_all(target_date: date) -> List[SessionData]:
    """
    采集所有数据源的数据
    
    Args:
        target_date: 目标日期
    
    Returns:
        所有会话数据列表
    """
    all_sessions = []
    
    for collector in get_all_collectors():
        try:
            sessions = collector.collect(target_date)
            all_sessions.extend(sessions)
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"采集器 {collector.name} 执行失败: {e}")
    
    # 按开始时间排序
    all_sessions.sort(key=lambda s: s.start_time)
    return all_sessions