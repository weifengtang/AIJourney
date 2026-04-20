"""
缓存工具模块

提供统一的 JSON 文件缓存功能，支持：
1. 缓存过期机制（TTL）
2. 缓存版本管理
3. 自动创建目录
"""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class CacheManager:
    """缓存管理器"""
    
    def __init__(self, cache_dir: str = "data/cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get_cache_path(self, name: str) -> Path:
        """获取缓存文件路径"""
        return self.cache_dir / f"{name}.json"
    
    def load_cache(self, name: str, default: Any = None) -> Any:
        """
        加载缓存数据
        
        Args:
            name: 缓存名称
            default: 默认值
        
        Returns:
            缓存数据，如果不存在或过期返回默认值
        """
        cache_path = self.get_cache_path(name)
        
        if not cache_path.exists():
            logger.debug(f"缓存文件不存在: {cache_path}")
            return default
        
        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查缓存版本和过期时间
            if self._is_cache_valid(data):
                return data
            
            logger.debug(f"缓存已过期: {cache_path}")
            return default
            
        except Exception as e:
            logger.error(f"加载缓存失败 {cache_path}: {e}")
            return default
    
    def save_cache(self, name: str, data: Any, ttl_days: int = 7) -> None:
        """
        保存缓存数据
        
        Args:
            name: 缓存名称
            data: 缓存数据
            ttl_days: 过期天数，默认7天
        """
        cache_path = self.get_cache_path(name)
        
        # 添加缓存元数据
        cache_data = {
            "cache_version": "1.0",
            "last_updated": datetime.now().isoformat(),
            "ttl_days": ttl_days,
            "data": data
        }
        
        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
            logger.debug(f"缓存已保存: {cache_path}")
        except Exception as e:
            logger.error(f"保存缓存失败 {cache_path}: {e}")
    
    def _is_cache_valid(self, cache_data: Dict) -> bool:
        """
        检查缓存是否有效
        
        Args:
            cache_data: 缓存数据
        
        Returns:
            是否有效
        """
        # 检查版本
        if cache_data.get("cache_version") != "1.0":
            return False
        
        # 检查过期时间
        last_updated = cache_data.get("last_updated")
        ttl_days = cache_data.get("ttl_days", 7)
        
        if not last_updated:
            return False
        
        try:
            last_time = datetime.fromisoformat(last_updated)
            expire_time = last_time + timedelta(days=ttl_days)
            return datetime.now() <= expire_time
        except Exception as e:
            logger.error(f"检查缓存过期时间失败: {e}")
            return False
    
    def clear_cache(self, name: str) -> bool:
        """
        清除指定缓存
        
        Args:
            name: 缓存名称
        
        Returns:
            是否成功清除
        """
        cache_path = self.get_cache_path(name)
        
        if cache_path.exists():
            try:
                cache_path.unlink()
                logger.debug(f"缓存已清除: {cache_path}")
                return True
            except Exception as e:
                logger.error(f"清除缓存失败 {cache_path}: {e}")
        
        return False
    
    def clear_all(self) -> None:
        """清除所有缓存"""
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                logger.debug(f"已清除缓存: {cache_file}")
            except Exception as e:
                logger.error(f"清除缓存失败 {cache_file}: {e}")


# 创建全局缓存管理器实例
cache_manager = CacheManager()