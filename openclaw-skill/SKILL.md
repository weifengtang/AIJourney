---
name: ai_journey
description: "AI 工作日报自动生成助手。自动采集 Claude Code/CodeBuddy/Git 数据，默认使用 AI 增强生成智能报告。"
homepage: https://github.com/weifengtang/AIJourney
metadata:
  {
    "openclaw": {
      "emoji": "📊",
      "os": ["darwin", "linux", "win32"],
      "requires": {
        "bins": ["python3"],
        "anyBins": ["git"]
      },
      "primaryEnv": "AIJOURNEY_LLM_API_KEY",
      "install": [
        {
          "id": "dateutil",
          "kind": "pip",
          "package": "python-dateutil",
          "label": "Install dateutil (required for timestamp parsing)"
        },
        {
          "id": "gitpython",
          "kind": "pip",
          "package": "gitpython",
          "label": "Install GitPython (required for Git commits)"
        },
        {
          "id": "anthropic",
          "kind": "pip",
          "package": "anthropic",
          "label": "Install Anthropic SDK (optional, for LLM enhancement)"
        },
        {
          "id": "openai",
          "kind": "pip",
          "package": "openai",
          "label": "Install OpenAI SDK (optional, for LLM enhancement)"
        }
      ]
    }
  }
---

# 📊 AI Journey - AI 工作日报自动生成助手

自动采集 Claude Code、CodeBuddy、Git 数据，生成智能日报、周报和区间报告。默认使用 AI 增强，让每一次 AI 协作都被永久记录。

## 架构设计

```
┌─────────────────────────────────────────────────┐
│              Claude Code (IDE)                 │
│   ┌─────────────────────────────────────────┐   │
│   │           AIJourney Skill              │   │
│   │  ┌─────────┐  ┌─────────┐  ┌─────────┐ │   │
│   │  │ 数据采集 │→│ 报告生成 │→│ LLM总结 │ │   │
│   │  └─────────┘  └─────────┘  └─────────┘ │   │
│   └─────────────────────────────────────────┘   │
│                    ↓                            │
│         直接调用 Claude Code 内置 LLM            │
│                    ↓                            │
│              生成智能报告                        │
└─────────────────────────────────────────────────┘
```

## 使用场景

✅ **USE when:**
- 用户需要生成工作日报或周报
- 用户想查看 AI 对话历史记录
- 用户想统计 Git 提交记录和工作成果
- 用户想搜索历史对话内容
- 用户想生成指定日期范围的工作报告

❌ **DON'T use when:**
- 需要实时监控（用其他监控工具）
- 需要项目管理功能（用 Jira/Trello 等）
- 需要团队协作看板（用其他协作工具）

## 功能总览

| 命令 | 说明 |
|------|------|
| `daily-report` | 生成今日日报（默认 AI 增强） |
| `weekly-report` | 生成本周周报（默认 AI 增强） |
| `range-report` | 生成日期区间报告（默认 AI 增强） |
| `search` | 搜索历史对话 |

## 快速开始

### 安装 Skill

```bash
# 方式一：通过 skillhub 安装（推荐）
skillhub install ai_journey

# 方式二：手动安装
cp -r ./aijourney ~/.openclaw/workspace/skills/ai_journey
```

### 基本用法

```bash
# 生成今日日报（默认 AI 增强）
python3 {baseDir}/scripts/daily-report.py

# 生成本周周报（默认 AI 增强）
python3 {baseDir}/scripts/weekly-report.py

# 生成日期区间报告（最近7天）
python3 {baseDir}/scripts/range-report.py --days 7

# 本周
python3 {baseDir}/scripts/range-report.py --week

# 本月
python3 {baseDir}/scripts/range-report.py --month

# 自定义日期范围
python3 {baseDir}/scripts/range-report.py --start 2026-04-01 --end 2026-04-15

# 禁用 AI 增强
python3 {baseDir}/scripts/range-report.py --week --no-ai

# 搜索历史对话
python3 {baseDir}/scripts/search.py <关键词>
```

## 详细用法

### 1. 日报 (daily-report)

自动采集当天的 Claude Code 会话、CodeBuddy 会话和 Git 提交记录，默认使用 AI 增强生成结构化 Markdown 报告。

```bash
python3 {baseDir}/scripts/daily-report.py
```

**输出示例：**

```
# 📅 daily报告 - 2026年04月20日

## 📊 工作概览
| 项目 | 详情 |
|------|------|
| **日期** | 2026-04-20 |
| **总会话数** | 4 |
| **AI 回复数** | 5 |
| **输入 Token** | 847,050 |
| **输出 Token** | 4,700 |

## 🎯 今日成果
1. **AI Journey 配置系统优化** - 实现了跨平台路径自动识别功能...

## 💡 技术亮点
- 跨平台路径处理: 使用 platform.system() 自动识别操作系统
- 配置优先级设计: 环境变量 > 配置文件 > 默认路径

## 📝 会话摘要
完成了配置系统的核心功能开发和测试验证
```

