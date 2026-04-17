"""
AI Journey 配置模块

支持跨平台路径自动识别（Windows/macOS/Linux）
支持用户自定义路径配置（配置文件 + 环境变量）

配置优先级（从高到低）：
1. 环境变量
2. 配置文件（config.json 或 .aijourney/config.json）
3. 系统默认路径
"""

import os
import json
import platform
from pathlib import Path
from typing import Optional, List, Dict


class AIJourneyConfig:
    """AI Journey 配置类"""
    
    def __init__(self):
        self._system = platform.system()
        self._config_file_data = {}
        self._load_config_file()
        self._load_env_overrides()
    
    def _find_config_file(self) -> Optional[Path]:
        """查找配置文件位置"""
        possible_paths = [
            Path(".aijourney/config.json"),
            Path("config.json"),
            Path.home() / ".aijourney/config.json",
            Path(os.environ.get("APPDATA", "")) / "aijourney/config.json",  # Windows
        ]
        
        for path in possible_paths:
            if path.exists():
                return path
        return None
    
    def _load_config_file(self):
        """加载配置文件"""
        config_file = self._find_config_file()
        if config_file:
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    self._config_file_data = json.load(f)
            except Exception as e:
                print(f"警告: 读取配置文件失败 {config_file}: {e}")
    
    def _load_env_overrides(self):
        """加载环境变量覆盖配置"""
        self._claude_code_path_override = os.environ.get('AIJOURNEY_CLAUDE_PATH')
        self._codebuddy_path_override = os.environ.get('AIJOURNEY_CODEBUDDY_PATH')
        self._git_search_paths_override = os.environ.get('AIJOURNEY_GIT_PATHS')
        self._report_dir_override = os.environ.get('AIJOURNEY_REPORT_DIR')
        # LLM 配置
        self._llm_provider_override = os.environ.get('AIJOURNEY_LLM_PROVIDER')
        self._llm_api_key_override = os.environ.get('AIJOURNEY_LLM_API_KEY')
        self._llm_api_base_override = os.environ.get('AIJOURNEY_LLM_API_BASE')
        self._llm_model_override = os.environ.get('AIJOURNEY_LLM_MODEL')
        self._llm_temperature_override = os.environ.get('AIJOURNEY_LLM_TEMPERATURE')
        self._llm_max_tokens_override = os.environ.get('AIJOURNEY_LLM_MAX_TOKENS')
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """从配置文件获取值"""
        return self._config_file_data.get(key)
    
    @property
    def system(self) -> str:
        """获取当前操作系统"""
        return self._system
    
    def is_windows(self) -> bool:
        """是否为 Windows 系统"""
        return self._system == "Windows"
    
    def is_macos(self) -> bool:
        """是否为 macOS 系统"""
        return self._system == "Darwin"
    
    def is_linux(self) -> bool:
        """是否为 Linux 系统"""
        return self._system == "Linux"
    
    @property
    def claude_code_path(self) -> Path:
        """
        获取 Claude Code 数据路径
        
        优先级：
        1. 环境变量 AIJOURNEY_CLAUDE_PATH
        2. 配置文件 claude_code_path
        3. 系统默认路径
        
        Windows: %APPDATA%/Claude 或 %APPDATA%/Anthropic/Claude
        macOS: ~/.claude 或 ~/Library/Application Support/Claude
        Linux: ~/.claude 或 ~/.config/claude
        """
        # 优先级1: 环境变量
        if self._claude_code_path_override:
            return Path(self._claude_code_path_override).expanduser().resolve()
        
        # 优先级2: 配置文件
        config_value = self._get_config_value('claude_code_path')
        if config_value:
            return Path(config_value).expanduser().resolve()
        
        # 优先级3: 系统默认路径
        default_paths = self._get_default_claude_paths()
        for path in default_paths:
            if path.exists():
                return path
        
        return default_paths[0]
    
    def _get_default_claude_paths(self) -> List[Path]:
        """获取 Claude Code 默认路径列表"""
        paths = []
        
        if self.is_windows():
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                paths = [
                    Path(appdata) / "Claude",
                    Path(appdata) / "Anthropic" / "Claude",
                ]
        elif self.is_macos():
            paths = [
                Path("~/.claude").expanduser(),
                Path("~/Library/Application Support/Claude").expanduser(),
            ]
        else:  # Linux
            paths = [
                Path("~/.claude").expanduser(),
                Path("~/.config/claude").expanduser(),
            ]
        
        return paths
    
    @property
    def codebuddy_storage_path(self) -> Path:
        """
        获取 CodeBuddy 数据路径
        
        优先级：
        1. 环境变量 AIJOURNEY_CODEBUDDY_PATH
        2. 配置文件 codebuddy_storage_path
        3. 系统默认路径
        
        Windows: %APPDATA%/CodeBuddy/storage
        macOS: ~/Library/Application Support/CodeBuddy/storage
        Linux: ~/.config/CodeBuddy/storage 或 ~/.CodeBuddy/storage
        """
        if self._codebuddy_path_override:
            return Path(self._codebuddy_path_override).expanduser().resolve()
        
        config_value = self._get_config_value('codebuddy_storage_path')
        if config_value:
            return Path(config_value).expanduser().resolve()
        
        default_paths = self._get_default_codebuddy_paths()
        for path in default_paths:
            if path.exists():
                return path
        
        return default_paths[0]
    
    def _get_default_codebuddy_paths(self) -> List[Path]:
        """获取 CodeBuddy 默认路径列表"""
        paths = []
        
        if self.is_windows():
            appdata = os.environ.get("APPDATA", "")
            if appdata:
                paths = [
                    Path(appdata) / "CodeBuddy" / "storage",
                ]
        elif self.is_macos():
            paths = [
                Path("~/Library/Application Support/CodeBuddy/storage").expanduser(),
            ]
        else:  # Linux
            paths = [
                Path("~/.config/CodeBuddy/storage").expanduser(),
                Path("~/.CodeBuddy/storage").expanduser(),
            ]
        
        return paths
    
    @property
    def git_search_paths(self) -> List[Path]:
        """
        获取 Git 仓库搜索路径列表
        
        优先级：
        1. 环境变量 AIJOURNEY_GIT_PATHS（逗号分隔）
        2. 配置文件 git_search_paths（数组）
        3. 系统默认路径列表
        
        默认搜索目录：work, projects, code, repos, Documents, Desktop, ~
        """
        if self._git_search_paths_override:
            return [
                Path(p.strip()).expanduser().resolve()
                for p in self._git_search_paths_override.split(',')
                if p.strip()
            ]
        
        config_value = self._get_config_value('git_search_paths')
        if config_value and isinstance(config_value, list):
            return [Path(p).expanduser().resolve() for p in config_value]
        
        default_dirs = [
            "~/work",
            "~/projects",
            "~/code",
            "~/repos",
            "~/Documents",
            "~/Desktop",
            "~",
        ]
        
        if self.is_windows():
            default_dirs.extend([
                "~/OneDrive/Documents",
                "~/OneDrive/Desktop",
            ])
        
        return [Path(d).expanduser() for d in default_dirs]
    
    @property
    def report_dir(self) -> Path:
        """
        获取报告输出目录
        
        优先级：
        1. 环境变量 AIJOURNEY_REPORT_DIR
        2. 配置文件 report_dir
        3. 项目根目录下的 reports 文件夹
        """
        if self._report_dir_override:
            return Path(self._report_dir_override).expanduser().resolve()
        
        config_value = self._get_config_value('report_dir')
        if config_value:
            return Path(config_value).expanduser().resolve()
        
        project_root = Path(__file__).parent
        return project_root / "reports"
    
    @property
    def daily_report_dir(self) -> Path:
        """获取日报输出目录"""
        return self.report_dir / "daily"
    
    @property
    def weekly_report_dir(self) -> Path:
        """获取周报输出目录"""
        return self.report_dir / "weekly"
    
    @property
    def data_dir(self) -> Path:
        """获取数据存储目录"""
        project_root = Path(__file__).parent
        return project_root / "data"
    
    def get_report_path(self, report_type: str, date_str: str) -> Path:
        """
        获取报告文件路径
        
        Args:
            report_type: daily 或 weekly
            date_str: 日期字符串，如 20240101
        
        Returns:
            报告文件路径
        """
        if report_type == "daily":
            dir_path = self.daily_report_dir
            filename = f"daily_report_{date_str}.md"
        elif report_type == "weekly":
            dir_path = self.weekly_report_dir
            filename = f"weekly_report_{date_str}.md"
        else:
            dir_path = self.report_dir
            filename = f"{report_type}_report_{date_str}.md"
        
        dir_path.mkdir(parents=True, exist_ok=True)
        
        return dir_path / filename
    
    def validate_paths(self) -> dict:
        """验证所有路径是否存在"""
        results = {
            "claude_code_path": {
                "path": str(self.claude_code_path),
                "exists": self.claude_code_path.exists(),
            },
            "codebuddy_storage_path": {
                "path": str(self.codebuddy_storage_path),
                "exists": self.codebuddy_storage_path.exists(),
            },
            "report_dir": {
                "path": str(self.report_dir),
                "exists": self.report_dir.exists(),
            },
        }
        
        git_paths = []
        for path in self.git_search_paths:
            git_paths.append({
                "path": str(path),
                "exists": path.exists(),
            })
        results["git_search_paths"] = git_paths
        
        return results
    
    ## ============ LLM 配置 ============
    
    @property
    def llm_provider(self) -> str:
        """
        获取 LLM 提供商
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_PROVIDER
        2. 配置文件 llm.provider
        3. 默认值: claude
        """
        if self._llm_provider_override:
            return self._llm_provider_override
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return config_value.get('provider', 'claude')
        
        return 'claude'
    
    @property
    def llm_api_key(self) -> str:
        """
        获取 LLM API Key
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_API_KEY
        2. 配置文件 llm.api_key
        """
        if self._llm_api_key_override:
            return self._llm_api_key_override
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return config_value.get('api_key', '')
        
        return ''
    
    @property
    def llm_api_base(self) -> str:
        """
        获取 LLM API 基础地址
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_API_BASE
        2. 配置文件 llm.api_base
        """
        if self._llm_api_base_override:
            return self._llm_api_base_override
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return config_value.get('api_base', '')
        
        return ''
    
    @property
    def llm_model(self) -> str:
        """
        获取 LLM 模型名称
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_MODEL
        2. 配置文件 llm.model
        3. 默认值: claude-3-sonnet-20240229
        """
        if self._llm_model_override:
            return self._llm_model_override
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return config_value.get('model', 'claude-3-sonnet-20240229')
        
        return 'claude-3-sonnet-20240229'
    
    @property
    def llm_temperature(self) -> float:
        """
        获取 LLM 温度参数
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_TEMPERATURE
        2. 配置文件 llm.temperature
        3. 默认值: 0.3
        """
        if self._llm_temperature_override:
            return float(self._llm_temperature_override)
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return float(config_value.get('temperature', 0.3))
        
        return 0.3
    
    @property
    def llm_max_tokens(self) -> int:
        """
        获取 LLM 最大 Token 数
        
        优先级：
        1. 环境变量 AIJOURNEY_LLM_MAX_TOKENS
        2. 配置文件 llm.max_tokens
        3. 默认值: 4000
        """
        if self._llm_max_tokens_override:
            return int(self._llm_max_tokens_override)
        
        config_value = self._get_config_value('llm')
        if config_value and isinstance(config_value, dict):
            return int(config_value.get('max_tokens', 4000))
        
        return 4000
    
    @property
    def llm_enabled(self) -> bool:
        """是否启用 LLM 增强（需要配置 API Key）"""
        return bool(self.llm_api_key) or self.llm_provider == 'mock'
    
    def __repr__(self):
        return f"AIJourneyConfig(system={self._system}, report_dir={self.report_dir}, llm_provider={self.llm_provider})"


