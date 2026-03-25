# SumAll 📝
> 程序员每日工作会话自动归档框架

[![Python 3.8+](https://img.shields.io/badge/python-3.8%2B-blue.svg)](https://www.python.org/downloads/)
[![Tests](https://github.com/yourusername/SumAll/workflows/Tests/badge.svg)](https://github.com/yourusername/SumAll/actions)
[![Coverage](https://img.shields.io/badge/coverage-69%25-green.svg)](https://github.com/yourusername/SumAll)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

自动采集多个 AI 编程工具的会话数据，生成结构化的工作日报。再也不用手动写日报了！

---

## 🧩 开发方式

本项目采用 **双层 Spec 驱动的 AI Coding 开发方式**：
> 由 AI 执行行级编码，人类与 AI 协作进行 Spec 维护。

- 👤 **Me2AI 层** - 用户主导，传达"做什么"和"为什么"
- 🤖 **AI2AI 层** - AI 主导，记录"怎么做"和"做到哪"
- 📐 **分层协作** - 规范 AI 辅助开发流程，保证文档与代码同步

详细规范见 [rules/ProjectRule.mdc](rules/ProjectRule.mdc)

---

## ✨ 特性

- 🔌 **插件化架构** - 轻松添加新采集器，支持扩展
- 🤖 **AI 工具支持** - 原生支持 Claude Code、CodeBuddy 等 AI 编程助手
- 📊 **双格式输出** - JSON（机器可读）+ Markdown（人类可读）
- 🎯 **智能摘要** - 自动总结会话内容，提取目标和成果
- 🛡️ **容错隔离** - 单个采集器失败不影响整体运行
- 🏝️ **零配置运行** - 安装依赖即可使用，默认路径自动识别

---

## 🚀 快速开始

### 1. 安装依赖

```bash
git clone https://github.com/yourusername/SumAll.git
cd SumAll
pip install -r requirements.txt
```

### 2. 运行

```bash
# 采集今天的数据，生成日报
python main.py

# 指定日期（格式 YYYY-MM-DD）
python main.py --date 2026-03-25

# 指定输出目录
python main.py --output ./my_reports

# 只启用指定采集器
python main.py --collectors claude_code codebuddy

# 调试模式（输出详细日志）
python main.py --log-level DEBUG
```

### 3. 配置（可选）

复制示例配置文件并修改：
```bash
cp settings.json.example settings.json
# 编辑 settings.json 自定义路径等配置
```

---

## 📋 支持的采集器

| 采集器 | 数据源路径 | 实现状态 | 平台 |
|--------|-----------|----------|------|
| **Claude Code** | `~/.claude/` | ✅ 完整实现 | macOS |
| **CodeBuddy** | `~/Library/Application Support/CodeBuddyExtension/Data/` | ✅ 完整实现 | macOS |
| **VSCode** | `~/Library/Application Support/Code/User/History/` | 🏗️ 框架完成 | macOS |
| **IDEA** | `~/Library/Application Support/JetBrains/` | 🏗️ 框架完成 | macOS |

> 🔍 **计划中**: Windows/Linux 路径适配，System 活动采集

---

## 📁 输出示例

输出目录结构：
```
output/
├── daily_report_20260325.json    # 结构化数据
└── daily_report_20260325.md      # 可读日报
```

### Markdown 日报包含：
- 📊 工作概览（时长、会话数、Token 统计）
- 🎯 今日成果（每个会话的目标和成果摘要）
- 📈 效率分析（工具使用分布）
- 🔧 技术成长（今日学习的技术点）
- 📝 明日计划（预留手动填写区域）

---

## 🗂️ 项目结构

```
SumAll/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── requirements.txt     # Python 依赖
├── collectors/          # 采集器模块
│   ├── __init__.py      # 采集器注册
│   ├── base.py          # 采集器基类 + 数据结构
│   ├── claude_code.py   # Claude Code 采集器
│   ├── codebuddy.py     # CodeBuddy 采集器
│   ├── vscode.py        # VSCode 采集器
│   └── idea.py          # IDEA 采集器
├── report/              # 报告生成模块
│   ├── __init__.py
│   ├── generator.py     # 报告生成器
│   └── summarizer.py   # 会话摘要生成
├── tests/               # 单元测试
│   ├── test_*.py        # 各模块测试
├── spec/                # 需求文档（AI 协作开发）
│   ├── Me2AI/           # 👤 用户维护层（需求、约束、规划）
│   └── AI2AI/           # 🤖 AI 维护层（设计、实现记录）
├── rules/               # 项目开发规范
├── output/              # 输出目录（报告文件）
└── logs/                # 日志目录
```

---

## 🧪 开发

### 运行测试

```bash
# 运行所有测试
pytest tests/ -v

# 查看覆盖率
pytest tests/ -v --cov=. --cov-report=html
# 打开 htmlcov/index.html 查看覆盖率
```

当前测试状态: **31/31 测试通过**，整体覆盖率 **69%**

### 添加自定义采集器

1. 继承 `BaseCollector` 基类
2. 实现 `collect()` 方法返回 `List[SessionData]`
3. 使用 `@register_collector` 装饰器注册
4. 重新运行即可自动加载

详细开发文档见 [spec/AI2AI/概要设计.md](spec/AI2AI/概要设计.md)

---

## 🛡️ 隐私说明

- 所有数据**只保存在本地**，不会上传到任何服务器
- 数据源直接读取本地工具存储，不经过第三方
- 敏感信息（如果有）需要手动处理，当前版本不做自动脱敏

---

## 📄 许可证

[MIT](LICENSE) © 2026

---

## 🙏 致谢

感谢 Claude Code 和 CodeBuddy 提供出色的 AI 编程体验，这个工具就是为了记录这些精彩的协作过程而生。
