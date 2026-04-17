# AI Journey 🤖📚

> 在 AI 编程时代，成为"AI 对话的 Git"，让每一次 AI 协作都被永久记录、可追溯、可复用、个人知识沉淀

## ✨ 核心价值

- **永久记录** - 自动采集 Claude Code、CodeBuddy、Git 提交记录
- **可追溯** - 完整的会话历史，支持全文搜索
- **可复用** - 结构化存储，便于知识沉淀和复用
- **智能报告** - 自动生成日报/周报，强调成果和影响
- **跨平台** - 完美支持 macOS、Windows、Linux

## 📁 项目结构

```
AIJourney/
├── config.py                # 配置模块（跨平台路径管理）
├── .claude-plugin/          # Claude 插件配置
│   └── plugin.json          # 插件元数据和命令定义
├── commands/                # 斜杠命令处理
│   ├── daily-report.py      # /daily-report 生成日报
│   ├── weekly-report.py     # /weekly-report 生成周报
│   └── search.py            # /search 搜索历史对话
├── collectors/              # 数据采集器
│   ├── base.py              # 基础采集器类
│   ├── claude_code.py       # Claude Code 采集器
│   ├── codebuddy.py         # CodeBuddy 采集器
│   └── git_commits.py       # Git 提交采集器
├── data/                    # SQLite 数据库
└── reports/                 # 生成的报告文件
    ├── daily/               # 日报目录
    └── weekly/              # 周报目录
```

## 🚀 快速开始

### 安装依赖

```bash
pip install python-dateutil
```

### 使用命令

```bash
# 生成今日日报
python3 commands/daily-report.py

# 生成本周周报
python3 commands/weekly-report.py

# 搜索历史对话
python3 commands/search.py AIJourney
```

### Claude 插件模式（推荐）

在 Claude Code 中直接使用斜杠命令：

```
/daily-report          # 生成今日日报
/weekly-report         # 生成本周周报  
/search AIJourney      # 搜索关键词
```

## 🎯 支持的数据源

| 数据源 | 说明 | 跨平台支持 |
|--------|------|------------|
| **Claude Code** | 自动采集对话历史 | ✅ macOS / Windows / Linux |
| **CodeBuddy** | 自动采集代码助手会话 | ✅ macOS / Windows / Linux |
| **Git** | 自动扫描项目提交记录 | ✅ macOS / Windows / Linux |

## ⚙️ 配置说明

### 环境变量配置

通过环境变量自定义路径配置：

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `AIJOURNEY_CLAUDE_PATH` | Claude Code 数据路径 | 自动识别平台 |
| `AIJOURNEY_CODEBUDDY_PATH` | CodeBuddy 数据路径 | 自动识别平台 |
| `AIJOURNEY_GIT_PATHS` | Git 仓库搜索路径（逗号分隔） | 常用目录列表 |
| `AIJOURNEY_REPORT_DIR` | 报告输出目录 | `./reports` |

### 路径自动识别规则

#### Claude Code 数据路径

| 操作系统 | 默认路径 |
|----------|----------|
| **macOS** | `~/.claude` 或 `~/Library/Application Support/Claude` |
| **Windows** | `%APPDATA%\Claude` 或 `%APPDATA%\Anthropic\Claude` |
| **Linux** | `~/.claude` 或 `~/.config/claude` |

#### CodeBuddy 数据路径

| 操作系统 | 默认路径 |
|----------|----------|
| **macOS** | `~/Library/Application Support/CodeBuddy/storage` |
| **Windows** | `%APPDATA%\CodeBuddy\storage` |
| **Linux** | `~/.config/CodeBuddy/storage` 或 `~/.CodeBuddy/storage` |

#### Git 仓库搜索路径

| 操作系统 | 默认搜索目录 |
|----------|--------------|
| **macOS/Linux** | `~/work`, `~/projects`, `~/code`, `~/repos`, `~/Documents`, `~/Desktop`, `~` |
| **Windows** | 上述目录 + `~/OneDrive/Documents`, `~/OneDrive/Desktop` |

### 手动指定目录示例

```bash
# Linux/macOS
export AIJOURNEY_CLAUDE_PATH="/custom/path/to/claude"
export AIJOURNEY_GIT_PATHS="/work/projects,/home/user/repos"
export AIJOURNEY_REPORT_DIR="/home/user/reports"

# Windows (PowerShell)
$env:AIJOURNEY_CLAUDE_PATH="C:\custom\claude"
$env:AIJOURNEY_REPORT_DIR="D:\reports"
```

### 报告目录配置

报告默认输出到项目根目录下的 `reports` 文件夹：

```
reports/
├── daily/              # 日报目录
│   └── daily_report_20260417.md
└── weekly/             # 周报目录
    └── weekly_report_20260415.md
```

通过 `AIJOURNEY_REPORT_DIR` 环境变量自定义报告输出位置。

## 📊 报告结构

### 日报
```markdown
# 📅 日报 - 2026年04月17日

## 📊 工作概览
| 项目 | 详情 |

## 🎯 今日成果
- 做成了什么？
- 有什么影响？

## 📝 会话详情
```

### 周报
```markdown
# 📅 周报 - 2026年04月15日 ~ 2026年04月21日

## 📊 本周概览

## 🎯 核心成果（重点）

## 📈 效率分析

## 📋 下周计划
```

## 🔍 搜索功能

```bash
# 搜索包含关键词的会话
python3 commands/search.py "AIJourney"

# 在 Claude 中
/search AIJourney
```

## 🛡️ 隐私说明

- 所有数据**仅存储在本地**
- 数据源直接读取本地工具存储，不经过第三方
- 敏感信息需要手动处理

## 📄 许可证

MIT License