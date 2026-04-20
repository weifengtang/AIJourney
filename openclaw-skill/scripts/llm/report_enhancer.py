"""
LLM 报告增强模块

使用 AI 对原始会话数据进行总结、提炼关键信息、生成更自然的描述
支持多种 LLM 后端（Claude API、OpenAI API、本地模型）
"""

import os
import json
from typing import List, Dict, Any, Optional
from datetime import date, datetime


class LLMConfig:
    """LLM 配置类
    
    支持从 AIJourneyConfig 或环境变量读取配置
    """
    
    def __init__(self, config_instance=None):
        """
        初始化 LLM 配置
        
        Args:
            config_instance: AIJourneyConfig 实例，如果提供则从该实例读取配置
        """
        if config_instance is not None:
            # 从 AIJourneyConfig 读取配置（支持配置文件 + 环境变量）
            self.provider = config_instance.llm_provider
            self.api_key = config_instance.llm_api_key
            self.api_base = config_instance.llm_api_base
            self.model = config_instance.llm_model
            self.temperature = config_instance.llm_temperature
            self.max_tokens = config_instance.llm_max_tokens
        else:
            # 从环境变量读取配置（向后兼容）
            self.provider = os.environ.get('AIJOURNEY_LLM_PROVIDER', 'claude')
            self.api_key = os.environ.get('AIJOURNEY_LLM_API_KEY', '')
            self.api_base = os.environ.get('AIJOURNEY_LLM_API_BASE', '')
            self.model = os.environ.get('AIJOURNEY_LLM_MODEL', 'claude-3-sonnet-20240229')
            self.temperature = float(os.environ.get('AIJOURNEY_LLM_TEMPERATURE', '0.3'))
            self.max_tokens = int(os.environ.get('AIJOURNEY_LLM_MAX_TOKENS', '4000'))
    
    def is_enabled(self) -> bool:
        """是否启用 LLM 增强"""
        # 以下情况启用 LLM：
        # 1. 配置了 API Key（使用外部 API）
        # 2. 使用 mock 模式（演示用）
        # 3. 使用 Claude Code 内置 LLM
        return bool(self.api_key) or \
               self.provider == 'mock' or \
               self.provider == 'claude_code_internal'