# 全局配置实例
_config_instance = None


def get_config() -> AIJourneyConfig:
    """获取全局配置实例"""
    global _config_instance
    if _config_instance is None:
        _config_instance = AIJourneyConfig()
    return _config_instance


def set_config_override(key: str, value: str):
    """
    运行时设置配置覆盖
    
    Args:
        key: 配置键名
        value: 配置值
    """
    config = get_config()
    
    if key == "claude_code_path":
        config._claude_code_path_override = value
    elif key == "codebuddy_path":
        config._codebuddy_path_override = value
    elif key == "git_search_paths":
        config._git_search_paths_override = value
    elif key == "report_dir":
        config._report_dir_override = value


def create_config_file_example(output_path: str = "config.json"):
    """
    创建配置文件示例
    
    Args:
        output_path: 输出路径
    """
    example_config = {
        "claude_code_path": "~/.claude",
        "codebuddy_storage_path": "~/Library/Application Support/CodeBuddy/storage",
        "git_search_paths": [
            "~/work",
            "~/projects",
            "~/code"
        ],
        "report_dir": "./reports",
        "llm": {
            "provider": "claude",
            "api_key": "",
            "api_base": "",
            "model": "claude-3-sonnet-20240229",
            "temperature": 0.3,
            "max_tokens": 4000
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(example_config, f, indent=2, ensure_ascii=False)
    
    print(f"配置文件示例已创建: {output_path}")