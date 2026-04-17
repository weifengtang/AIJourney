#!/usr/bin/env python3
"""
/daily-report - 生成今日日报

支持跨平台路径配置（Windows/macOS/Linux）
支持通过环境变量自定义报告输出目录
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.claude_code import ClaudeCodeCollector
from collectors.codebuddy import CodeBuddyCollector
from collectors.git_commits import GitCommitsCollector
from datetime import date, timedelta
from config import get_config


def main():
    # 获取配置
    config = get_config()
    
    # 获取今日日期
    today = date.today()
    
    print(f"📅 生成 {today.strftime('%Y年%m月%d日')} 日报")
    print(f"🔧 当前系统: {config.system}")
    print(f"📁 报告目录: {config.daily_report_dir}")
    
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
    
    # 汇总数据
    all_sessions = claude_data + codebuddy_data + git_data
    
    if all_sessions:
        print(f"✅ 共采集到 {len(all_sessions)} 条会话")
    else:
        print("⚠️ 未采集到任何数据")
    
    # 生成报告
    report = generate_report(all_sessions, today, "daily")
    
    # 输出报告
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告文件（使用配置的报告目录）
    report_file = config.get_report_path("daily", today.strftime('%Y%m%d'))
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📁 报告已保存: {report_file}")


def generate_report(sessions, target_date, period):
    """生成 Markdown 报告"""
    report = f"""# 📅 {period}报告 - {target_date.strftime('%Y年%m月%d日')}

## 📊 工作概览

| 项目 | 详情 |
|------|------|
| **日期** | {target_date.strftime('%Y-%m-%d')} |
| **周期** | {period} |
| **总会话数** | {len(sessions)} |

## 🎯 今日成果

"""
    
    # 按数据源分类
    by_source = {}
    for session in sessions:
        source = session.source
        if source not in by_source:
            by_source[source] = []
        by_source[source].append(session)
    
    source_names = {
        'claude_code': 'Claude Code',
        'codebuddy': 'CodeBuddy',
        'git_commits': 'Git 提交',
    }
    
    for source, source_sessions in by_source.items():
        source_name = source_names.get(source, source)
        report += f"### {source_name}\n\n"
        for idx, session in enumerate(source_sessions[:5], 1):
            summary = session.summary[:100] + ('...' if len(session.summary) > 100 else '')
            report += f"{idx}. **{session.title}**\n   {summary}\n"
        report += "\n"
    
    report += """## 📝 会话详情

（完整会话列表...）

---
*AI Journey - 让每一次 AI 协作都被永久记录*
"""
    
    return report


if __name__ == "__main__":
    main()