"""
Claude Code 采集器单元测试
"""

import json
import tempfile
from datetime import datetime, date
from pathlib import Path
from unittest.mock import patch, MagicMock

from collectors.claude_code import ClaudeCodeCollector
from collectors.base import SessionData


class TestClaudeCodeCollector:
    """Claude Code 采集器单元测试"""

    def setup_method(self):
        """测试前准备"""
        self.collector = ClaudeCodeCollector()

    def test_collector_metadata(self):
        """测试采集器元数据"""
        assert self.collector.name == "claude_code"
        assert self.collector.version == "2.0.0"
        assert self.collector.priority == 10

    def test_get_session_file_path_conversion(self):
        """测试项目路径转换（/ -> -）"""
        projects_dir = Path("/tmp/projects")
        project_path = "/Users/user/work/project"
        session_id = "test-session-123"
        
        session_file = self.collector._get_session_file(projects_dir, project_path, session_id)
        expected = projects_dir / "-Users-user-work-project" / "test-session-123.jsonl"
        assert session_file == expected

    def test_extract_text_from_content_string(self):
        """测试从字符串提取文本"""
        content = "Hello world"
        result = self.collector._extract_text_from_content(content)
        assert result == "Hello world"

    def test_extract_text_from_content_list(self):
        """测试从列表提取文本"""
        content = [
            {"type": "text", "text": "First part"},
            {"type": "text", "text": "Second part"}
        ]
        result = self.collector._extract_text_from_content(content)
        assert "First part" in result
        assert "Second part" in result

    def test_extract_text_from_content_mixed(self):
        """测试混合类型提取文本"""
        content = [
            "Plain text",
            {"type": "text", "text": "Dict text"},
            {"type": "other", "text": "Should not extract"},
        ]
        result = self.collector._extract_text_from_content(content)
        assert "Plain text" in result
        assert "Dict text" in result

    def test_extract_text_from_content_unknown(self):
        """测试未知类型返回空字符串"""
        content = 12345
        result = self.collector._extract_text_from_content(content)
        assert result == ""

    def test_convert_to_session_data(self):
        """测试转换为 SessionData"""
        session_id = "test-123"
        session_info = {
            "project": "/test/project",
            "start_time": datetime(2026, 3, 25, 10, 0, 0),
            "end_time": datetime(2026, 3, 25, 11, 0, 0),
            "user_inputs": [
                {"content": "Help me fix this bug in the code", "time": datetime.now()}
            ],
            "messages": [],
            "files_modified": {"main.py", "config.py"},
            "tool_calls": ["read_file", "edit_file"],
            "tokens_input": 500,
            "tokens_output": 1000,
        }
        
        result = self.collector._convert_to_session_data(session_id, session_info)
        assert isinstance(result, SessionData)
        assert result.session_id == "test-123"
        assert result.source == "claude_code"
        assert result.project_path == "/test/project"
        assert result.start_time == session_info["start_time"]
        assert result.end_time == session_info["end_time"]
        assert "Help me fix" in result.title
        assert len(result.files_modified) == 2
        assert set(result.files_modified) == {"main.py", "config.py"}
        assert result.tokens_input == 500
        assert result.tokens_output == 1000

    def test_convert_to_session_data_empty_user_inputs(self):
        """测试空用户输入时标题为空"""
        session_id = "test-123"
        session_info = {
            "project": "/test/project",
            "start_time": datetime(2026, 3, 25, 10, 0, 0),
            "end_time": datetime(2026, 3, 25, 11, 0, 0),
            "user_inputs": [],
            "messages": [],
            "files_modified": set(),
            "tool_calls": [],
            "tokens_input": 0,
            "tokens_output": 0,
        }
        
        result = self.collector._convert_to_session_data(session_id, session_info)
        assert result.title == ""

    def test_load_sessions_from_history_filter_by_date(self):
        """测试从 history.jsonl 加载并按日期筛选"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            # 今天的会话
            f.write(json.dumps({
                "timestamp": int(datetime(2026, 3, 25, 10, 0, 0).timestamp() * 1000),
                "sessionId": "session-today",
                "project": "/test/project",
                "display": "test today"
            }) + '\n')
            # 昨天的会话（应该被过滤）
            f.write(json.dumps({
                "timestamp": int(datetime(2026, 3, 24, 10, 0, 0).timestamp() * 1000),
                "sessionId": "session-yesterday",
                "project": "/test/project",
                "display": "test yesterday"
            }) + '\n')
            temp_path = Path(f.name)
        
        try:
            sessions = self.collector._load_sessions_from_history(temp_path, date(2026, 3, 25))
            assert len(sessions) == 1
            assert "session-today" in sessions
            assert "session-yesterday" not in sessions
        finally:
            temp_path.unlink()

    def test_load_sessions_from_history_invalid_json(self):
        """测试处理无效 JSON 行"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{ "valid": "json" }\n')
            f.write('this is not json\n')
            f.write(json.dumps({
                "timestamp": int(datetime(2026, 3, 25, 10, 0, 0).timestamp() * 1000),
                "sessionId": "session-valid",
                "project": "/test/project"
            }) + '\n')
            temp_path = Path(f.name)
        
        try:
            sessions = self.collector._load_sessions_from_history(temp_path, date(2026, 3, 25))
            # 无效行被跳过，有效行被处理
            assert len(sessions) == 1
            assert "session-valid" in sessions
        finally:
            temp_path.unlink()

    def test_collect_returns_empty_when_path_not_exists(self):
        """测试数据路径不存在时返回空列表"""
        with patch.object(self.collector, 'get_data_path', return_value=Path("/nonexistent/path")):
            result = self.collector.collect(date(2026, 3, 25))
            assert result == []

    def test_collect_returns_empty_when_history_not_exists(self):
        """测试 history.jsonl 不存在时返回空列表"""
        with tempfile.TemporaryDirectory() as tmpdir:
            data_path = Path(tmpdir)
            with patch.object(self.collector, 'get_data_path', return_value=data_path):
                result = self.collector.collect(date(2026, 3, 25))
                assert result == []
