"""
配置模块单元测试
"""

import tempfile
from pathlib import Path
from datetime import date
import json

from config import Config, get_config, set_config


class TestConfig:
    """Config 类单元测试"""

    def test_default_config(self):
        """测试默认配置"""
        config = Config()
        assert config.output_dir == Path("./output")
        assert config.output_format == ["json", "markdown"]
        assert "claude_code" in config.enabled_collectors
        assert config.log_level == "INFO"

    def test_post_init_conversion(self):
        """测试路径自动转换为 Path 对象"""
        config = Config(
            claude_code_path=str(Path.home() / ".claude"),
            output_dir="./test_output"
        )
        assert isinstance(config.claude_code_path, Path)
        assert isinstance(config.output_dir, Path)

    def test_to_dict_and_from_dict(self):
        """测试序列化和反序列化"""
        config = Config()
        config.target_date = date(2026, 3, 25)
        data = config.to_dict()
        assert data["target_date"] == "2026-03-25"
        
        loaded = Config.from_dict(data)
        assert loaded.target_date == date(2026, 3, 25)
        assert loaded.output_format == config.output_format

    def test_save_and_load_file(self):
        """测试保存到文件和从文件加载"""
        config = Config()
        config.target_date = date(2026, 3, 25)
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        
        try:
            config.save_to_file(temp_path)
            loaded = Config.load_from_file(temp_path)
            assert loaded.target_date == config.target_date
            assert loaded.output_dir == config.output_dir
        finally:
            temp_path.unlink()

    def test_global_config(self):
        """测试全局配置获取和设置"""
        original = get_config()
        new_config = Config()
        new_config.log_level = "DEBUG"
        set_config(new_config)
        assert get_config().log_level == "DEBUG"
        set_config(original)
