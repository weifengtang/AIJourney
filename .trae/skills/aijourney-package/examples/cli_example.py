#!/usr/bin/env python3
"""
命令行使用示例

演示如何将AIJourney Skill包装为命令行工具
"""

import argparse
import sys
from datetime import date
from pathlib import Path

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from aijourney import AIJourneySkill


def main():
    parser = argparse.ArgumentParser(
        description="AIJourney Skill - 采集AI编程会话并生成报告"
    )
    
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="目标日期 (YYYY-MM-DD，默认今天)",
    )
    
    parser.add_argument(
        "--period",
        type=str,
        default="daily",
        choices=["daily", "weekly", "monthly", "yearly"],
        help="报告周期 (默认: daily)",
    )
    
    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="输出目录 (默认: ./output)",
    )
    
    parser.add_argument(
        "--collectors",
        type=str,
        nargs="+",
        default=None,
        help="指定采集器 (默认: 全部)",
    )
    
    parser.add_argument(
        "--format",
        type=str,
        nargs="+",
        default=["json", "markdown"],
        choices=["json", "markdown"],
        help="输出格式 (默认: json markdown)",
    )
    
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别 (默认: INFO)",
    )
    
    args = parser.parse_args()
    
    # 解析日期
    if args.date:
        target_date = date.fromisoformat(args.date)
    else:
        target_date = date.today()
    
    # 创建Skill实例
    skill = AIJourneySkill(
        output_dir=args.output,
        log_level=args.log_level,
    )
    
    # 加载内置采集器
    skill.load_builtin_collectors()
    
    # 运行
    print(f"🚀 AIJourney Skill 启动")
    print(f"   日期: {target_date}")
    print(f"   周期: {args.period}")
    print(f"   输出: {args.output}")
    print()
    
    result = skill.run(
        target_date=target_date,
        period=args.period,
        collector_names=args.collectors,
        formats=args.format,
    )
    
    # 输出结果
    print(f"\n✅ 执行完成!")
    print(f"   采集会话: {result['session_count']} 个")
    print(f"   报告文件:")
    for f in result['report']['files']:
        print(f"     - {f}")


if __name__ == "__main__":
    main()