### 2. 周报 (weekly-report)

生成本周一到周日的汇总报告，默认 AI 增强。

```bash
python3 {baseDir}/scripts/weekly-report.py
```

### 3. 区间报告 (range-report)

支持任意日期范围的灵活报告生成。

```bash
# 最近 N 天
python3 {baseDir}/scripts/range-report.py --days 7

# 本周（周一到周日）
python3 {baseDir}/scripts/range-report.py --week

# 本月
python3 {baseDir}/scripts/range-report.py --month

# 自定义日期范围
python3 {baseDir}/scripts/range-report.py --start 2026-04-01 --end 2026-04-15

# 禁用 AI 增强
python3 {baseDir}/scripts/range-report.py --week --no-ai

# 指定输出文件
python3 {baseDir}/scripts/range-report.py --week --output ./my_report.md
```

### 4. 搜索 (search)

在所有历史对话中搜索关键词。

```bash
python3 {baseDir}/scripts/search.py AIJourney
python3 {baseDir}/scripts/search.py "重构配置"
```

## 配置选项

在项目根目录创建 `config.json`：

```json
{
  "claude_code_path": "",
  "codebuddy_storage_path": "",
  "git_search_paths": ["~/work", "~/projects", "~/code", "~/repos", "~/Documents", "~/Desktop"],
  "data_dir": "./data",
  "log_dir": "./logs",
  "report_dir": "./reports",
  "llm": {
    "provider": "",
    "api_key": "",
    "api_base": "",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.3,
    "max_tokens": 4000
  }
}
```

### 环境变量覆盖

```bash
export AIJOURNEY_CLAUDE_PATH="~/.claude"
export AIJOURNEY_CODEBUDDY_PATH="~/Library/Application Support/CodeBuddy/storage"
export AIJOURNEY_GIT_PATHS="~/work,~/projects"
export AIJOURNEY_DATA_DIR="./data"
export AIJOURNEY_LOG_DIR="./logs"
export AIJOURNEY_REPORT_DIR="./reports"
export AIJOURNEY_LLM_PROVIDER=claude
export AIJOURNEY_LLM_API_KEY=your-key
```

### 配置优先级

环境变量 > 配置文件 > 系统默认路径

### LLM 提供商选择优先级

1. 环境变量 `AIJOURNEY_LLM_PROVIDER`
2. 在 Claude Code 环境中自动使用内置 LLM
3. 配置文件 `config.json` 中 `llm.provider`
4. 默认使用 mock 模式（演示）

## 数据源支持

| 数据源 | 默认路径 | 支持平台 |
|--------|----------|---------|
| **Claude Code** | `~/.claude/` | macOS / Linux / Windows |
| **CodeBuddy** | `~/Library/Application Support/CodeBuddy/storage` | macOS |
| **Git 提交** | 自定义目录列表 | 全平台 |

## 数据目录结构

```
data/
└── raw/                          # 原始数据根目录
    ├── claude_code/              # Claude Code 数据源
    │   ├── 2026-04-20/          # 日期目录
    │   │   ├── session_001.md
    │   │   └── session_002.md
    ├── codebuddy/                # CodeBuddy 数据源
    └── git_commits/              # Git 提交记录
```

## 错误处理

| 错误 | 处理方式 |
|------|---------|
| 数据路径不存在 | 自动跳过该数据源，继续采集其他数据 |
| 会话文件格式异常 | 记录警告日志，跳过异常文件 |
| LLM API 调用失败 | 降级为普通报告（不含 AI 总结） |
| 配置文件解析失败 | 使用默认配置 |

## 安全注意

⚠️ 报告保存在本地 `reports/` 目录，不会上传任何外部服务器
⚠️ LLM API Key 请妥善保管，不要提交到代码仓库
⚠️ Git 提交信息可能包含敏感内容，请自行审查

## 相关文件

| 文件 | 说明 |
|------|------|
| `scripts/daily-report.py` | 日报生成脚本 |
| `scripts/weekly-report.py` | 周报生成脚本 |
| `scripts/range-report.py` | 区间报告脚本 |
| `scripts/search.py` | 搜索脚本 |
| `scripts/config.py` | 配置模块 |
| `scripts/collectors/` | 数据采集器模块 |
| `scripts/llm/` | LLM 报告增强模块 |
| `assets/config.json` | 配置文件模板 |

## 依赖安装

```bash
# 核心依赖（必需）
pip install python-dateutil gitpython

# LLM 增强依赖（可选）
pip install anthropic   # Claude API
pip install openai       # OpenAI API (兼容接口)
```

## 版本信息

- **版本**: 2.0.0
- **Python 要求**: >= 3.9
- **支持平台**: macOS / Linux / Windows
- **开源协议**: MIT
