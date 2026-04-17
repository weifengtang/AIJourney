#!/usr/bin/env python3
"""
/weekly-report - 生成本周周报

支持跨平台路径配置（Windows/macOS/Linux）
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
    
    # 获取本周日期范围
    today = date.today()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)
    
    print(f"📅 生成周报 {monday.strftime('%Y年%m月%d日')} ~ {sunday.strftime('%Y年%m月%d日')}")
    print(f"🔧 当前系统: {config.system}")
    
    # 采集数据
    print(f"\n📥 正在采集本周数据 ({monday} ~ {sunday})...")
    
    all_sessions = []
    current_date = monday
    
    while current_date <= sunday:
        # Claude Code 数据
        claude_collector = ClaudeCodeCollector()
        claude_data = claude_collector.collect(current_date)
        
        # CodeBuddy 数据
        codebuddy_collector = CodeBuddyCollector()
        codebuddy_data = codebuddy_collector.collect(current_date)
        
        # Git 提交记录
        git_collector = GitCommitsCollector()
        git_data = git_collector.collect(current_date)
        
        day_sessions = claude_data + codebuddy_data + git_data
        all_sessions.extend(day_sessions)
        
        print(f"  - {current_date.strftime('%m-%d')}: {len(day_sessions)} 条")
        current_date += timedelta(days=1)
    
    if all_sessions:
        print(f"✅ 共采集到 {len(all_sessions)} 条会话")
    else:
        print("⚠️ 未采集到任何数据")
    
    # 生成报告
    report = generate_weekly_report(all_sessions, monday, sunday)
    
    # 输出报告
    print("\n" + "="*60)
    print(report)
    print("="*60)
    
    # 保存报告文件（使用配置的报告目录）
    date_str = f"{monday.strftime('%Y%m%d')}-{sunday.strftime('%Y%m%d')}"
    report_file = config.get_report_path("weekly", date_str)
    with open(report_file, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"\n📁 报告已保存: {report_file}")


def generate_weekly_report(sessions, start_date, end_date):
    """生成周报"""
    report = f"""# 📅 周报 - {start_date.strftime('%Y年%m月%d日')} ~ {end_date.strftime('%Y年%m月%d日')}

## 📊 本周概览

| 项目 | 详情 |
|------|------|
| **周期** | {start_date.strftime('%m-%d')} ~ {end_date.strftime('%m-%d')} |
| **总会话数** | {len(sessions)} |
| **工作天数** | 7 天 |

## 🎯 本周成果

"""
    
    # 按数据源分类统计
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
        report += f"### {source_name} ({len(source_sessions)} 次)\n\n"
        for idx, session in enumerate(source_sessions[:8], 1):
            summary = session.summary[:120] + ('...' if len(session.summary) > 120 else '')
            report += f"{idx}. **{session.title}**\n   {summary}\n"
        report += "\n"
    
    report += """## 📈 效率分析

- 工具使用分布...
- 活跃度趋势...

## 🎯 核心成果

（本周最重要的成就...）

## 📋 下周计划

（计划事项...）

---
*AI Journey - 让每一次 AI 协作都被永久记录*
"""
    
    return report


if __name__ == "__main__":
    main()