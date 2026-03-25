"""
CodeBuddy 采集器

采集 CodeBuddy 的会话数据（JSON文件格式）
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
import logging

from .base import BaseCollector, SessionData, Message, register_collector
from config import get_config


logger = logging.getLogger(__name__)


@register_collector
class CodeBuddyCollector(BaseCollector):
    """CodeBuddy 采集器"""
    
    name = "codebuddy"
    version = "2.1.0"
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
        
        all_sessions = []
        
        # 遍历用户目录（可能有多个用户）
        for user_dir in data_path.iterdir():
            if not user_dir.is_dir():
                continue
            if user_dir.name in ['Public', 'default']:
                continue
            
            # 遍历编辑器类型（VSCode / JetBrains）
            for editor_dir in user_dir.iterdir():
                if not editor_dir.is_dir():
                    continue
                
                editor_type = editor_dir.name  # VSCode 或 JetBrains
                
                # 查找对应的用户目录
                user_editor_dir = editor_dir / user_dir.name
                if not user_editor_dir.exists():
                    continue
                
                history_dir = user_editor_dir / "history"
                if not history_dir.exists():
                    continue
                
                # 遍历工作区
                for workspace_dir in history_dir.iterdir():
                    if not workspace_dir.is_dir():
                        continue
                    
                    workspace_hash = workspace_dir.name
                    
                    # 读取工作区的会话列表
                    sessions = self._load_workspace_sessions(
                        workspace_dir, target_date, editor_type, workspace_hash
                    )
                    all_sessions.extend(sessions)
        
        logger.info(f"[{self.name}] 采集完成，获取到 {len(all_sessions)} 个会话")
        return all_sessions
    
    def _load_workspace_sessions(
        self, 
        workspace_dir: Path, 
        target_date: date,
        editor_type: str,
        workspace_hash: str
    ) -> List[SessionData]:
        """
        加载工作区的会话
        
        Args:
            workspace_dir: 工作区目录
            target_date: 目标日期
            editor_type: 编辑器类型
            workspace_hash: 工作区hash
        
        Returns:
            会话数据列表
        """
        sessions = []
        
        # 读取工作区 index.json
        workspace_index_file = workspace_dir / "index.json"
        if not workspace_index_file.exists():
            return sessions
        
        try:
            with open(workspace_index_file, 'r', encoding='utf-8') as f:
                workspace_index = json.load(f)
            
            conversations = workspace_index.get('conversations', [])
            
            for conv in conversations:
                conv_id = conv.get('id')
                conv_name = conv.get('name', '')
                created_at_str = conv.get('createdAt')
                last_message_at_str = conv.get('lastMessageAt')
                
                if not conv_id or not created_at_str:
                    continue
                
                # 解析时间
                created_at = self._parse_iso_datetime(created_at_str)
                last_message_at = self._parse_iso_datetime(last_message_at_str) if last_message_at_str else created_at
                
                # 筛选目标日期
                if created_at.date() != target_date:
                    continue
                
                # 读取会话详细内容
                session_dir = workspace_dir / conv_id
                session_data = self._load_session_detail(
                    session_dir, conv_id, conv_name, created_at, last_message_at,
                    editor_type, workspace_hash
                )
                
                if session_data:
                    sessions.append(session_data)
        
        except Exception as e:
            logger.error(f"[{self.name}] 读取工作区 {workspace_hash} 失败: {e}")
        
        return sessions
    
    def _load_session_detail(
        self,
        session_dir: Path,
        session_id: str,
        session_name: str,
        created_at: datetime,
        last_message_at: datetime,
        editor_type: str,
        workspace_hash: str
    ) -> Optional[SessionData]:
        """
        加载会话详细内容
        
        Args:
            session_dir: 会话目录
            session_id: 会话ID
            session_name: 会话名称
            created_at: 创建时间
            last_message_at: 最后消息时间
            editor_type: 编辑器类型
            workspace_hash: 工作区hash
        
        Returns:
            会话数据
        """
        session_index_file = session_dir / "index.json"
        if not session_index_file.exists():
            return None
        
        try:
            with open(session_index_file, 'r', encoding='utf-8') as f:
                session_index = json.load(f)
            
            messages_list = session_index.get('messages', [])
            requests_list = session_index.get('requests', [])
            
            # 统计 token - 从 requests 数组累加
            tokens_input = 0
            tokens_output = 0
            
            for req in requests_list:
                usage = req.get('usage', {})
                tokens_input += usage.get('inputTokens', 0)
                tokens_output += usage.get('outputTokens', 0)
            
            # 加载消息内容
            messages = []
            messages_dir = session_dir / "messages"
            
            if messages_dir.exists():
                for msg_meta in messages_list:
                    # 跳过 craft 类型的消息（这是会话级别的统计）
                    if msg_meta.get('type') == 'craft':
                        continue
                    
                    msg_id = msg_meta.get('id')
                    if not msg_id:
                        continue
                    
                    msg_file = messages_dir / f"{msg_id}.json"
                    if msg_file.exists():
                        msg = self._load_message(msg_file)
                        if msg:
                            messages.append(msg)
            
            # 生成摘要
            user_msgs = len([m for m in messages if m.role == 'user'])
            assistant_msgs = len([m for m in messages if m.role == 'assistant'])
            summary = f"用户输入 {user_msgs} 次，AI 回复 {assistant_msgs} 次"
            
            return SessionData(
                session_id=session_id,
                source=self.name,
                project_path=f"{editor_type}:{workspace_hash}",
                start_time=created_at,
                end_time=last_message_at,
                title=session_name,
                summary=summary,
                messages=messages,
                files_modified=[],
                tokens_input=tokens_input,
                tokens_output=tokens_output,
            )
        
        except Exception as e:
            logger.error(f"[{self.name}] 读取会话 {session_id} 失败: {e}")
            return None
    
    def _load_message(self, msg_file: Path) -> Optional[Message]:
        """
        加载单条消息
        
        Args:
            msg_file: 消息文件路径
        
        Returns:
            消息对象
        """
        try:
            with open(msg_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            role = data.get('role', 'user')
            timestamp_str = data.get('createdAt') or data.get('timestamp')
            
            if timestamp_str:
                timestamp = self._parse_iso_datetime(timestamp_str)
            else:
                timestamp = datetime.now()
            
            # CodeBuddy 的消息格式：message 字段是 JSON 字符串
            message_str = data.get('message', '')
            content = ''
            
            if message_str:
                try:
                    message_data = json.loads(message_str)
                    # content 可能是字符串或数组
                    raw_content = message_data.get('content', '')
                    if isinstance(raw_content, str):
                        content = raw_content
                    elif isinstance(raw_content, list):
                        # 从 content 数组中提取文本
                        texts = []
                        for item in raw_content:
                            if isinstance(item, dict) and item.get('type') == 'text':
                                texts.append(item.get('text', ''))
                            elif isinstance(item, str):
                                texts.append(item)
                        content = '\n'.join(texts)
                except json.JSONDecodeError:
                    content = message_str
            
            return Message(
                role=role,
                content=content,
                timestamp=timestamp,
            )
        
        except Exception as e:
            logger.warning(f"[{self.name}] 读取消息文件失败 {msg_file}: {e}")
            return None
    
    def _parse_iso_datetime(self, dt_str: str) -> datetime:
        """
        解析 ISO 格式的时间字符串
        
        Args:
            dt_str: ISO 时间字符串
        
        Returns:
            datetime 对象
        """
        try:
            # 处理带 Z 的格式
            if dt_str.endswith('Z'):
                dt_str = dt_str[:-1] + '+00:00'
            return datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        except:
            return datetime.now()
