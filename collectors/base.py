"""
SumAll 采集器基类模块

定义采集器的基类和注册机制
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Dict, Type, Optional, Any
import logging


logger = logging.getLogger(__name__)


@dataclass
class Message:
    """消息数据结构"""
    role: str                    # user / assistant
    content: str                 # 消息内容
    timestamp: datetime          # 时间戳
    tool_calls: List[Dict[str, Any]] = field(default_factory=list)  # 工具调用
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "tool_calls": self.tool_calls,
        }


@dataclass
class SessionData:
    """单个会话的数据结构"""
    
    # 基础信息
    session_id: str              # 会话唯一标识
    source: str                  # 来源：claude_code / vscode / idea / codebuddy
    project_path: Optional[str] = None  # 项目路径
    
    # 时间信息
    start_time: datetime = field(default_factory=datetime.now)  # 开始时间
    end_time: Optional[datetime] = None  # 结束时间
    
    # 内容信息
    title: Optional[str] = None  # 会话标题
    summary: Optional[str] = None  # 摘要
    messages: List[Message] = field(default_factory=list)  # 消息列表
    files_modified: List[str] = field(default_factory=list)  # 修改的文件列表
    
    # 统计信息
    tokens_input: int = 0        # 输入 token 数
    tokens_output: int = 0       # 输出 token 数
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "session_id": self.session_id,
            "source": self.source,
            "project_path": self.project_path,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "title": self.title,
            "summary": self.summary,
            "messages": [msg.to_dict() for msg in self.messages],
            "files_modified": self.files_modified,
            "tokens_input": self.tokens_input,
            "tokens_output": self.tokens_output,
        }


class BaseCollector(ABC):
    """采集器基类"""
    
    # 采集器元数据（子类必须覆盖）
    name: str = "base"
    version: str = "1.0.0"
    priority: int = 100  # 优先级（越小越先执行）
    
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
        验证采集器是否可用
        
        Returns:
            True 如果采集器可用，False 否则
        """
        data_path = self.get_data_path()
        if not data_path.exists():
            logger.warning(f"[{self.name}] 数据路径不存在: {data_path}")
            return False
        return True
    
    @abstractmethod
    def get_data_path(self) -> Path:
        """
        获取数据源路径
        
        Returns:
            数据源路径
        """
        pass
    
    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name={self.name} version={self.version}>"


# 采集器注册表
_COLLECTORS: Dict[str, Type[BaseCollector]] = {}


def register_collector(cls: Type[BaseCollector]) -> Type[BaseCollector]:
    """
    装饰器：注册采集器
    
    Args:
        cls: 采集器类
    
    Returns:
        注册后的采集器类
    """
    _COLLECTORS[cls.name] = cls
    logger.debug(f"注册采集器: {cls.name}")
    return cls


def get_collector(name: str) -> Optional[Type[BaseCollector]]:
    """
    根据名称获取采集器类
    
    Args:
        name: 采集器名称
    
    Returns:
        采集器类，如果不存在返回 None
    """
    return _COLLECTORS.get(name)


def get_all_collectors() -> List[Type[BaseCollector]]:
    """
    获取所有已注册的采集器类
    
    Returns:
        采集器类列表
    """
    return list(_COLLECTORS.values())


def get_all_collector_instances() -> List[BaseCollector]:
    """
    获取所有已注册的采集器实例
    
    Returns:
        采集器实例列表（按优先级排序）
    """
    collectors = [cls() for cls in _COLLECTORS.values()]
    return sorted(collectors, key=lambda c: c.priority)


def clear_collectors():
    """清空采集器注册表（用于测试）"""
    global _COLLECTORS
    _COLLECTORS = {}
