#!/usr/bin/env python3
"""
/daily-report-ai - 使用 LLM 增强的日报生成

使用 AI 对原始会话数据进行总结、提炼关键信息、生成更自然的描述
支持 Claude API、OpenAI API 或 Mock 模式（演示用）
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
from config import get_config


def main():
    # 获取配置
    config = get_config()
    
    # 获取今日日期
    today = date.today()
    
    print(f"📅 生成 {today.strftime('%Y年%m月%d日')} AI 增强日报")
    print(f"🔧 当前系统: {config.system}")
    print(f"📁 报告目录: {config.daily_report_dir}")
    print(f"🤖 LLM 提供商: {config.llm_provider}")
    print(f"🔑 LLM 启用: {'是' if config.llm_enabled else '否（使用 Mock 模式演示）'}")
    print("🤖 使用 LLM 增强报告内容...")
    
    # 采集数据
    print("\n📥 正在采集今日数据...")
    
    # Claude Code 数据
    claude_collector = ClaudeCodeCollector()
    claude_data = claude_collector.collect(today)
    print(f"  - Claude Code: {len(claude_data)} 条会话")
    
    # CodeBuddy 数据
    codebuddy_collector = CodeBuddyCollector()
    codebuddy_data = codebuddy_collector.collect(today)
    print(f"  - CodeBuddy: {len(codebuddy_data)} 条会话")
    
    # Git 提交记录
    git_collector = GitCommitsCollector()
    git_data = git_collector.collect(today)
    print(f"  - Git 提交: {len(git_data)} 条记录")
    
    # 汇总数据并转换为字典格式（便于 JSON 序列化）
    all_sessions = claude_data + codebuddy_data + git_data
    
    if all_sessions:
        print(f"✅ 共采集到 {len(all_sessions)} 条会话")
    else:
        print("⚠️ 未采集到任何数据")
    
    # 转换为字典格式用于 LLM 处理
    sessions_dict = [session_to_dict(session) for session in all_sessions]
    
    # 使用 LLM 增强报告
    print("\n🤖 正在使用 AI 生成报告...")
    
    # 初始化报告增强器（使用统一配置，支持配置文件）
    llm_config = LLMConfig(config)
    # 如果未配置 API Key，使用 Mock 模式演示
    if not llm_config.is_enabled():
        llm_config.provider = 'mock'
    enhancer = ReportEnhancer(llm_config)
    
    # 生成增强报告
    report = enhancer.enhance_daily_report(sessions_dict, today)
    
    # 输出报告
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告文件
    report_file = config.get_report_path("daily", f"ai_{today.strftime('%Y%m%d')}")
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📁 报告已保存: {report_file}")
    
    print("\n💡 提示: 配置环境变量以启用真实 LLM 增强")
    print("  - AIJOURNEY_LLM_PROVIDER=claude")
    print("  - AIJOURNEY_LLM_API_KEY=your-api-key")


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