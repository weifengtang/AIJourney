"""
Claude Code 采集器（优化版）

优化点：
1. 完整遍历 projects 目录获取所有历史会话（P0）
2. 添加会话元数据缓存机制（P1）
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Any
import logging
from dateutil import parser as date_parser

from .base import BaseCollector, SessionData, Message, register_collector
from config import get_config
from utils.cache import cache_manager

logger = logging.getLogger(__name__)


@register_collector
class ClaudeCodeCollector(BaseCollector):
    """Claude Code 采集器（优化版）"""
    
    name = "claude_code"
    version = "3.0.0"
    priority = 10  # 最高优先级
    
    def __init__(self):
        self._cached_sessions = None
    
    def get_data_path(self) -> Path:
        """获取数据源路径"""
        return get_config().claude_code_path
    
    def _scan_project_sessions(self, projects_dir: Path) -> List[Dict]:
        """
        扫描 projects 目录，获取所有会话文件信息
        
        Args:
            projects_dir: projects 目录路径
        
        Returns:
            会话文件信息列表
        """
        session_files = []
        
        if not projects_dir.exists():
            logger.warning(f"[{self.name}] projects 目录不存在: {projects_dir}")
            return session_files
        
        try:
            # 遍历所有项目目录
            for project_dir in projects_dir.iterdir():
                if not project_dir.is_dir():
                    continue
                
                # 跳过隐藏目录
                if project_dir.name.startswith('.'):
                    continue
                
                # 查找所有 .jsonl 会话文件
                for session_file in project_dir.glob("*.jsonl"):
                    session_id = session_file.stem
                    
                    session_files.append({
                        'session_id': session_id,
                        'project_path': project_dir.name.replace('-', '/'),  # 还原项目路径
                        'file_path': str(session_file),
                        'file_mtime': session_file.stat().st_mtime,
                    })
            
            logger.info(f"[{self.name}] 从 projects 目录发现 {len(session_files)} 个会话文件")
        
        except Exception as e:
            logger.error(f"[{self.name}] 扫描 projects 目录失败: {e}")
        
        return session_files
    
    def _load_session_cache(self) -> Dict:
        """
        加载会话缓存
        
        Returns:
            缓存的会话数据
        """
        if self._cached_sessions is not None:
            return self._cached_sessions
        
        cache_data = cache_manager.load_cache("claude_sessions")
        if cache_data is not None:
            self._cached_sessions = cache_data.get("data", {})
            return self._cached_sessions
        
        return {}
    
    def _save_session_cache(self, sessions: Dict) -> None:
        """
        保存会话缓存
        
        Args:
            sessions: 会话数据
        """
        self._cached_sessions = sessions
        cache_manager.save_cache("claude_sessions", sessions, ttl_days=1)
    
    def _parse_session_file(self, session_file: Path) -> Dict:
        """
        解析单个会话文件
        
        Args:
            session_file: 会话文件路径
        
        Returns:
            解析后的会话数据
        """
        session_data = {
            'messages': [],
            'user_inputs': [],
            'tokens_input': 0,
            'tokens_output': 0,
            'tool_calls': [],
            'files_modified': set(),
            'start_time': None,
            'end_time': None,
        }
        
        try:
            with open(session_file, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        data = json.loads(line.strip())
                        msg_type = data.get('type')
                        timestamp = self._parse_timestamp(data.get('timestamp'))
                        
                        # 更新时间范围
                        if session_data['start_time'] is None or timestamp < session_data['start_time']:
                            session_data['start_time'] = timestamp
                        if session_data['end_time'] is None or timestamp > session_data['end_time']:
                            session_data['end_time'] = timestamp
                        
                        # 处理用户消息
                        if msg_type == 'user':
                            message = data.get('message', {})
                            content = message.get('content', '')
                            if isinstance(content, list):
                                content = self._extract_text_from_content(content)
                            if content and isinstance(content, str) and not content.startswith('<local-command-caveat>'):
                                session_data['user_inputs'].append({
                                    'time': timestamp,
                                    'content': content,
                                })
                                session_data['messages'].append(Message(
                                    role='user',
                                    content=content,
                                    timestamp=timestamp,
                                ))
                        
                        # 处理助手消息
                        elif msg_type == 'assistant':
                            message = data.get('message', {})
                            content = message.get('content', [])
                            text_content = self._extract_text_from_content(content)
                            if text_content:
                                session_data['messages'].append(Message(
                                    role='assistant',
                                    content=text_content,
                                    timestamp=timestamp,
                                ))
                            
                            # 统计 token
                            usage = message.get('usage', {})
                            session_data['tokens_input'] += usage.get('input_tokens', 0)
                            session_data['tokens_output'] += usage.get('output_tokens', 0)
                        
                        # 处理工具调用
                        elif msg_type == 'tool_use':
                            tool_name = data.get('tool', '')
                            if tool_name:
                                session_data['tool_calls'].append(tool_name)
                        
                        # 处理文件修改
                        elif msg_type == 'file-history-snapshot':
                            snapshot = data.get('snapshot', {})
                            tracked_files = snapshot.get('trackedFileBackups', {})
                            session_data['files_modified'].update(tracked_files.keys())
                    
                    except json.JSONDecodeError as e:
                        logger.warning(f"[{self.name}] 会话文件 {session_file} 第 {line_num} 行解析失败: {e}")
                        continue
        
        except Exception as e:
            logger.error(f"[{self.name}] 读取会话文件失败 {session_file}: {e}")
        
        # 设置默认时间
        if session_data['start_time'] is None:
            session_data['start_time'] = datetime.now()
        if session_data['end_time'] is None:
            session_data['end_time'] = session_data['start_time']
        
        return session_data
    
    def collect(self, target_date: date, save_raw: bool = True) -> List[SessionData]:
        """
        采集指定日期的 Claude Code 会话数据（优化版）
        
        改进点：完整遍历 projects 目录获取所有历史会话
        
        Args:
            target_date: 目标日期
            save_raw: 是否保存原始数据
        
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
        
        # 1. 扫描 projects 目录获取所有会话文件
        projects_dir = data_path / "projects"
        session_files = self._scan_project_sessions(projects_dir)
        
        # 2. 加载缓存，检查哪些会话需要重新解析
        cached_sessions = self._load_session_cache()
        
        # 3. 按日期筛选并解析会话
        session_data_list = []
        updated_cache = {}
        
        for session_info in session_files:
            session_id = session_info['session_id']
            file_path = Path(session_info['file_path'])
            file_mtime = session_info['file_mtime']
            project_path = session_info['project_path']
            
            # 检查缓存
            cached_info = cached_sessions.get(session_id)
            needs_reparse = True
            
            if cached_info:
                # 检查文件是否修改过
                if cached_info.get('file_mtime') == file_mtime:
                    # 使用缓存数据
                    cached_data = cached_info.get('data')
                    if cached_data:
                        needs_reparse = False
                        session_data = self._convert_to_session_data(session_id, cached_data)
                        session_data_list.append(session_data)
                        updated_cache[session_id] = cached_info
            
            if needs_reparse:
                # 重新解析会话文件
                parsed_data = self._parse_session_file(file_path)
                
                # 检查会话日期是否匹配目标日期
                session_date = parsed_data['start_time'].date()
                if session_date != target_date:
                    # 缓存非目标日期的会话，但不加入结果
                    # 将 Message 对象转换为字典以便序列化
                    cache_data = self._prepare_cache_data(parsed_data)
                    updated_cache[session_id] = {
                        'file_mtime': file_mtime,
                        'date': session_date.isoformat(),
                        'data': cache_data,
                    }
                    continue
                
                # 转换为 SessionData
                session_data = self._convert_to_session_data(session_id, parsed_data)
                session_data_list.append(session_data)
                
                # 更新缓存
                cache_data = self._prepare_cache_data(parsed_data)
                updated_cache[session_id] = {
                    'file_mtime': file_mtime,
                    'date': session_date.isoformat(),
                    'data': cache_data,
                }
        
        # 4. 保存缓存
        self._save_session_cache(updated_cache)
        
        # 5. 保存原始数据（保持完整，不剪辑）
        if save_raw and session_data_list:
            self.save_raw_data(session_data_list, data_path)
        
        logger.info(f"[{self.name}] 采集完成，获取到 {len(session_data_list)} 个会话")
        return session_data_list
    
    def _prepare_cache_data(self, parsed_data: Dict) -> Dict:
        """
        将解析的数据准备为可序列化的格式
        
        Args:
            parsed_data: 解析后的会话数据
        
        Returns:
            可序列化的字典数据
        """
        cache_data = {k: v for k, v in parsed_data.items()}
        
        # 将 Message 对象转换为字典
        if 'messages' in cache_data:
            cache_data['messages'] = [
                {
                    'role': m.role,
                    'content': m.content,
                    'timestamp': m.timestamp.isoformat()
                } for m in cache_data['messages']
            ]
        
        # 将 datetime 对象转换为字符串
        if 'start_time' in cache_data and isinstance(cache_data['start_time'], datetime):
            cache_data['start_time'] = cache_data['start_time'].isoformat()
        if 'end_time' in cache_data and isinstance(cache_data['end_time'], datetime):
            cache_data['end_time'] = cache_data['end_time'].isoformat()
        
        # 将 user_inputs 中的 datetime 转换为字符串
        if 'user_inputs' in cache_data:
            cache_data['user_inputs'] = [
                {
                    'time': item['time'].isoformat() if isinstance(item['time'], datetime) else item['time'],
                    'content': item['content']
                } for item in cache_data['user_inputs']
            ]
        
        # 将 set 转换为 list
        if 'files_modified' in cache_data and isinstance(cache_data['files_modified'], set):
            cache_data['files_modified'] = list(cache_data['files_modified'])
        
        return cache_data
    
    def _parse_timestamp(self, timestamp_value) -> datetime:
        """
        解析时间戳，支持多种格式：ISO 8601 字符串、毫秒数值
        
        Args:
            timestamp_value: 时间戳值
        
        Returns:
            datetime 对象（无时区）
        """
        if isinstance(timestamp_value, str):
            try:
                dt = date_parser.parse(timestamp_value)
                if dt.tzinfo is not None:
                    dt = dt.replace(tzinfo=None)
                return dt
            except Exception:
                return datetime.now()
        elif isinstance(timestamp_value, (int, float)):
            return datetime.fromtimestamp(timestamp_value / 1000)
        else:
            return datetime.now()
    
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
            session_info: 会话信息字典（可能是缓存数据或解析数据）
        
        Returns:
            SessionData 实例
        """
        # 生成标题（使用第一个用户输入）
        title = ''
        if session_info.get('user_inputs'):
            first_input = session_info['user_inputs'][0]['content']
            title = first_input[:50] + ('...' if len(first_input) > 50 else '')
        else:
            title = f"会话 {session_id[:8]}"
        
        # 处理消息（可能是缓存的字典或 Message 对象）
        messages = []
        for msg in session_info.get('messages', []):
            if isinstance(msg, Message):
                messages.append(msg)
            elif isinstance(msg, dict):
                # 从缓存数据重建 Message 对象
                messages.append(Message(
                    role=msg.get('role', ''),
                    content=msg.get('content', ''),
                    timestamp=self._parse_timestamp(msg.get('timestamp'))
                ))
        
        # 处理时间（可能是字符串或 datetime）
        start_time = session_info.get('start_time')
        if isinstance(start_time, str):
            start_time = self._parse_timestamp(start_time)
        if start_time is None:
            start_time = datetime.now()
        
        end_time = session_info.get('end_time')
        if isinstance(end_time, str):
            end_time = self._parse_timestamp(end_time)
        if end_time is None:
            end_time = start_time
        
        # 生成摘要
        user_count = len(session_info.get('user_inputs', []))
        assistant_count = len([m for m in messages if m.role == 'assistant'])
        tool_count = len(session_info.get('tool_calls', []))
        
        summary = f"用户输入 {user_count} 次，" \
                  f"AI 回复 {assistant_count} 次，" \
                  f"调用工具 {tool_count} 次"
        
        # 处理 files_modified
        files_modified = session_info.get('files_modified', [])
        if isinstance(files_modified, set):
            files_modified = list(files_modified)
        
        return SessionData(
            session_id=session_id,
            source=self.name,
            project_path=session_info.get('project_path', ''),
            start_time=start_time,
            end_time=end_time,
            title=title,
            summary=summary,
            messages=messages,
            files_modified=files_modified,
            tokens_input=session_info.get('tokens_input', 0),
            tokens_output=session_info.get('tokens_output', 0),
        )