"""
基础采集器模块

定义统一的采集器接口和数据结构
支持原始数据保存到按渠道/日期分目录的结构
"""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Any
import logging

logger = logging.getLogger(__name__)


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
    
    def save_raw_data(self, sessions: List[SessionData], data_dir: Path) -> None:
        """
        将原始会话数据保存到按渠道/日期分目录的结构
        
        目录结构：
        data/raw/{source}/{date}/session_{index}.md
        
        Args:
            sessions: 会话数据列表
            data_dir: 数据根目录
        """
        from config import get_config
        
        config = get_config()
        raw_data_dir = config.data_dir / "raw"
        
        for idx, session in enumerate(sessions, 1):
            # 创建目录结构: data/raw/{source}/{date}/
            date_str = session.start_time.strftime("%Y-%m-%d")
            session_dir = raw_data_dir / session.source / date_str
            session_dir.mkdir(parents=True, exist_ok=True)
            
            # 生成文件名: session_001.md, session_002.md, ...
            filename = f"session_{idx:03d}.md"
            file_path = session_dir / filename
            
            # 保存原始数据（保持完整，不剪辑）
            content = self._format_session_as_markdown(session)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            logger.info(f"[{self.name}] 原始数据已保存: {file_path}")
    
    def _format_session_as_markdown(self, session: SessionData) -> str:
        """
        将会话数据格式化为 Markdown 格式（保持原始数据完整）
        
        Args:
            session: 会话数据
        
        Returns:
            Markdown 格式的会话内容
        """
        lines = []
        
        # 会话元信息
        lines.append(f"# {session.title}")
        lines.append("")
        lines.append(f"**会话ID**: {session.session_id}")
        lines.append(f"**来源**: {session.source}")
        lines.append(f"**项目路径**: {session.project_path}")
        lines.append(f"**开始时间**: {session.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**结束时间**: {session.end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**摘要**: {session.summary}")
        lines.append(f"**输入Token**: {session.tokens_input}")
        lines.append(f"**输出Token**: {session.tokens_output}")
        if session.files_modified:
            lines.append(f"**修改文件**: {', '.join(session.files_modified)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        
        # 消息内容（保持完整，不剪辑）
        lines.append("## 对话内容")
        lines.append("")
        
        for msg in session.messages:
            role_label = "👤 用户" if msg.role == "user" else "🤖 助手"
            lines.append(f"### {role_label}")
            lines.append(f"**时间**: {msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')}")
            lines.append("")
            lines.append(msg.content)
            lines.append("")
            lines.append("---")
            lines.append("")
        
        return '\n'.join(lines)


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