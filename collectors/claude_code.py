"""
Claude Code 采集器

采集 Claude Code 的会话数据
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
class ClaudeCodeCollector(BaseCollector):
    """Claude Code 采集器"""
    
    name = "claude_code"
    version = "2.0.0"
    priority = 10  # 最高优先级
    
    def get_data_path(self) -> Path:
        """获取数据源路径"""
        return get_config().claude_code_path
    
    def collect(self, target_date: date) -> List[SessionData]:
        """
        采集指定日期的 Claude Code 会话数据
        
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
        
        # 1. 从 history.jsonl 获取今天的会话
        history_file = data_path / "history.jsonl"
        if not history_file.exists():
            logger.warning(f"[{self.name}] history.jsonl 不存在")
            return []
        
        sessions = self._load_sessions_from_history(history_file, target_date)
        logger.info(f"[{self.name}] 从 history.jsonl 找到 {len(sessions)} 个会话")
        
        # 2. 读取每个会话的详细内容
        projects_dir = data_path / "projects"
        for session_id, session_info in sessions.items():
            session_file = self._get_session_file(projects_dir, session_info['project'], session_id)
            
            if session_file and session_file.exists():
                self._load_session_details(session_file, session_info)
            else:
                logger.warning(f"[{self.name}] 会话文件不存在: {session_id}")
        
        # 3. 转换为 SessionData 格式
        session_data_list = []
        for session_id, session_info in sessions.items():
            session_data = self._convert_to_session_data(session_id, session_info)
            session_data_list.append(session_data)
        
        logger.info(f"[{self.name}] 采集完成，获取到 {len(session_data_list)} 个会话")
        return session_data_list
    
    def _load_sessions_from_history(self, history_file: Path, target_date: date) -> Dict[str, Dict]:
        """
        从 history.jsonl 加载指定日期的会话
        
        Args:
            history_file: history.jsonl 文件路径
            target_date: 目标日期
        
        Returns:
            会话字典 {session_id: session_info}
        """
        sessions = {}
        
        try:
            with open(history_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        
                        # 解析时间戳（去除时区信息保证一致性）
                        timestamp_ms = data.get('timestamp')
                        if not timestamp_ms:
                            continue
                        
                        timestamp = datetime.fromtimestamp(timestamp_ms / 1000)
                        # 去除时区信息，保证与其他采集器一致
                        if timestamp.tzinfo is not None:
                            timestamp = timestamp.replace(tzinfo=None)
                        
                        # 筛选目标日期
                        if timestamp.date() != target_date:
                            continue
                        
                        session_id = data.get('sessionId')
                        if not session_id:
                            continue
                        
                        # 初始化会话信息
                        if session_id not in sessions:
                            sessions[session_id] = {
                                'project': data.get('project', ''),
                                'start_time': timestamp,
                                'end_time': timestamp,
                                'user_inputs': [],
                                'messages': [],
                                'files_modified': set(),
                                'tool_calls': [],
                                'tokens_input': 0,
                                'tokens_output': 0,
                            }
                        
                        # 更新结束时间
                        if timestamp > sessions[session_id]['end_time']:
                            sessions[session_id]['end_time'] = timestamp
                        
                        # 记录用户输入
                        display = data.get('display', '')
                        if display:
                            sessions[session_id]['user_inputs'].append({
                                'time': timestamp,
                                'content': display,
                            })
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"[{self.name}] history.jsonl 第 {line_num} 行解析失败: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"[{self.name}] 读取 history.jsonl 失败: {e}")
        
        return sessions
    
    def _get_session_file(self, projects_dir: Path, project_path: str, session_id: str) -> Path:
        """
        获取会话文件路径
        
        Args:
            projects_dir: projects 目录
            project_path: 项目路径
            session_id: 会话ID
        
        Returns:
            会话文件路径
        """
        # 项目路径转换：/ 替换为 -
        if project_path:
            converted_path = project_path.replace('/', '-')
            session_file = projects_dir / converted_path / f"{session_id}.jsonl"
        else:
            # 空项目路径直接放在 projects 根目录
            session_file = projects_dir / f"{session_id}.jsonl"
        return session_file
    
    def _load_session_details(self, session_file: Path, session_info: Dict):
        """
        加载会话详细内容
        
        Args:
            session_file: 会话文件路径
            session_info: 会话信息字典
        """
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        msg_type = data.get('type')
                        
                        # 处理用户消息
                        if msg_type == 'user':
                            message = data.get('message', {})
                            content = message.get('content', '')
                            if content:
                                timestamp = datetime.fromtimestamp(data.get('timestamp', 0) / 1000)
                                if timestamp.tzinfo is not None:
                                    timestamp = timestamp.replace(tzinfo=None)
                                session_info['messages'].append(Message(
                                    role='user',
                                    content=content,
                                    timestamp=timestamp,
                                ))
                        
                        # 处理助手消息
                        elif msg_type == 'assistant':
                            message = data.get('message', {})
                            content = message.get('content', [])
                            
                            # 提取文本内容
                            text_content = self._extract_text_from_content(content)
                            if text_content:
                                timestamp = datetime.fromtimestamp(data.get('timestamp', 0) / 1000)
                                if timestamp.tzinfo is not None:
                                    timestamp = timestamp.replace(tzinfo=None)
                                session_info['messages'].append(Message(
                                    role='assistant',
                                    content=text_content,
                                    timestamp=timestamp,
                                ))
                            
                            # 统计 token
                            usage = message.get('usage', {})
                            session_info['tokens_input'] += usage.get('input_tokens', 0)
                            session_info['tokens_output'] += usage.get('output_tokens', 0)
                        
                        # 处理工具调用
                        elif msg_type == 'tool_use':
                            tool_name = data.get('tool', '')
                            if tool_name:
                                session_info['tool_calls'].append(tool_name)
                        
                        # 处理文件修改
                        elif msg_type == 'file-history-snapshot':
                            files = data.get('files', {})
                            session_info['files_modified'].update(files.keys())
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"[{self.name}] 会话文件第 {line_num} 行解析失败: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"[{self.name}] 读取会话文件失败 {session_file}: {e}")
    
    def _extract_text_from_content(self, content: Any) -> str:
        """
        从 content 中提取文本
        
        Args:
            content: 内容（可能是字符串、列表等）
        
        Returns:
            提取的文本
        """
        if isinstance(content, str):
            return content
        elif isinstance(content, list):
            texts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        texts.append(item.get('text', ''))
                elif isinstance(item, str):
                    texts.append(item)
            return '\n'.join(texts)
        return ''
    
    def _convert_to_session_data(self, session_id: str, session_info: Dict) -> SessionData:
        """
        将会话信息转换为 SessionData
        
        Args:
            session_id: 会话ID
            session_info: 会话信息字典
        
        Returns:
            SessionData 实例
        """
        # 生成标题（使用第一个用户输入）
        title = ''
        if session_info['user_inputs']:
            first_input = session_info['user_inputs'][0]['content']
            # 取前50个字符作为标题
            title = first_input[:50] + ('...' if len(first_input) > 50 else '')
        
        # 生成摘要
        summary = f"用户输入 {len(session_info['user_inputs'])} 次，" \
                  f"AI 回复 {len([m for m in session_info['messages'] if m.role == 'assistant'])} 次，" \
                  f"调用工具 {len(session_info['tool_calls'])} 次"
        
        return SessionData(
            session_id=session_id,
            source=self.name,
            project_path=session_info['project'],
            start_time=session_info['start_time'],
            end_time=session_info['end_time'],
            title=title,
            summary=summary,
            messages=session_info['messages'],
            files_modified=list(session_info['files_modified']),
            tokens_input=session_info['tokens_input'],
            tokens_output=session_info['tokens_output'],
        )
