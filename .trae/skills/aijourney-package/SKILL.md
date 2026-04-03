---
name: "aijourney-package"
description: "AIJourney Skill Package - A standalone toolkit for collecting AI programming tool sessions and generating work reports. Invoke when user needs to track AI-assisted programming activities or generate daily/weekly/monthly reports."
---

# AIJourney Skill Package

一个独立的Skill工具包，用于自动采集AI编程工具会话数据并生成工作日报。

## 安装

```bash
# 复制skill包到项目
mkdir -p .trae/skills/aijourney-package

# 安装依赖
pip install -r requirements.txt
```

## 快速开始

### 1. 基础使用

```python
from aijourney import AIJourneySkill

# 创建Skill实例
skill = AIJourneySkill(output_dir="./output")

# 加载内置采集器
skill.load_builtin_collectors()

# 一键运行：采集 + 生成报告
result = skill.run(period="daily")
print(result)
```

### 2. 分步使用

```python
from aijourney import AIJourneySkill
from datetime import date

skill = AIJourneySkill(output_dir="./output")
skill.load_builtin_collectors()

# 仅采集数据
sessions = skill.collect(target_date=date.today())

# 仅生成报告
report = skill.generate_report(
    sessions=sessions,
    period="weekly",
    formats=["json", "markdown"]
)
```

### 3. 自定义采集器

```python
from aijourney import BaseCollector, SessionData, register_collector
from datetime import date
from typing import List

@register_collector
class MyCollector(BaseCollector):
    name = "my_collector"
    description = "My custom collector"
    
    def validate(self) -> bool:
        # 检查数据源是否存在
        return True
    
    def collect(self, target_date: date) -> List[SessionData]:
        # 实现采集逻辑
        sessions = []
        # ... 采集代码 ...
        return sessions

# 使用自定义采集器
skill = AIJourneySkill()
skill.register_collector(MyCollector)
result = skill.run()
```

## API 参考

### AIJourneySkill

主类，提供完整的采集和报告功能。

#### 构造函数

```python
AIJourneySkill(
    output_dir: str = "./output",    # 输出目录
    log_level: str = "INFO",          # 日志级别
    config: Optional[Dict] = None,    # 配置字典
)
```

#### 方法

- `load_builtin_collectors()` - 加载所有内置采集器
- `register_collector(collector_class)` - 注册自定义采集器
- `collect(target_date, collector_names)` - 采集会话数据
- `generate_report(sessions, period, formats)` - 生成报告
- `run(target_date, period, collector_names, formats)` - 一键运行

### BaseCollector

采集器基类，继承此类实现自定义采集器。

```python
class MyCollector(BaseCollector):
    name = "my_collector"           # 采集器名称（必需）
    description = "描述"             # 采集器描述
    
    def validate(self) -> bool:
        """验证采集器是否可用"""
        pass
    
    def collect(self, target_date: date) -> List[SessionData]:
        """采集数据"""
        pass
```

### SessionData

会话数据模型。

```python
SessionData(
    session_id: str,                 # 会话ID
    tool_name: str,                  # 工具名称
    start_time: datetime,            # 开始时间
    end_time: Optional[datetime],    # 结束时间
    messages: List[Dict],            # 消息列表
    metadata: Dict,                  # 元数据
)
```

## 配置

```python
config = {
    "output_dir": "./output",
    "log_level": "INFO",
    "collectors": {
        "claude_code": {
            "path": "~/.claude"
        },
        "codebuddy": {
            "path": "~/Library/Application Support/CodeBuddyExtension/Data"
        }
    }
}

skill = AIJourneySkill(config=config)
```

## 输出格式

支持两种报告格式：

- **JSON** - 结构化数据，便于程序处理
- **Markdown** - 人类可读，包含工作概览和会话详情

## 示例

见 `examples/` 目录：

- `basic_usage.py` - 基础使用示例
- `custom_collector.py` - 自定义采集器示例
- `cli_example.py` - 命令行使用示例

## 开发

### 添加新的内置采集器

1. 在 `aijourney/collectors/` 目录创建采集器文件
2. 继承 `BaseCollector` 并实现 `collect()` 方法
3. 使用 `@register_collector` 装饰器注册

### 测试

```bash
python -m pytest tests/
```

## 许可证

MIT License
