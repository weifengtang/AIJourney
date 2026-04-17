"""
CodeBuddy 采集器

采集 CodeBuddy 的会话数据
支持跨平台路径自动识别（Windows/macOS/Linux）
支持通过环境变量手动指定路径
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any
import logging

from .base import BaseCollector, SessionData, Message, register_collector
from config import get_config


logger = logging.getLogger(__name__)


@register_collector
class CodeBuddyCollector(BaseCollector):
    """CodeBuddy 采集器"""
    
    name = "codebuddy"
    version = "2.0.0"
    priority = 20
    
    def get_data_path(self) -> Path:
        """获取数据源路径"""
        return get_config().codebuddy_storage_path
    
    def collect(self, target_date: date) -> List[SessionData]:
        """
        采集指定日期的 CodeBuddy 会话数据
        
        Args:
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        logger.info(f"[{self.name}] 开始采集 {target_date} 的会话数据")
        
        data_path = self.get_data_path()
        logger.info(f"[{self.name}] 数据路径: {data_path}")
        
        # 验证数据路径
        if not data_path.exists():
            logger.warning(f"[{self.name}] 数据路径不存在，跳过采集")
            return []
        
        sessions = []
        
        # 遍历存储目录查找会话文件
        for item in data_path.iterdir():
            if item.is_dir():
                session_files = list(item.glob("*.json"))
                for session_file in session_files:
                    try:
                        session_data = self._parse_session_file(session_file, target_date)
                        if session_data:
                            sessions.append(session_data)
                    except Exception as e:
                        logger.error(f"[{self.name}] 解析会话文件失败 {session_file}: {e}")
        
        # 按开始时间排序
        sessions.sort(key=lambda s: s.start_time)
        
        logger.info(f"[{self.name}] 采集完成，获取到 {len(sessions)} 个会话")
        return sessions
    
    def _parse_session_file(self, session_file: Path, target_date: date) -> SessionData:
        """
        解析会话文件
        
        Args:
            session_file: 会话文件路径
            target_date: 目标日期
        
        Returns:
            SessionData 实例，如果日期不匹配返回 None
        """
        with open(session_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # 获取会话基本信息
        session_id = data.get('id', session_file.stem)
        
        # 获取时间戳
        created_at = data.get('createdAt')
        if created_at:
            try:
                start_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                start_time = start_time.replace(tzinfo=None)
            except ValueError:
                start_time = datetime.fromtimestamp(0)
        else:
            start_time = datetime.fromtimestamp(0)
        
        # 检查日期是否匹配
        if start_time.date() != target_date:
            return None
        
        # 获取结束时间
        updated_at = data.get('updatedAt')
        if updated_at:
            try:
                end_time = datetime.fromisoformat(updated_at.replace('Z', '+00:00'))
                end_time = end_time.replace(tzinfo=None)
            except ValueError:
                end_time = start_time
        else:
            end_time = start_time
        
        # 解析消息
        messages = []
        messages_data = data.get('messages', [])
        
        user_input_count = 0
        assistant_reply_count = 0
        tokens_input = 0
        tokens_output = 0
        
        for msg_data in messages_data:
            role = msg_data.get('role', 'user')
            content = msg_data.get('content', '')
            timestamp_str = msg_data.get('createdAt', created_at)
            
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
                timestamp = timestamp.replace(tzinfo=None)
            except ValueError:
                timestamp = start_time
            
            messages.append(Message(
                role=role,
                content=content,
                timestamp=timestamp,
            ))
            
            if role == 'user':
                user_input_count += 1
                tokens_input += len(content) // 4  # 粗略估算
            else:
                assistant_reply_count += 1
                tokens_output += len(content) // 4
        
        # 生成标题
        title = self._generate_title(messages, data.get('title'))
        
        # 生成摘要
        summary = f"用户输入 {user_input_count} 次，AI 回复 {assistant_reply_count} 次"
        
        # 获取项目路径
        project_path = data.get('projectPath', '')
        
        # 获取修改的文件
        files_modified = data.get('filesModified', [])
        
        return SessionData(
            session_id=session_id,
            source=self.name,
            project_path=project_path,
            start_time=start_time,
            end_time=end_time,
            title=title,
            summary=summary,
            messages=messages,
            files_modified=files_modified,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
        )
    
    def _generate_title(self, messages: List[Message], default_title: str = '') -> str:
        """
        生成标题
        
        Args:
            messages: 消息列表
            default_title: 默认标题
        
        Returns:
            标题
        """
        if default_title:
            return default_title[:50] + ('...' if len(default_title) > 50 else '')
        
        # 从第一条用户消息提取标题
        for msg in messages:
            if msg.role == 'user':
                return msg.content[:50] + ('...' if len(msg.content) > 50 else '')
        
        return "无标题会话"