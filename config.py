"""
AIJourney 配置管理模块

负责管理全局配置，包括输出路径、日志配置、采集器启用状态等
"""

from dataclasses import dataclass, field
from datetime import datetime, date
from pathlib import Path
from typing import List, Optional
import json


@dataclass
class Config:
    """全局配置"""
    
    # 输出配置
    output_dir: Path = field(default_factory=lambda: Path("./output"))
    daily_report_dir: Path = field(default_factory=lambda: Path("./output"))
    output_format: List[str] = field(default_factory=lambda: ["json", "markdown"])
    
    # 报告周期配置
    report_period: str = "daily"  # daily, weekly, monthly, yearly
    
    # 采集配置
    enabled_collectors: List[str] = field(
        default_factory=lambda: [
            "claude_code", "codebuddy", "vscode", "idea", "doubao_selenium",
            "shell_history", "git_commits",
        ]
    )
    target_date: date = field(default_factory=date.today)
    
    # 日志配置
    log_level: str = "INFO"
    log_dir: Path = field(default_factory=lambda: Path("./logs"))
    
    # 数据源路径（macOS）
    claude_code_path: Path = field(
        default_factory=lambda: Path.home() / ".claude"
    )
    vscode_history_path: Path = field(
        default_factory=lambda: Path.home() / "Library" / "Application Support" / "Code" / "User" / "History"
    )
    idea_config_path: Path = field(
        default_factory=lambda: Path.home() / "Library" / "Application Support" / "JetBrains"
    )
    codebuddy_storage_path: Path = field(
        default_factory=lambda: Path.home() / "Library" / "Application Support" / "CodeBuddyExtension" / "Data"
    )
    
    def __post_init__(self):
        """初始化后处理：确保路径为 Path 对象"""
        self.output_dir = Path(self.output_dir)
        self.daily_report_dir = Path(self.daily_report_dir)
        self.log_dir = Path(self.log_dir)
        self.claude_code_path = Path(self.claude_code_path)
        self.vscode_history_path = Path(self.vscode_history_path)
        self.idea_config_path = Path(self.idea_config_path)
        self.codebuddy_storage_path = Path(self.codebuddy_storage_path)
    
    def to_dict(self) -> dict:
        """转换为字典（用于序列化）"""
        return {
            "output_dir": str(self.output_dir),
            "daily_report_dir": str(self.daily_report_dir),
            "output_format": self.output_format,
            "report_period": self.report_period,
            "enabled_collectors": self.enabled_collectors,
            "target_date": self.target_date.isoformat(),
            "log_level": self.log_level,
            "log_dir": str(self.log_dir),
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "Config":
        """从字典创建配置（用于反序列化）"""
        if "target_date" in data:
            data["target_date"] = date.fromisoformat(data["target_date"])
        return cls(**data)
    
    def save_to_file(self, file_path: Path):
        """保存配置到文件"""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
    
    @classmethod
    def load_from_file(cls, file_path: Path) -> "Config":
        """从文件加载配置"""
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return cls.from_dict(data)


# 全局配置实例
_config: Optional[Config] = None


def get_config() -> Config:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = Config()
    return _config


def set_config(config: Config):
    """设置全局配置"""
    global _config
    _config = config


def init_config(
    output_dir: Optional[str] = None,
    daily_report_dir: Optional[str] = None,
    log_level: Optional[str] = None,
    enabled_collectors: Optional[List[str]] = None,
    target_date: Optional[date] = None,
    report_period: Optional[str] = None,
) -> Config:
    """
    初始化配置
    
    Args:
        output_dir: 输出目录
        daily_report_dir: 日报输出目录
        log_level: 日志级别
        enabled_collectors: 启用的采集器列表
        target_date: 目标日期
        report_period: 报告周期（daily/weekly/monthly/yearly）
    
    Returns:
        配置实例
    """
    global _config
    
    _config = Config()
    
    if output_dir:
        _config.output_dir = Path(output_dir)
    if daily_report_dir:
        _config.daily_report_dir = Path(daily_report_dir)
    if log_level:
        _config.log_level = log_level
    if enabled_collectors:
        _config.enabled_collectors = enabled_collectors
    if target_date:
        _config.target_date = target_date
    if report_period:
        _config.report_period = report_period
    
    return _config