class ReportEnhancer:
    """报告增强器 - 使用 LLM 处理报告内容"""
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self.client = None
        self._init_client()
    
    def _init_client(self):
        """初始化 LLM 客户端"""
        provider = self.config.provider.lower()
        
        if provider == 'claude':
            self._init_claude_client()
        elif provider == 'openai':
            self._init_openai_client()
        elif provider == 'mock':
            self.client = MockLLMClient()
        elif provider == 'claude_code_internal':
            # 在 Claude Code 环境中使用内置 LLM
            self.client = ClaudeCodeInternalClient()
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
    
    def _init_claude_client(self):
        """初始化 Claude 客户端"""
        try:
            import anthropic
            self.client = anthropic.Anthropic(
                api_key=self.config.api_key,
            )
        except ImportError:
            raise ImportError("请安装 anthropic 库: pip install anthropic")
        except Exception as e:
            raise RuntimeError(f"初始化 Claude 客户端失败: {e}")
    
    def _init_openai_client(self):
        """初始化 OpenAI 客户端"""
        try:
            from openai import OpenAI
            client_kwargs = {}
            if self.config.api_base:
                client_kwargs['base_url'] = self.config.api_base
            
            self.client = OpenAI(
                api_key=self.config.api_key,
                **client_kwargs
            )
        except ImportError:
            raise ImportError("请安装 openai 库: pip install openai")
        except Exception as e:
            raise RuntimeError(f"初始化 OpenAI 客户端失败: {e}")
    
    def enhance_daily_report(self, sessions: List[Dict], target_date: date) -> str:
        """
        使用 LLM 增强日报内容
        
        Args:
            sessions: 会话数据列表
            target_date: 目标日期
        
        Returns:
            增强后的日报内容
        """
        if not self.config.is_enabled():
            return self._generate_fallback_report(sessions, target_date)
        
        prompt = self._build_daily_report_prompt(sessions, target_date)
        response = self._call_llm(prompt)
        
        return self._parse_report_response(response)
    
    def enhance_weekly_report(self, sessions: List[Dict], start_date: date, end_date: date) -> str:
        """
        使用 LLM 增强周报内容
        
        Args:
            sessions: 会话数据列表
            start_date: 开始日期
            end_date: 结束日期
        
        Returns:
            增强后的周报内容
        """
        if not self.config.is_enabled():
            return self._generate_fallback_weekly_report(sessions, start_date, end_date)
        
        prompt = self._build_weekly_report_prompt(sessions, start_date, end_date)
        response = self._call_llm(prompt)
        
        return self._parse_report_response(response)
    
    def _build_daily_report_prompt(self, sessions: List[Dict], target_date: date) -> str:
        """构建日报生成提示词"""
        sessions_json = json.dumps(sessions, default=str, ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一位专业的技术工作日报助手。请根据以下原始会话数据，帮我生成一份专业、简洁、有价值的工作日报。

## 要求

1. **分析内容**: 仔细阅读所有会话记录，理解当天完成的工作
2. **提炼成果**: 提取关键成果和技术亮点
3. **总结价值**: 说明工作带来的业务价值或技术价值
4. **保持专业**: 使用专业但易懂的语言
5. **格式输出**: 输出 Markdown 格式的日报

## 输出格式

```markdown
# 📅 日报 - {target_date.strftime('%Y年%m月%d日')}

## 📊 工作概览

| 项目 | 详情 |
|------|------|
| **日期** | {target_date.strftime('%Y-%m-%d')} |
| **会话数** | {{会话数量}} |
| **主要工作** | {{简要描述}} |

## 🎯 今日成果

1. **成果标题** - 详细描述这项工作的内容、技术实现和价值
2. **成果标题** - 详细描述这项工作的内容、技术实现和价值

## 💡 技术亮点

- 技术点1: 描述使用的关键技术或解决的技术难题
- 技术点2: 描述使用的关键技术或解决的技术难题

## 📝 会话摘要

（简要总结重要的对话内容）

---
*AI Journey - 让每一次 AI 协作都被永久记录*
```

## 原始数据

{sessions_json}
"""
        return prompt.strip()
    
    def _build_weekly_report_prompt(self, sessions: List[Dict], start_date: date, end_date: date) -> str:
        """构建周报生成提示词"""
        sessions_json = json.dumps(sessions, default=str, ensure_ascii=False, indent=2)
        
        prompt = f"""
你是一位专业的技术工作周报助手。请根据以下原始会话数据，帮我生成一份专业、全面、有价值的工作周报。

## 要求

1. **综合分析**: 分析一周的工作内容，识别主要项目和任务
2. **提炼核心成果**: 提取最重要的3-5项核心成果
3. **量化价值**: 尽可能用量化指标说明工作价值
4. **识别模式**: 发现工作模式、效率趋势或需要改进的地方
5. **保持专业**: 使用专业但易懂的语言
6. **格式输出**: 输出 Markdown 格式的周报

## 输出格式

```markdown
# 📅 周报 - {start_date.strftime('%Y年%m月%d日')} ~ {end_date.strftime('%Y年%m月%d日')}

## 📊 本周概览

| 项目 | 详情 |
|------|------|
| **周期** | {start_date.strftime('%m-%d')} ~ {end_date.strftime('%m-%d')} |
| **总会话数** | {{会话数量}} |
| **工作天数** | 7 天 |

## 🎯 核心成果

### 1. 主要成果标题
**描述**: 详细描述这项工作的内容和技术实现
**价值**: 说明这项工作带来的业务价值或技术价值
**量化指标**: 相关数据指标（如代码量、功能点、性能提升等）

### 2. 主要成果标题
**描述**: 详细描述这项工作的内容和技术实现
**价值**: 说明这项工作带来的业务价值或技术价值
**量化指标**: 相关数据指标

## 📈 效率分析

- **工具使用分布**: 各工具/平台的使用频率分析
- **活跃度趋势**: 工作时段分布和活跃度变化
- **改进建议**: 基于数据分析的效率提升建议

## 💡 技术亮点

- 技术点1: 描述使用的关键技术或解决的技术难题
- 技术点2: 描述使用的关键技术或解决的技术难题

## 📋 下周计划

1. 计划事项1 - 简要描述
2. 计划事项2 - 简要描述

---
*AI Journey - 让每一次 AI 协作都被永久记录*
```

## 原始数据

{sessions_json}
"""
        return prompt.strip()
    
    def _call_llm(self, prompt: str) -> str:
        """调用 LLM 生成响应"""
        provider = self.config.provider.lower()
        
        if provider == 'claude':
            return self._call_claude(prompt)
        elif provider == 'openai':
            return self._call_openai(prompt)
        elif provider == 'mock':
            return self.client.generate_response(prompt)
        elif provider == 'claude_code_internal':
            return self.client.generate_response(prompt)
        else:
            raise ValueError(f"不支持的 LLM 提供商: {provider}")
    
    def _call_claude(self, prompt: str) -> str:
        """调用 Claude API"""
        try:
            response = self.client.messages.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.content[0].text
        except Exception as e:
            print(f"调用 Claude API 失败: {e}")
            return ""
    
    def _call_openai(self, prompt: str) -> str:
        """调用 OpenAI API"""
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"调用 OpenAI API 失败: {e}")
            return ""
    
    def _parse_report_response(self, response: str) -> str:
        """解析 LLM 响应，提取 Markdown 内容"""
        if not response:
            return ""
        
        # 尝试提取代码块内容
        if '```markdown' in response:
            start = response.find('```markdown') + len('```markdown')
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        if '```' in response:
            start = response.find('```') + len('```')
            end = response.find('```', start)
            if end > start:
                return response[start:end].strip()
        
        return response.strip()
    
    def _generate_fallback_report(self, sessions: List[Dict], target_date: date) -> str:
        """生成降级报告（不使用 LLM）"""
        report = f"""# 📅 日报 - {target_date.strftime('%Y年%m月%d日')}

## 📊 工作概览

| 项目 | 详情 |
|------|------|
| **日期** | {target_date.strftime('%Y-%m-%d')} |
| **会话数** | {len(sessions)} |
| **主要工作** | 未启用 LLM 增强 |

## 🎯 今日成果

（LLM 增强未启用，请配置环境变量启用 AI 总结功能）

## 💡 技术亮点

（LLM 增强未启用）

## 📝 会话摘要

共有 {len(sessions)} 条会话记录

---
*AI Journey - 让每一次 AI 协作都被永久记录*
"""
        return report
    
    def _generate_fallback_weekly_report(self, sessions: List[Dict], start_date: date, end_date: date) -> str:
        """生成降级周报（不使用 LLM）"""
        report = f"""# 📅 周报 - {start_date.strftime('%Y年%m月%d日')} ~ {end_date.strftime('%Y年%m月%d日')}

## 📊 本周概览

| 项目 | 详情 |
|------|------|
| **周期** | {start_date.strftime('%m-%d')} ~ {end_date.strftime('%m-%d')} |
| **总会话数** | {len(sessions)} |
| **工作天数** | 7 天 |

## 🎯 核心成果

（LLM 增强未启用，请配置环境变量启用 AI 总结功能）

## 📈 效率分析

（LLM 增强未启用）

## 💡 技术亮点

（LLM 增强未启用）

## 📋 下周计划

（LLM 增强未启用）

---
*AI Journey - 让每一次 AI 协作都被永久记录*
"""
        return report


class MockLLMClient:
    """Mock LLM 客户端 - 用于测试和演示"""
    
    def generate_response(self, prompt: str) -> str:
        """生成模拟响应"""
        if '日报' in prompt:
            return """
```markdown
# 📅 日报 - 2026年04月17日

## 📊 工作概览

| 项目 | 详情 |
|------|------|
| **日期** | 2026-04-17 |
| **会话数** | 3 |
| **主要工作** | AI 对话历史记录与分析工具开发 |

## 🎯 今日成果

1. **AI Journey 配置系统优化** - 实现了跨平台路径自动识别功能，支持 Windows/macOS/Linux 三种操作系统，用户可以通过配置文件或环境变量自定义数据路径
2. **LLM 报告增强模块设计** - 设计了基于 Claude/OpenAI 的智能报告生成方案，支持自动总结和关键信息提炼

## 💡 技术亮点

- 跨平台路径处理: 使用 platform.system() 自动识别操作系统，结合环境变量实现灵活配置
- 配置优先级设计: 环境变量 > 配置文件 > 默认路径，满足不同场景需求

## 📝 会话摘要

完成了配置系统的核心功能开发和测试验证

---
*AI Journey - 让每一次 AI 协作都被永久记录*
```
"""
        elif '周报' in prompt:
            return """
```markdown
# 📅 周报 - 2026年04月15日 ~ 2026年04月21日

## 📊 本周概览

| 项目 | 详情 |
|------|------|
| **周期** | 04-15 ~ 04-21 |
| **总会话数** | 15 |
| **工作天数** | 7 天 |

## 🎯 核心成果

### 1. AI Journey 配置系统开发完成
**描述**: 实现了完整的跨平台配置系统，支持自动路径识别和手动配置
**价值**: 提升了工具的易用性和兼容性，用户无需手动配置即可在不同平台使用
**量化指标**: 支持 3 种操作系统，配置方式扩展到 3 种

### 2. 数据采集器重构
**描述**: 重构了 Claude Code、CodeBuddy、Git 三个采集器，统一接口规范
**价值**: 提高了代码可维护性，便于后续扩展新数据源
**量化指标**: 代码复用率提升 40%

## 📈 效率分析

- **工具使用分布**: Claude Code 60%、CodeBuddy 20%、Git 20%
- **活跃度趋势**: 工作日活跃度较高，周末相对较低
- **改进建议**: 可以考虑添加定时自动采集功能

## 💡 技术亮点

- 设计模式应用: 使用策略模式实现不同数据源的统一接口
- 错误处理增强: 添加了完善的异常处理和日志记录

## 📋 下周计划

1. LLM 报告增强功能开发
2. Web 界面优化
3. 性能测试和优化

---
*AI Journey - 让每一次 AI 协作都被永久记录*
```
"""
        return "这是一个模拟响应。请配置真实的 LLM API Key 以获得更好的效果。"


class ClaudeCodeInternalClient:
    """Claude Code 内置 LLM 客户端
    
    在 Claude Code 插件环境中运行时，直接调用内置的 AI 能力
    """
    
    def __init__(self):
        self._claude_api = None
        self._init_claude_api()
    
    def _init_claude_api(self):
        """初始化 Claude Code 内置 API"""
        try:
            # 尝试导入 Claude Code 内置 API
            import sys
            if hasattr(sys, '_claude_internal_api'):
                self._claude_api = sys._claude_internal_api
            elif 'claude' in sys.modules:
                self._claude_api = sys.modules['claude']
        except Exception:
            pass
    
    def generate_response(self, prompt: str) -> str:
        """通过 Claude Code 内置 LLM 生成响应"""
        # 优先尝试直接调用内置 API
        if self._claude_api is not None:
            try:
                return self._call_internal_api(prompt)
            except Exception as e:
                print(f"直接调用内置 API 失败，尝试备用方案: {e}")
        
        # 备用方案：环境变量方式
        if self._has_claude_env():
            return self._call_via_env(prompt)
        
        # 降级到 Mock 响应
        print("未检测到 Claude Code 内置 LLM，使用 Mock 模式")
        mock_client = MockLLMClient()
        return mock_client.generate_response(prompt)
    
    def _call_internal_api(self, prompt: str) -> str:
        """直接调用 Claude Code 内置 API"""
        # 尝试多种可能的 API 接口
        api_methods = [
            lambda p: self._claude_api.complete(p),
            lambda p: self._claude_api.generate(p),
            lambda p: self._claude_api.chat.completions.create(
                messages=[{"role": "user", "content": p}],
                model="claude-3-sonnet",
                max_tokens=4000
            ),
            lambda p: self._claude_api.messages.create(
                model="claude-3-sonnet",
                max_tokens=4000,
                messages=[{"role": "user", "content": p}]
            )
        ]
        
        for method in api_methods:
            try:
                result = method(prompt)
                # 处理不同的返回格式
                if hasattr(result, 'content'):
                    if isinstance(result.content, list) and len(result.content) > 0:
                        return result.content[0].text if hasattr(result.content[0], 'text') else str(result.content[0])
                    return str(result.content)
                elif hasattr(result, 'choices') and len(result.choices) > 0:
                    return result.choices[0].message.content
                return str(result)
            except Exception:
                continue
        
        raise RuntimeError("无法调用内置 API")
    
    def _call_via_env(self, prompt: str) -> str:
        """通过环境变量方式调用"""
        try:
            import subprocess
            result = subprocess.run(
                ['claude', 'completion', '--prompt', prompt, '--max-tokens', '4000'],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return ""
    
    def _has_claude_env(self) -> bool:
        """检查是否处于 Claude Code 环境"""
        import os
        return any([
            os.environ.get('CLAUDE_CODE_ENV') == 'true',
            os.environ.get('ANTHROPIC_CLAUDE_CODE') == '1',
            os.environ.get('CLAUDE_PLUGIN_ENV') == 'true',
            'claude' in os.environ.get('USER', '').lower()
        ])


def get_enhancer(config: Optional[LLMConfig] = None) -> ReportEnhancer:
    """获取报告增强器实例"""
    return ReportEnhancer(config)