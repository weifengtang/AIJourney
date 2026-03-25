"""
采集器基类单元测试
"""

from datetime import datetime, date
from typing import List

from collectors.base import (
    BaseCollector,
    SessionData,
    Message,
    register_collector,
    get_collector,
    get_all_collectors,
    get_all_collector_instances,
    clear_collectors,
)


class TestMessage:
    """Message 数据类单元测试"""

    def test_create_message(self):
        """测试创建消息"""
        now = datetime.now()
        msg = Message(
            role="user",
            content="Hello world",
            timestamp=now
        )
        assert msg.role == "user"
        assert msg.content == "Hello world"
        assert msg.timestamp == now
        assert msg.tool_calls == []

    def test_to_dict(self):
        """测试转换为字典"""
        now = datetime(2026, 3, 25, 10, 0, 0)
        msg = Message(
            role="assistant",
            content="Hi there",
            timestamp=now,
            tool_calls=[{"name": "test", "args": {}}]
        )
        data = msg.to_dict()
        assert data["role"] == "assistant"
        assert data["content"] == "Hi there"
        assert data["timestamp"] == "2026-03-25T10:00:00"
        assert len(data["tool_calls"]) == 1


class TestSessionData:
    """SessionData 数据类单元测试"""

    def test_create_session(self):
        """测试创建会话"""
        now = datetime.now()
        session = SessionData(
            session_id="test-123",
            source="claude_code",
            start_time=now
        )
        assert session.session_id == "test-123"
        assert session.source == "claude_code"
        assert session.messages == []
        assert session.files_modified == []

    def test_to_dict(self):
        """测试转换为字典"""
        now = datetime(2026, 3, 25, 10, 0, 0)
        session = SessionData(
            session_id="test-123",
            source="claude_code",
            project_path="/home/user/project",
            start_time=now,
            title="Test Session",
            tokens_input=100,
            tokens_output=200
        )
        session.messages.append(Message(
            role="user",
            content="test",
            timestamp=now
        ))
        session.files_modified.append("test.py")
        
        data = session.to_dict()
        assert data["session_id"] == "test-123"
        assert data["source"] == "claude_code"
        assert data["project_path"] == "/home/user/project"
        assert len(data["messages"]) == 1
        assert len(data["files_modified"]) == 1
        assert data["tokens_input"] == 100
        assert data["tokens_output"] == 200


class TestCollectorRegistry:
    """采集器注册机制单元测试"""

    def setup_method(self):
        """测试前清理"""
        clear_collectors()

    def test_register_collector(self):
        """测试注册采集器"""
        @register_collector
        class TestCollector(BaseCollector):
            name = "test"
            version = "1.0.0"
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        collectors = get_all_collectors()
        assert len(collectors) == 1
        assert collectors[0].name == "test"

    def test_get_collector(self):
        """测试按名称获取采集器"""
        @register_collector
        class TestCollector(BaseCollector):
            name = "test_get"
            version = "1.0.0"
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        collector_cls = get_collector("test_get")
        assert collector_cls is not None
        assert collector_cls.name == "test_get"

    def test_get_all_collector_instances(self):
        """测试获取所有采集器实例"""
        from pathlib import Path
        @register_collector
        class TestCollector1(BaseCollector):
            name = "test1"
            version = "1.0.0"
            def get_data_path(self) -> Path:
                return Path("/tmp")
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        @register_collector
        class TestCollector2(BaseCollector):
            name = "test2"
            version = "1.0.0"
            def get_data_path(self) -> Path:
                return Path("/tmp")
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        instances = get_all_collector_instances()
        assert len(instances) == 2
        assert {inst.name for inst in instances} == {"test1", "test2"}

    def test_clear_collectors(self):
        """测试清空采集器"""
        @register_collector
        class TestCollector(BaseCollector):
            name = "test_clear"
            version = "1.0.0"
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        assert len(get_all_collectors()) == 1
        clear_collectors()
        assert len(get_all_collectors()) == 0


class TestBaseCollector:
    """BaseCollector 基类单元测试"""

    def test_default_validate(self):
        """测试默认验证方法总是返回 True"""
        from pathlib import Path
        class TestCollector(BaseCollector):
            name = "test_validate"
            version = "1.0.0"
            def get_data_path(self) -> Path:
                return Path("/tmp")
            def collect(self, target_date: date) -> List[SessionData]:
                return []
        
        collector = TestCollector()
        assert collector.validate() is True
