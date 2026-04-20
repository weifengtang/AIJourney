#!/usr/bin/env python3
"""
/range-report - 日期区间报告（默认 AI 增强）

支持指定任意日期范围生成 AI 增强的汇总报告
"""

import argparse
import sys
import logging
from datetime import date, timedelta, datetime
from pathlib import Path

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from collectors.base import collect_all
from llm.report_enhancer import ReportEnhancer, LLMConfig
from config import get_config, is_running_in_claude_code


def setup_logging(config):
    """设置日志配置"""
    log_dir = config.log_dir
    log_dir.mkdir(parents=True, exist_ok=True)
    
    log_file = log_dir / f"aijourney_{date.today().strftime('%Y%m%d')}.log"
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)


def log_execution(log, step, message):
    """记录执行日志"""
    log.info(f"[{step}] {message}")


def parse_date(date_str: str) -> date:
    """解析日期字符串"""
    from datetime import datetime
    formats = ['%Y-%m-%d', '%Y%m%d', '%Y/%m/%d', '%d-%m-%Y']
    for fmt in formats:
        try:
            return datetime.strptime(date_str, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"无法解析日期: {date_str}")


def get_week_range(target_date: date = None) -> tuple:
    """获取指定日期所在周的范围（周一到周日）"""
    if target_date is None:
        target_date = date.today()
    start_of_week = target_date - timedelta(days=target_date.weekday())
    end_of_week = start_of_week + timedelta(days=6)
    return start_of_week, end_of_week


def get_month_range(target_date: date = None) -> tuple:
    """获取指定日期所在月的范围"""
    if target_date is None:
        target_date = date.today()
    start_of_month = date(target_date.year, target_date.month, 1)
    if target_date.month == 12:
        end_of_month = date(target_date.year + 1, 1, 1) - timedelta(days=1)
    else:
        end_of_month = date(target_date.year, target_date.month + 1, 1) - timedelta(days=1)
    return start_of_month, end_of_month


def collect_range_data(start_date: date, end_date: date) -> list:
    """采集指定日期区间的数据"""
    all_sessions = []
    current_date = start_date
    
    while current_date <= end_date:
        sessions = collect_all(current_date)
        all_sessions.extend(sessions)
        current_date += timedelta(days=1)
    
    return all_sessions


def generate_period_summary(sessions: list, start_date: date, end_date: date, use_ai: bool = True) -> str:
    """生成周期汇总报告（默认使用 AI 增强）"""
    config = get_config()
    
    if use_ai:
        llm_config = LLMConfig(config)
        enhancer = ReportEnhancer(llm_config)
        return enhancer.enhance_weekly_report(sessions, start_date, end_date)
    
    # 手动生成报告
    days = (end_date - start_date).days + 1
    
    report = f"""# 📅 区间报告 - {start_date.strftime('%Y年%m月%d日')} ~ {end_date.strftime('%Y年%m月%d日')}

## 📊 概览

| 项目 | 详情 |
|------|------|
| **周期** | {start_date.strftime('%Y-%m-%d')} ~ {end_date.strftime('%Y-%m-%d')} |
| **天数** | {days} 天 |
| **总会话数** | {len(sessions)} |

## 🎯 成果汇总

### Claude Code ({len([s for s in sessions if s.get('source') == 'claude_code'])} 次)
"""
    
    # 按日期分组
    date_groups = {}
    for session in sessions:
        session_date = session.get('date', '')
        if session_date not in date_groups:
            date_groups[session_date] = []
        date_groups[session_date].append(session)
    
    for session_date in sorted(date_groups.keys()):
        report += f"\n#### {session_date}\n"
        for i, session in enumerate(date_groups[session_date], 1):
            title = session.get('title', '无标题')[:50] + '...' if len(session.get('title', '')) > 50 else session.get('title', '无标题')
            report += f"{i}. **{title}**\n"
    
    report += """

---
*AI Journey - 让每一次 AI 协作都被永久记录*
"""
    
    return report


def main():
    parser = argparse.ArgumentParser(description='生成日期区间报告（默认 AI 增强）')
    parser.add_argument('--start', '-s', type=str, help='开始日期 (YYYY-MM-DD)')
    parser.add_argument('--end', '-e', type=str, help='结束日期 (YYYY-MM-DD)')
    parser.add_argument('--days', '-d', type=int, help='最近N天')
    parser.add_argument('--week', '-w', action='store_true', help='本周')
    parser.add_argument('--month', '-m', action='store_true', help='本月')
    parser.add_argument('--no-ai', action='store_true', help='禁用 AI 增强')
    parser.add_argument('--output', '-o', type=str, help='输出文件路径')
    
    args = parser.parse_args()
    config = get_config()
    is_claude_env = is_running_in_claude_code()
    
    # 设置日志
    log = setup_logging(config)
    start_time = datetime.now()
    
    today = date.today()
    start_date = None
    end_date = None
    
    try:
        # 解析日期参数
        if args.week:
            start_date, end_date = get_week_range(today)
        elif args.month:
            start_date, end_date = get_month_range(today)
        elif args.days:
            end_date = today
            start_date = today - timedelta(days=args.days - 1)
        elif args.start and args.end:
            start_date = parse_date(args.start)
            end_date = parse_date(args.end)
        else:
            parser.print_help()
            sys.exit(1)
        
        log_execution(log, "START", f"开始生成区间报告，日期范围: {start_date} 至 {end_date}")
        
        # 验证日期
        if start_date > end_date:
            print("错误: 开始日期不能晚于结束日期")
            sys.exit(1)
        
        # 采集数据
        log_execution(log, "COLLECT", f"开始采集 {start_date} 至 {end_date} 的数据")
        sessions = collect_range_data(start_date, end_date)
        log_execution(log, "COLLECT", f"数据采集完成，共 {len(sessions)} 条会话")
        
        # 生成报告（默认使用 AI 增强）
        use_ai = not args.no_ai
        log_execution(log, "LLM", f"开始生成报告，AI 增强: {'启用' if use_ai else '禁用'}")
        report = generate_period_summary(sessions, start_date, end_date, use_ai)
        log_execution(log, "LLM", "报告生成完成")
        
        # 输出报告（适合 Skill 场景）
        print(report)
        
        # 保存报告
        if args.output:
            output_path = Path(args.output)
        else:
            period_str = f"{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}"
            output_path = config.report_dir / f"range_report_{period_str}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report)
        log_execution(log, "SAVE", f"报告已保存: {output_path}")
        
        # 仅在非 Claude Code 环境输出保存信息
        if not is_claude_env:
            print(f"\n📁 报告已保存: {output_path}")
        
        # 记录执行时间
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_execution(log, "END", f"区间报告生成完成，耗时: {duration:.2f} 秒")
        
    except Exception as e:
        log_execution(log, "ERROR", f"区间报告生成失败: {str(e)}")
        raise


if __name__ == '__main__':
    main()
