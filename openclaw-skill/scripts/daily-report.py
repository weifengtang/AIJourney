#!/usr/bin/env python3
"""
/daily-report - AI 增强日报（默认）

作为 Claude Code Skill 使用，自动采集数据并使用内置 LLM 生成智能日报
"""

import sys
import os
import logging
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from collectors.claude_code import ClaudeCodeCollector
from collectors.codebuddy import CodeBuddyCollector
from collectors.git_commits import GitCommitsCollector
from llm.report_enhancer import ReportEnhancer, LLMConfig
from datetime import date
from typing import Dict
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


def log_execution(log, config, step, message):
    """记录执行日志"""
    log.info(f"[{step}] {message}")


def main():
    config = get_config()
    today = date.today()
    is_claude_env = is_running_in_claude_code()
    
    # 设置日志
    log = setup_logging(config)
    start_time = datetime.now()
    
    log_execution(log, config, "START", f"开始生成日报，日期: {today}")
    
    try:
        # 采集数据
        log_execution(log, config, "COLLECT", "开始采集 Claude Code 数据")
        claude_collector = ClaudeCodeCollector()
        claude_data = claude_collector.collect(today)
        log_execution(log, config, "COLLECT", f"Claude Code 采集完成，获取 {len(claude_data)} 条记录")
        
        log_execution(log, config, "COLLECT", "开始采集 CodeBuddy 数据")
        codebuddy_collector = CodeBuddyCollector()
        codebuddy_data = codebuddy_collector.collect(today)
        log_execution(log, config, "COLLECT", f"CodeBuddy 采集完成，获取 {len(codebuddy_data)} 条记录")
        
        log_execution(log, config, "COLLECT", "开始采集 Git 提交记录")
        git_collector = GitCommitsCollector()
        git_data = git_collector.collect(today)
        log_execution(log, config, "COLLECT", f"Git 采集完成，获取 {len(git_data)} 条记录")
        
        all_sessions = claude_data + codebuddy_data + git_data
        log_execution(log, config, "COLLECT", f"数据采集完成，共 {len(all_sessions)} 条会话")
        
        # 转换为字典格式
        sessions_dict = [session_to_dict(session) for session in all_sessions]
        
        # 初始化报告增强器（自动使用 Claude Code 内置 LLM）
        log_execution(log, config, "LLM", "初始化报告增强器")
        llm_config = LLMConfig(config)
        enhancer = ReportEnhancer(llm_config)
        
        # 生成 AI 增强报告
        log_execution(log, config, "LLM", "开始生成 AI 增强报告")
        report = enhancer.enhance_daily_report(sessions_dict, today)
        log_execution(log, config, "LLM", "AI 增强报告生成完成")
        
        # 主要输出报告（适合 Skill 场景）
        print(report)
        
        # 保存报告文件
        report_file = config.get_report_path("daily", today.strftime('%Y%m%d'))
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        log_execution(log, config, "SAVE", f"报告已保存: {report_file}")
        
        # 仅在非 Claude Code 环境输出保存信息
        if not is_claude_env:
            print(f"\n📁 报告已保存: {report_file}")
        
        # 记录执行时间
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        log_execution(log, config, "END", f"日报生成完成，耗时: {duration:.2f} 秒")
        
    except Exception as e:
        log_execution(log, config, "ERROR", f"日报生成失败: {str(e)}")
        raise


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