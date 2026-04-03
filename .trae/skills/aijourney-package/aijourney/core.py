"""
AIJourney Skill 核心模块
"""

import logging
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import List, Optional, Dict, Any, Callable
import json


@dataclass
class SessionData:
    """会话数据结构"""
    session_id: str
    tool_name: str
    start_time: datetime
    end_time: Optional[datetime] = None
    messages: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "tool_name": self.tool_name,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "messages": self.messages,
            "metadata": self.metadata,
        }


class BaseCollector:
    """采集器基类"""
    
    name: str = "base"
    description: str = ""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
    
    def validate(self) -> bool:
        """验证采集器是否可用"""
        return True
    
    def collect(self, target_date: date) -> List[SessionData]:
        """采集数据"""
        raise NotImplementedError


# 采集器注册表
_COLLECTORS: Dict[str, type] = {}


def register_collector(collector_class: type) -> type:
    """注册采集器装饰器"""
    _COLLECTORS[collector_class.name] = collector_class
    return collector_class


def get_all_collectors() -> Dict[str, type]:
    """获取所有注册的采集器"""
    return _COLLECTORS.copy()


class AIJourneySkill:
    """
    AIJourney Skill 主类
    
    提供完整的会话采集和报告生成功能
    """
    
    def __init__(
        self,
        output_dir: str = "./output",
        log_level: str = "INFO",
        config: Optional[Dict[str, Any]] = None,
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.config = config or {}
        
        # 配置日志
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s | %(levelname)-8s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        self.logger = logging.getLogger(__name__)
        
        # 采集器实例
        self._collectors: Dict[str, BaseCollector] = {}
    
    def register_collector(self, collector_class: type) -> "AIJourneySkill":
        """注册自定义采集器"""
        instance = collector_class(self.config.get(collector_class.name, {}))
        self._collectors[collector_class.name] = instance
        self.logger.info(f"注册采集器: {collector_class.name}")
        return self
    
    def load_builtin_collectors(self) -> "AIJourneySkill":
        """加载内置采集器"""
        # 自动导入并注册所有内置采集器
        try:
            from . import collectors as cols
            for name, collector_class in get_all_collectors().items():
                if name not in self._collectors:
                    self.register_collector(collector_class)
        except ImportError:
            self.logger.warning("没有内置采集器可用")
        return self
    
    def collect(
        self,
        target_date: Optional[date] = None,
        collector_names: Optional[List[str]] = None,
    ) -> List[SessionData]:
        """
        采集会话数据
        
        Args:
            target_date: 目标日期，默认今天
            collector_names: 指定采集器，None表示全部
        
        Returns:
            会话数据列表
        """
        if target_date is None:
            target_date = date.today()
        
        sessions = []
        collectors_to_use = collector_names or list(self._collectors.keys())
        
        self.logger.info(f"开始采集 {target_date} 的数据")
        
        for name in collectors_to_use:
            if name not in self._collectors:
                self.logger.warning(f"采集器 {name} 未注册")
                continue
            
            collector = self._collectors[name]
            try:
                if collector.validate():
                    data = collector.collect(target_date)
                    sessions.extend(data)
                    self.logger.info(f"✓ {name}: {len(data)} 个会话")
                else:
                    self.logger.warning(f"✗ {name}: 验证失败")
            except Exception as e:
                self.logger.error(f"✗ {name}: {e}")
        
        return sessions
    
    def generate_report(
        self,
        sessions: List[SessionData],
        period: str = "daily",
        formats: List[str] = None,
        target_date: Optional[date] = None,
    ) -> Dict[str, Any]:
        """
        生成报告
        
        Args:
            sessions: 会话数据
            period: 周期 (daily/weekly/monthly/yearly)
            formats: 格式列表 ["json", "markdown"]
            target_date: 目标日期
        
        Returns:
            报告信息
        """
        if formats is None:
            formats = ["json", "markdown"]
        if target_date is None:
            target_date = date.today()
        
        report_info = {
            "period": period,
            "date": target_date.isoformat(),
            "session_count": len(sessions),
            "formats": formats,
            "files": [],
        }
        
        # 生成JSON报告
        if "json" in formats:
            json_file = self._generate_json_report(sessions, period, target_date)
            report_info["files"].append(str(json_file))
        
        # 生成Markdown报告
        if "markdown" in formats:
            md_file = self._generate_markdown_report(sessions, period, target_date)
            report_info["files"].append(str(md_file))
        
        return report_info
    
    def _generate_json_report(
        self,
        sessions: List[SessionData],
        period: str,
        target_date: date,
    ) -> Path:
        """生成JSON报告"""
        filename = f"{period}_report_{target_date.strftime('%Y%m%d')}.json"
        filepath = self.output_dir / filename
        
        data = {
            "period": period,
            "date": target_date.isoformat(),
            "generated_at": datetime.now().isoformat(),
            "session_count": len(sessions),
            "sessions": [s.to_dict() for s in sessions],
        }
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        self.logger.info(f"生成JSON报告: {filepath}")
        return filepath
    
    def _generate_markdown_report(
        self,
        sessions: List[SessionData],
        period: str,
        target_date: date,
    ) -> Path:
        """生成Markdown报告"""
        filename = f"{period}_report_{target_date.strftime('%Y%m%d')}.md"
        filepath = self.output_dir / filename
        
        content = f"""# {period.capitalize()} Report - {target_date}

## Overview

- **Date**: {target_date}
- **Period**: {period}
- **Total Sessions**: {len(sessions)}

## Sessions

"""
        
        for session in sessions:
            content += f"""### {session.tool_name} - {session.session_id}

- **Start**: {session.start_time}
- **Messages**: {len(session.messages)}

"""
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        self.logger.info(f"生成Markdown报告: {filepath}")
        return filepath
    
    def run(
        self,
        target_date: Optional[date] = None,
        period: str = "daily",
        collector_names: Optional[List[str]] = None,
        formats: List[str] = None,
    ) -> Dict[str, Any]:
        """
        一键运行：采集 + 生成报告
        
        Returns:
            完整执行结果
        """
        if target_date is None:
            target_date = date.today()
        if formats is None:
            formats = ["json", "markdown"]
        
        # 采集
        sessions = self.collect(target_date, collector_names)
        
        # 生成报告
        report_info = self.generate_report(sessions, period, formats, target_date)
        
        return {
            "success": True,
            "target_date": target_date.isoformat(),
            "period": period,
            "session_count": len(sessions),
            "report": report_info,
        }
