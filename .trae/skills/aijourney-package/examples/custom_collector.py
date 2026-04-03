#!/usr/bin/env python3
"""
自定义采集器示例
"""

from datetime import date, datetime
from typing import List
from aijourney import (
    AIJourneySkill,
    BaseCollector,
    SessionData,
    register_collector,
)


@register_collector
class MockAICollector(BaseCollector):
    """模拟AI工具采集器 - 用于演示"""
    
    name = "mock_ai_tool"
    description = "模拟AI编程工具数据"
    
    def validate(self) -> bool:
        """总是可用"""
        return True
    
    def collect(self, target_date: date) -> List[SessionData]:
        """生成模拟数据"""
        sessions = []
        
        # 模拟3个会话
        for i in range(3):
            session = SessionData(
                session_id=f"mock_session_{i}_{target_date}",
                tool_name="MockAI",
                start_time=datetime.combine(target_date, datetime.min.time()),
                messages=[
                    {
                        "role": "user",
                        "content": f"问题 {i+1}: 如何优化这段代码？",
                        "timestamp": datetime.now().isoformat(),
                    },
                    {
                        "role": "assistant",
                        "content": f"回答 {i+1}: 建议使用更高效的数据结构...",
                        "timestamp": datetime.now().isoformat(),
                    },
                ],
                metadata={
                    "model": "gpt-4",
                    "tokens": 150 + i * 50,
                },
            )
            sessions.append(session)
        
        return sessions


@register_collector
class FileLogCollector(BaseCollector):
    """从日志文件采集"""
    
    name = "file_log"
    description = "从本地日志文件读取会话"
    
    def __init__(self, config=None):
        super().__init__(config)
        self.log_file = self.config.get("log_file", "./my_ai_logs.txt")
    
    def validate(self) -> bool:
        """检查日志文件是否存在"""
        from pathlib import Path
        return Path(self.log_file).exists()
    
    def collect(self, target_date: date) -> List[SessionData]:
        """读取日志文件"""
        sessions = []
        
        try:
            with open(self.log_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # 简单解析：每行一个会话
            for i, line in enumerate(content.strip().split('\n')):
                if line.strip():
                    session = SessionData(
                        session_id=f"log_{i}_{target_date}",
                        tool_name="FileLog",
                        start_time=datetime.combine(target_date, datetime.min.time()),
                        messages=[{"content": line}],
                        metadata={"source": self.log_file},
                    )
                    sessions.append(session)
        except Exception as e:
            self.logger.error(f"读取日志文件失败: {e}")
        
        return sessions


def example_custom_collector():
    """使用自定义采集器"""
    print("=" * 60)
    print("自定义采集器示例")
    print("=" * 60)
    
    # 创建Skill实例
    skill = AIJourneySkill(output_dir="./output")
    
    # 注册自定义采集器
    skill.register_collector(MockAICollector)
    skill.register_collector(FileLogCollector)
    
    # 运行
    result = skill.run(
        collector_names=["mock_ai_tool"],  # 只使用模拟采集器
        period="daily",
    )
    
    print(f"\n采集结果:")
    print(f"  会话数: {result['session_count']}")
    print(f"  报告文件: {result['report']['files']}")


def example_all_collectors():
    """使用所有采集器"""
    print("\n" + "=" * 60)
    print("所有采集器示例")
    print("=" * 60)
    
    skill = AIJourneySkill(output_dir="./output")
    
    # 加载内置采集器
    skill.load_builtin_collectors()
    
    # 注册自定义采集器
    skill.register_collector(MockAICollector)
    
    # 运行所有采集器
    result = skill.run(period="daily")
    
    print(f"\n总共采集到 {result['session_count']} 个会话")


if __name__ == "__main__":
    example_custom_collector()
    example_all_collectors()
    
    print("\n" + "=" * 60)
    print("自定义采集器示例执行完成！")
    print("=" * 60)
