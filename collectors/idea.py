"""
IDEA 采集器

采集 JetBrains IDE（IDEA、WebStorm、PyCharm 等）的会话数据
"""

from datetime import date, datetime
from pathlib import Path
from typing import List
import logging

from .base import BaseCollector, SessionData, register_collector
from config import get_config


logger = logging.getLogger(__name__)


@register_collector
class IDEACollector(BaseCollector):
    """IDEA 采集器"""
    
    name = "idea"
    version = "1.0.0"
    priority = 40
    
    def get_data_path(self) -> Path:
        """获取数据源路径"""
        return get_config().idea_config_path
    
    def collect(self, target_date: date) -> List[SessionData]:
        """
        采集指定日期的 IDEA 会话数据
        
        Args:
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        logger.info(f"[{self.name}] 开始采集 {target_date} 的会话数据")
        
        # TODO: 实现真实的采集逻辑
        # 当前为空实现，仅打印日志，证明跑通流程
        
        data_path = self.get_data_path()
        logger.info(f"[{self.name}] 数据路径: {data_path}")
        
        # 验证数据路径
        if not data_path.exists():
            logger.warning(f"[{self.name}] 数据路径不存在，跳过采集")
            return []
        
        # 模拟采集结果
        logger.info(f"[{self.name}] 采集完成，获取到 0 个会话")
        
        return []
