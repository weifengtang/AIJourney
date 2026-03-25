"""
报告生成器

生成完整的日报，符合规范格式
"""

import json
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional
from collections import defaultdict
import logging

from collectors.base import SessionData
from report.summarizer import SessionSummarizer


logger = logging.getLogger(__name__)


class ReportGenerator:
    """报告生成器"""
    
    def __init__(self, output_dir: Path, settings_path: Optional[Path] = None):
        """
        初始化报告生成器
        
        Args:
            output_dir: 输出目录
            settings_path: settings.json 路径
        """
        self.output_dir = output_dir
        self.summarizer = SessionSummarizer(settings_path)
    
    def generate(self, sessions: List[SessionData], target_date: date, output_format: List[str]):
        """
        生成报告
        
        Args:
            sessions: 会话数据列表
            target_date: 目标日期
            output_format: 输出格式列表
        """
        # 创建输出目录
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # 如果没有会话数据，不生成空文件
        if not sessions:
            logger.info(f"[{target_date}] 没有采集到会话数据，跳过生成报告")
            return
        
        # 生成文件名
        date_str = target_date.strftime("%Y%m%d")
        
        # 生成 JSON 报告
        if "json" in output_format:
            json_file = self.output_dir / f"daily_report_{date_str}.json"
            self._generate_json_report(sessions, target_date, json_file)
            logger.info(f"JSON 报告已生成: {json_file}")
        
        # 生成 Markdown 报告
        if "markdown" in output_format:
            md_file = self.output_dir / f"daily_report_{date_str}.md"
            self._generate_markdown_report(sessions, target_date, md_file)
            logger.info(f"Markdown 报告已生成: {md_file}")
    
    def _generate_json_report(self, sessions: List[SessionData], target_date: date, output_file: Path):
        """
        生成 JSON 格式的报告
        
        Args:
            sessions: 会话数据列表
            target_date: 目标日期
            output_file: 输出文件路径
        """
        # 统计数据
        stats = self._calculate_stats(sessions)
        
        # 为每个会话生成摘要
        sessions_data = []
        for session in sessions:
            session_dict = session.to_dict()
            # 生成摘要
            summary = self.summarizer.summarize(session)
            session_dict["summary"] = summary.to_dict()
            sessions_data.append(session_dict)
        
        # 构建报告数据
        report_data = {
            "meta": {
                "date": target_date.isoformat(),
                "generated_at": datetime.now().isoformat(),
                "version": "2.1.0",
            },
            "stats": stats,
            "sessions": sessions_data,
        }
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
    
    def _generate_markdown_report(self, sessions: List[SessionData], target_date: date, output_file: Path):
        """
        生成 Markdown 格式的报告
        
        Args:
            sessions: 会话数据列表
            target_date: 目标日期
            output_file: 输出文件路径
        """
        # 统计数据
        stats = self._calculate_stats(sessions)
        
        # 生成 Markdown 内容
        lines = []
        
        # 标题
        weekday_names = ['一', '二', '三', '四', '五', '六', '日']
        weekday = weekday_names[target_date.weekday()]
        lines.extend([
            f"# 今日工作总结 - {target_date.strftime('%Y年%m月%d日')}（星期{weekday}）",
            "",
            f"> 报告生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"> 数据来源：{', '.join(stats['sources']) if stats['sources'] else '无'}",
            "",
            "---",
            "",
        ])
        
        # 工作概览
        lines.extend(self._generate_overview_section(sessions, stats))
        
        # 今日成果
        if sessions:
            lines.extend(self._generate_achievements_section(sessions, stats))
        
        # 效率分析
        lines.extend(self._generate_efficiency_section(sessions, stats))
        
        # 技术成长
        lines.extend(self._generate_learning_section(sessions, stats))
        
        # 明日计划（占位，需要用户手动填写）
        lines.extend(self._generate_plan_section())
        
        # 思考与改进
        lines.extend(self._generate_reflection_section(sessions, stats))
        
        # 附录
        lines.extend(self._generate_appendix_section(sessions, stats))
        
        # 写入文件
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
    
    def _calculate_stats(self, sessions: List[SessionData]) -> Dict:
        """
        计算统计数据
        
        Args:
            sessions: 会话数据列表
        
        Returns:
            统计数据字典
        """
        if not sessions:
            return {
                "total_sessions": 0,
                "total_messages": 0,
                "total_tokens_input": 0,
                "total_tokens_output": 0,
                "total_files_modified": 0,
                "sources": [],
                "projects": [],
                "duration_minutes": 0,
            }
        
        # 计算时间范围（统一去除时区信息避免比较错误）
        start_times = [s.start_time.replace(tzinfo=None) for s in sessions if s.start_time]
        end_times = [s.end_time.replace(tzinfo=None) for s in sessions if s.end_time]
        
        if start_times and end_times:
            earliest = min(start_times)
            latest = max(end_times)
            duration_minutes = int((latest - earliest).total_seconds() / 60)
        else:
            duration_minutes = 0
        
        # 统计来源
        sources = list(set(s.source for s in sessions))
        
        # 统计项目
        projects = list(set(s.project_path for s in sessions if s.project_path))
        
        # 统计消息数
        total_messages = sum(len(s.messages) for s in sessions)
        
        # 统计 token
        total_tokens_input = sum(s.tokens_input for s in sessions)
        total_tokens_output = sum(s.tokens_output for s in sessions)
        
        # 统计文件数
        total_files_modified = sum(len(s.files_modified) for s in sessions)
        
        return {
            "total_sessions": len(sessions),
            "total_messages": total_messages,
            "total_tokens_input": total_tokens_input,
            "total_tokens_output": total_tokens_output,
            "total_files_modified": total_files_modified,
            "sources": sources,
            "projects": projects,
            "duration_minutes": duration_minutes,
        }
    
    def _generate_overview_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成概览部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 📊 工作概览",
            "",
            "### 核心指标",
            "",
            "| 指标 | 数值 | 说明 |",
            "|------|------|------|",
        ]
        
        # 工作时长
        hours = stats['duration_minutes'] // 60
        minutes = stats['duration_minutes'] % 60
        duration_str = f"{hours}小时{minutes}分" if hours > 0 else f"{minutes}分钟"
        lines.append(f"| 工作总时长 | {duration_str} | 首次到最后一次活动时间 |")
        
        # AI 辅助会话数
        lines.append(f"| AI 辅助会话 | {stats['total_sessions']} 次 | 所有工具合计 |")
        
        # 消息数
        lines.append(f"| 消息总数 | {stats['total_messages']} 条 | 用户+AI消息 |")
        
        # Token 统计
        total_tokens = stats['total_tokens_input'] + stats['total_tokens_output']
        if total_tokens > 0:
            lines.append(f"| Token 总量 | {total_tokens:,} | 输入 {stats['total_tokens_input']:,} + 输出 {stats['total_tokens_output']:,} |")
        
        # 文件修改数
        lines.append(f"| 编辑文件数 | {stats['total_files_modified']} | 所有工具合计 |")
        
        lines.extend(["", "### 时间分布", ""])
        
        # 按来源统计会话数
        source_counts = defaultdict(int)
        for session in sessions:
            source_counts[session.source] += 1
        
        if source_counts:
            lines.append("```")
            for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True):
                percentage = int(count / len(sessions) * 100)
                bar_length = int(percentage / 5)
                bar = '█' * bar_length
                lines.append(f"{source:15} {bar:20} {percentage:3}% ({count}次)")
            lines.append("```")
        
        lines.extend(["", "---", ""])
        
        return lines
    
    def _generate_achievements_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成今日成果部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 🎯 今日成果",
            "",
            "### AI 协作会话",
            "",
        ]
        
        # 按来源分组
        sessions_by_source = defaultdict(list)
        for session in sessions:
            sessions_by_source[session.source].append(session)
        
        # 展示每个来源的会话
        for source in sorted(sessions_by_source.keys()):
            source_sessions = sessions_by_source[source]
            
            lines.append(f"#### {source.upper()} ({len(source_sessions)} 个会话)")
            lines.append("")
            
            for i, session in enumerate(source_sessions, 1):
                # 会话标题
                title = session.title or f"会话 {session.session_id[:8]}"
                lines.append(f"**{i}. {title}**")
                lines.append("")
                
                # 生成摘要
                summary = self.summarizer.summarize(session)
                
                # 会话信息
                if session.project_path:
                    lines.append(f"- **项目**: `{session.project_path}`")
                
                lines.append(f"- **时间**: {session.start_time.strftime('%H:%M')} - {session.end_time.strftime('%H:%M') if session.end_time else '进行中'}")
                
                # 使用生成的摘要
                summary_md = summary.to_markdown()
                if summary_md:
                    lines.append("")
                    lines.append("**会话摘要**")
                    lines.append(summary_md)
                
                # Token 统计
                if session.tokens_input + session.tokens_output > 0:
                    lines.append(f"- **Token**: 输入 {session.tokens_input:,} / 输出 {session.tokens_output:,}")
                
                lines.append("")
            
            lines.append("---")
            lines.append("")
        
        return lines
    
    def _generate_efficiency_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成效率分析部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 📈 效率分析",
            "",
            "### AI 协作效果",
            "",
            "| AI 工具 | 使用时长 | 会话数 | Token 消耗 |",
            "|---------|----------|--------|------------|",
        ]
        
        # 按来源统计
        source_stats = defaultdict(lambda: {"count": 0, "duration": 0, "tokens_in": 0, "tokens_out": 0})
        for session in sessions:
            source_stats[session.source]["count"] += 1
            if session.start_time and session.end_time:
                source_stats[session.source]["duration"] += (session.end_time - session.start_time).seconds // 60
            source_stats[session.source]["tokens_in"] += session.tokens_input
            source_stats[session.source]["tokens_out"] += session.tokens_output
        
        for source, data in sorted(source_stats.items()):
            hours = data["duration"] // 60
            mins = data["duration"] % 60
            duration_str = f"{hours}h{mins}m" if hours > 0 else f"{mins}m"
            total_tokens = data["tokens_in"] + data["tokens_out"]
            lines.append(f"| {source} | {duration_str} | {data['count']} | {total_tokens:,} |")
        
        lines.extend([
            "",
            "### 工具使用效率",
            "",
            "| 工具 | 会话数 | 消息数 | 平均消息/会话 |",
            "|------|--------|--------|---------------|",
        ])
        
        for source, data in sorted(source_stats.items()):
            msg_count = sum(len(s.messages) for s in sessions if s.source == source)
            avg_msg = msg_count / data["count"] if data["count"] > 0 else 0
            lines.append(f"| {source} | {data['count']} | {msg_count} | {avg_msg:.1f} |")
        
        lines.extend(["", "---", ""])
        
        return lines
    
    def _generate_learning_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成技术成长部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 🔧 技术成长",
            "",
            "### 今日学习",
            "",
        ]
        
        # 从会话标题中提取学习点（简化版）
        topics = []
        for session in sessions[:5]:  # 最多取5个会话
            if session.title:
                topics.append(f"- **{session.title[:50]}**")
        
        if topics:
            lines.extend(topics)
        else:
            lines.append("- 暂无记录")
        
        lines.extend([
            "",
            "### 技术栈使用",
            "",
            "| 技术 | 使用时长 | 说明 |",
            "|------|----------|------|",
        ])
        
        # 根据来源推断技术栈
        tech_usage = defaultdict(int)
        for session in sessions:
            if "claude" in session.source.lower():
                tech_usage["AI 协作"] += 1
            if session.project_path:
                tech_usage["项目开发"] += 1
        
        for tech, count in sorted(tech_usage.items(), key=lambda x: x[1], reverse=True):
            lines.append(f"| {tech} | {count} 次 | - |")
        
        lines.extend(["", "---", ""])
        
        return lines
    
    def _generate_plan_section(self) -> List[str]:
        """
        生成明日计划部分（占位）
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 📝 明日计划",
            "",
            "### 优先级 P0（必须完成）",
            "- [ ] _请手动填写_",
            "",
            "### 优先级 P1（争取完成）",
            "- [ ] _请手动填写_",
            "",
            "### 优先级 P2（如有时间）",
            "- [ ] _请手动填写_",
            "",
            "---",
            "",
        ]
        
        return lines
    
    def _generate_reflection_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成思考与改进部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 💡 思考与改进",
            "",
            "### 今日亮点",
        ]
        
        # 自动提取亮点
        if stats['total_sessions'] > 0:
            lines.append(f"- 完成 {stats['total_sessions']} 个 AI 协作会话")
        if stats['total_tokens_input'] + stats['total_tokens_output'] > 10000:
            lines.append(f"- Token 消耗量：{stats['total_tokens_input'] + stats['total_tokens_output']:,}")
        if stats['total_messages'] > 50:
            lines.append(f"- 高频交互：{stats['total_messages']} 条消息")
        
        lines.extend([
            "",
            "### 遇到的问题",
            "- _请手动填写_",
            "",
            "### 改进建议",
            "- _请手动填写_",
            "",
            "---",
            "",
        ])
        
        return lines
    
    def _generate_appendix_section(self, sessions: List[SessionData], stats: Dict) -> List[str]:
        """
        生成附录部分
        
        Args:
            sessions: 会话数据列表
            stats: 统计数据
        
        Returns:
            Markdown 行列表
        """
        lines = [
            "## 📎 附录：详细数据",
            "",
            "### 会话详细记录",
            "",
        ]
        
        # 按来源列出会话
        sessions_by_source = defaultdict(list)
        for session in sessions:
            sessions_by_source[session.source].append(session)
        
        for source in sorted(sessions_by_source.keys()):
            source_sessions = sessions_by_source[source]
            lines.append(f"- **{source.upper()}**: {len(source_sessions)} 个会话")
            for session in source_sessions[:3]:  # 最多显示3个
                title = session.title or session.session_id[:8]
                lines.append(f"  - {title}")
            if len(source_sessions) > 3:
                lines.append(f"  - ... 还有 {len(source_sessions) - 3} 个会话")
        
        lines.extend([
            "",
            "---",
            "",
            "**报告结束**",
        ])
        
        return lines
