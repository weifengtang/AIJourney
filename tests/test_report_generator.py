"""
报告生成器单元测试
"""

import tempfile
from datetime import date, datetime
from pathlib import Path

from collectors.base import SessionData, Message
from report.generator import ReportGenerator
from report.summarizer import SessionSummary, SessionSummarizer


class TestReportGenerator:
    """报告生成器单元测试"""

    def setup_method(self):
        """测试前准备"""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.output_dir = Path(self.temp_dir.name)
        self.generator = ReportGenerator(self.output_dir)

    def teardown_method(self):
        """测试后清理"""
        self.temp_dir.cleanup()

    def test_generate_json_report(self):
        """测试生成 JSON 报告"""
        sessions = self._create_test_sessions()
        self.generator.generate(sessions, date(2026, 3, 25), ["json"])
        
        json_file = self.output_dir / "daily_report_20260325.json"
        assert json_file.exists()

    def test_generate_markdown_report(self):
        """测试生成 Markdown 报告"""
        sessions = self._create_test_sessions()
        self.generator.generate(sessions, date(2026, 3, 25), ["markdown"])
        
        md_file = self.output_dir / "daily_report_20260325.md"
        assert md_file.exists()
        content = md_file.read_text(encoding='utf-8')
        assert "2026年03月25日" in content
        assert "Test Session" in content

    def test_generate_both_formats(self):
        """测试同时生成两种格式"""
        sessions = self._create_test_sessions()
        self.generator.generate(sessions, date(2026, 3, 25), ["json", "markdown"])
        
        assert (self.output_dir / "daily_report_20260325.json").exists()
        assert (self.output_dir / "daily_report_20260325.md").exists()

    def _create_test_sessions(self):
        """创建测试会话数据"""
        now = datetime.now()
        session1 = SessionData(
            session_id="test-session-1",
            source="claude_code",
            project_path="/test/project",
            start_time=now,
            title="Test Session",
            tokens_input=100,
            tokens_output=200
        )
        session1.messages.append(Message(
            role="user",
            content="Test message",
            timestamp=now
        ))
        session1.files_modified = ["test.py"]
        return [session1]


class TestSessionSummarizer:
    """会话摘要生成器单元测试"""

    def test_summary_to_dict(self):
        """测试摘要转换为字典"""
        summary = SessionSummary(
            goal="Fix a bug in the code",
            key_questions=["Why is it crashing?"],
            achievements=["Fixed the null pointer exception"],
            files_modified=["main.py"],
            tech_points=["Python", "Debugging"],
            summary_method="rule"
        )
        data = summary.to_dict()
        assert data["goal"] == "Fix a bug in the code"
        assert len(data["key_questions"]) == 1
        assert data["summary_method"] == "rule"

    def test_summary_to_markdown(self):
        """测试摘要转换为 Markdown"""
        summary = SessionSummary(
            goal="Fix a bug",
            key_questions=["What's wrong?"],
            achievements=["Fixed bug", "Added test"],
            files_modified=["app.py"],
            tech_points=["Flask"],
            summary_method="rule"
        )
        md = summary.to_markdown()
        assert "**目标**: Fix a bug" in md
        assert "**关键问题**" in md
        assert "**主要成果**" in md
        assert "app.py" in md
