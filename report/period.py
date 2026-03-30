"""
报告周期枚举

定义支持的报告周期类型
"""

from enum import Enum
from datetime import date, timedelta
from typing import Tuple


class ReportPeriod(Enum):
    """报告周期枚举"""
    
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"
    
    def get_display_name(self) -> str:
        """获取显示名称"""
        return {
            ReportPeriod.DAILY: "日报",
            ReportPeriod.WEEKLY: "周报",
            ReportPeriod.MONTHLY: "月报",
            ReportPeriod.YEARLY: "年报",
        }[self]
    
    def get_date_range(self, target_date: date) -> Tuple[date, date]:
        """
        获取报告周期的日期范围
        
        Args:
            target_date: 目标日期
        
        Returns:
            (start_date, end_date) 元组
        """
        if self == ReportPeriod.DAILY:
            return target_date, target_date
        
        elif self == ReportPeriod.WEEKLY:
            start = target_date - timedelta(days=target_date.weekday())
            end = start + timedelta(days=6)
            return start, end
        
        elif self == ReportPeriod.MONTHLY:
            start = target_date.replace(day=1)
            next_month = start.replace(month=start.month % 12 + 1, day=1) if start.month < 12 else start.replace(year=start.year + 1, month=1, day=1)
            end = next_month - timedelta(days=1)
            return start, end
        
        elif self == ReportPeriod.YEARLY:
            start = target_date.replace(month=1, day=1)
            end = target_date.replace(month=12, day=31)
            return start, end
        
        else:
            raise ValueError(f"未知的报告周期: {self}")
    
    def get_filename_prefix(self, target_date: date) -> str:
        """
        获取报告文件名前缀
        
        Args:
            target_date: 目标日期
        
        Returns:
            文件名前缀
        """
        if self == ReportPeriod.DAILY:
            return target_date.strftime("%Y%m%d")
        
        elif self == ReportPeriod.WEEKLY:
            start, end = self.get_date_range(target_date)
            return f"{start.strftime('%Y%m%d')}-{end.strftime('%m%d')}"
        
        elif self == ReportPeriod.MONTHLY:
            return target_date.strftime("%Y%m")
        
        elif self == ReportPeriod.YEARLY:
            return str(target_date.year)
        
        else:
            raise ValueError(f"未知的报告周期: {self}")
    
    @classmethod
    def from_string(cls, value: str) -> "ReportPeriod":
        """
        从字符串创建报告周期枚举
        
        Args:
            value: 字符串值
        
        Returns:
            报告周期枚举
        """
        value_map = {
            "daily": cls.DAILY,
            "weekly": cls.WEEKLY,
            "monthly": cls.MONTHLY,
            "yearly": cls.YEARLY,
            "day": cls.DAILY,
            "week": cls.WEEKLY,
            "month": cls.MONTHLY,
            "year": cls.YEARLY,
        }
        
        if value.lower() not in value_map:
            raise ValueError(f"未知的报告周期: {value}，支持的值: {list(value_map.keys())}")
        
        return value_map[value.lower()]
