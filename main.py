#!/usr/bin/env python3
"""
AIJourney - 记录你的 AI 编程成长之旅

主程序入口
"""

import argparse
import logging
import sys
from datetime import date, datetime
from pathlib import Path
from typing import List

from config import init_config, get_config
from collectors import get_all_collector_instances, SessionData
from report import ReportGenerator
from report.period import ReportPeriod


def setup_logging(log_level: str = "INFO", log_dir: Path = None):
    """
    配置日志系统
    
    Args:
        log_level: 日志级别
        log_dir: 日志目录
    """
    # 创建日志目录
    if log_dir:
        log_dir.mkdir(parents=True, exist_ok=True)
    
    # 配置日志格式
    log_format = "%(asctime)s | %(levelname)-8s | %(name)-15s | %(message)s"
    date_format = "%Y-%m-%d %H:%M:%S"
    
    # 配置根日志器
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format=log_format,
        datefmt=date_format,
        handlers=[
            # 控制台输出
            logging.StreamHandler(sys.stdout),
        ]
    )
    
    # 添加文件输出（如果指定了日志目录）
    if log_dir:
        log_file = log_dir / f"aijourney_{date.today().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setFormatter(logging.Formatter(log_format, date_format))
        logging.root.addHandler(file_handler)
    
    logger = logging.getLogger(__name__)
    logger.info("日志系统初始化完成")


def safe_collect(collector, target_date: date) -> List[SessionData]:
    """
    安全执行采集任务
    
    Args:
        collector: 采集器实例
        target_date: 目标日期
    
    Returns:
        会话数据列表
    """
    logger = logging.getLogger(__name__)
    
    try:
        # 验证采集器
        if not collector.validate():
            logger.warning(f"采集器 {collector.name} 验证失败，跳过")
            return []
        
        # 执行采集
        return collector.collect(target_date)
    
    except Exception as e:
        logger.error(f"采集器 {collector.name} 执行失败: {e}", exc_info=True)
        return []


def collect_all(target_date: date, enabled_collectors: List[str] = None) -> List[SessionData]:
    """
    执行所有采集器的采集任务
    
    Args:
        target_date: 目标日期
        enabled_collectors: 启用的采集器列表（None 表示全部启用）
    
    Returns:
        所有会话数据列表
    """
    logger = logging.getLogger(__name__)
    logger.info(f"开始采集 {target_date} 的会话数据")
    
    # 获取所有采集器实例
    all_collectors = get_all_collector_instances()
    logger.info(f"已注册 {len(all_collectors)} 个采集器: {[c.name for c in all_collectors]}")
    
    # 过滤启用的采集器
    if enabled_collectors:
        collectors = [c for c in all_collectors if c.name in enabled_collectors]
        logger.info(f"启用的采集器: {[c.name for c in collectors]}")
    else:
        collectors = all_collectors
    
    # 执行采集
    all_sessions = []
    for collector in collectors:
        logger.info(f"执行采集器: {collector.name}")
        sessions = safe_collect(collector, target_date)
        all_sessions.extend(sessions)
        logger.info(f"采集器 {collector.name} 返回 {len(sessions)} 个会话")
    
    logger.info(f"采集完成，共获取 {len(all_sessions)} 个会话")
    return all_sessions


def generate_report(sessions: List[SessionData], output_dir: Path, daily_report_dir: Path, 
                   output_format: List[str], target_date: date, report_period: str = "daily"):
    """
    生成报告
    
    Args:
        sessions: 会话数据列表
        output_dir: 输出目录
        daily_report_dir: 日报输出目录
        output_format: 输出格式列表
        target_date: 目标日期
        report_period: 报告周期（daily/weekly/monthly/yearly）
    """
    logger = logging.getLogger(__name__)
    
    # 使用报告生成器
    generator = ReportGenerator(output_dir, daily_report_dir)
    
    # 解析报告周期
    period = ReportPeriod.from_string(report_period)
    
    # 根据周期生成报告
    generator.generate_by_period(sessions, target_date, period, output_format)


def main():
    """主函数"""
    # 解析命令行参数
    parser = argparse.ArgumentParser(description="AIJourney - 记录你的 AI 编程成长之旅")
    parser.add_argument(
        "--date",
        type=str,
        default=None,
        help="目标日期（格式：YYYY-MM-DD，默认今天）"
    )
    parser.add_argument(
        "--output",
        type=str,
        default="./output",
        help="输出目录（默认：./output）"
    )
    parser.add_argument(
        "--daily-report-dir",
        type=str,
        default=None,
        help="日报输出目录（默认：同 --output）"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="日志级别（默认：INFO）"
    )
    parser.add_argument(
        "--collectors",
        type=str,
        nargs="+",
        default=None,
        help="启用的采集器（默认：全部）"
    )
    parser.add_argument(
        "--period",
        type=str,
        default="daily",
        choices=["daily", "weekly", "monthly", "yearly", "day", "week", "month", "year"],
        help="报告周期（默认：daily）"
    )
    
    args = parser.parse_args()
    
    # 解析目标日期
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        target_date = date.today()
    
    # 从 settings.json 读取输出配置
    from pathlib import Path
    import json
    settings_path = Path(__file__).parent / "settings.json"
    output_dir = args.output
    daily_report_dir = args.daily_report_dir
    collectors = args.collectors
    report_period = args.period
    
    if settings_path.exists():
        with open(settings_path, 'r', encoding='utf-8') as f:
            settings = json.load(f)
            output_config = settings.get("output", {})
            # 只有当命令行没指定时，才使用 settings.json 中的值
            if not output_dir or output_dir == "./output":
                output_dir = output_config.get("output_dir", "./output")
            if not daily_report_dir:
                daily_report_dir = output_config.get("daily_report_dir", output_dir)
            # 采集器配置优先级：命令行 > settings.json > 默认
            if collectors is None:
                settings_collectors = settings.get("collectors")
                if isinstance(settings_collectors, list) and settings_collectors:
                    collectors = settings_collectors
            # 报告周期配置优先级：命令行 > settings.json > 默认
            if report_period == "daily":
                settings_period = settings.get("report_period")
                if settings_period:
                    report_period = settings_period
    
    # 初始化配置
    init_config(
        output_dir=output_dir,
        daily_report_dir=daily_report_dir,
        log_level=args.log_level,
        enabled_collectors=args.collectors,
        target_date=target_date,
        report_period=report_period,
    )
    
    # 获取配置
    config = get_config()
    
    # 配置日志
    setup_logging(config.log_level, config.log_dir)
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("AIJourney 启动")
    logger.info(f"目标日期: {target_date}")
    logger.info(f"输出目录: {config.output_dir}")
    logger.info(f"日报目录: {config.daily_report_dir}")
    logger.info(f"日志级别: {config.log_level}")
    logger.info("=" * 60)
    
    # 执行采集
    sessions = collect_all(target_date, config.enabled_collectors)
    
    # 生成报告
    generate_report(sessions, config.output_dir, config.daily_report_dir, 
                   config.output_format, target_date, config.report_period)
    
    logger.info("=" * 60)
    logger.info("AIJourney 执行完成")
    logger.info("=" * 60)


if __name__ == "__main__":
    main()
