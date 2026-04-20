#!/usr/bin/env python3
"""
/daily-report-ai - AI 增强日报

作为 Claude Code Skill 使用，自动采集数据并使用内置 LLM 生成智能日报
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.claude_code import ClaudeCodeCollector
from collectors.codebuddy import CodeBuddyCollector
from collectors.git_commits import GitCommitsCollector
from llm.report_enhancer import ReportEnhancer, LLMConfig
from datetime import date
from typing import Dict
from config import get_config, is_running_in_claude_code


def main():
    config = get_config()
    today = date.today()
    is_claude_env = is_running_in_claude_code()
    
    # 简洁的状态输出（适合 Skill 场景）
    if not is_claude_env:
        print(f"📅 生成 {today.strftime('%Y年%m月%d日')} AI 增强日报")
    
    # 采集数据
    claude_collector = ClaudeCodeCollector()
    claude_data = claude_collector.collect(today)
    
    codebuddy_collector = CodeBuddyCollector()
    codebuddy_data = codebuddy_collector.collect(today)
    
    git_collector = GitCommitsCollector()
    git_data = git_collector.collect(today)
    
    all_sessions = claude_data + codebuddy_data + git_data
    sessions_dict = [session_to_dict(session) for session in all_sessions]
    
    # 初始化报告增强器（自动使用 Claude Code 内置 LLM）
    llm_config = LLMConfig(config)
    enhancer = ReportEnhancer(llm_config)
    
    # 生成增强报告
    report = enhancer.enhance_daily_report(sessions_dict, today)
    
    # 输出报告（主要输出，适合 Skill 场景）
    print(report)
    
    # 保存报告文件
    report_file = config.get_report_path("daily", f"ai_{today.strftime('%Y%m%d')}")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    
    # 仅在非 Claude Code 环境输出保存信息
    if not is_claude_env:
        print(f"\n📁 报告已保存: {report_file}")


def session_to_dict(session) -> Dict:
    """将会话对象转换为字典"""
    return {
        'session_id': session.session_id,
        'source': session.source,
        'project_path': session.project_path,
        'start_time': session.start_time.isoformat(),
        'end_time': session.end_time.isoformat(),
        'title': session.title,
        'summary': session.summary,
        'files_modified': session.files_modified,
        'tokens_input': session.tokens_input,
        'tokens_output': session.tokens_output,
        'messages': [
            {
                'role': msg.role,
                'content': msg.content,
                'timestamp': msg.timestamp.isoformat()
            } for msg in session.messages
        ]
    }


if __name__ == "__main__":
    main()