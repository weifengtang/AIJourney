#!/usr/bin/env python3
"""
AIJourney Skill 基础使用示例
"""

from aijourney import AIJourneySkill
from datetime import date, timedelta


def example_1_basic():
    """示例1：基础使用"""
    print("=" * 60)
    print("示例1：基础使用")
    print("=" * 60)
    
    # 创建Skill实例
    skill = AIJourneySkill(
        output_dir="./output",
        log_level="INFO",
    )
    
    # 加载内置采集器
    skill.load_builtin_collectors()
    
    # 一键运行
    result = skill.run(period="daily")
    
    print(f"\n执行结果:")
    print(f"  日期: {result['target_date']}")
    print(f"  周期: {result['period']}")
    print(f"  会话数: {result['session_count']}")
    print(f"  报告文件: {result['report']['files']}")


def example_2_step_by_step():
    """示例2：分步执行"""
    print("\n" + "=" * 60)
    print("示例2：分步执行")
    print("=" * 60)
    
    skill = AIJourneySkill(output_dir="./output")
    skill.load_builtin_collectors()
    
    # 指定日期采集
    yesterday = date.today() - timedelta(days=1)
    sessions = skill.collect(target_date=yesterday)
    
    print(f"\n采集到 {len(sessions)} 个会话")
    
    # 生成周报
    report = skill.generate_report(
        sessions=sessions,
        period="weekly",
        formats=["json", "markdown"],
        target_date=yesterday,
    )
    
    print(f"报告已生成: {report['files']}")


def example_3_custom_collectors():
    """示例3：指定采集器"""
    print("\n" + "=" * 60)
    print("示例3：指定采集器")
    print("=" * 60)
    
    skill = AIJourneySkill(output_dir="./output")
    skill.load_builtin_collectors()
    
    # 只使用特定采集器
    result = skill.run(
        collector_names=["shell_history", "git_commits"],
        period="daily",
    )
    
    print(f"使用指定采集器，采集到 {result['session_count']} 个会话")


if __name__ == "__main__":
    example_1_basic()
    example_2_step_by_step()
    example_3_custom_collectors()
    
    print("\n" + "=" * 60)
    print("所有示例执行完成！")
    print("=" * 60)
