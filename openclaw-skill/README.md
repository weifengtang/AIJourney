# AI Journey - OpenClaw Skill 🤖📊

> **Claude Code 原生 Skill** - 自动采集 AI 对话历史，生成智能日报/周报

## ✨ 核心功能

- 🤖 **自动采集** - 智能捕获 Claude Code、CodeBuddy、Git 提交记录
- 🧠 **AI 增强** - 使用 Claude Code 内置 LLM 生成高质量智能报告
- 📱 **跨平台** - 完美支持 macOS、Windows、Linux
- 🔒 **隐私保护** - 所有数据本地处理，不上传云端

## 📁 目录结构

```
openclaw-skill/
├── SKILL.md              # Skill 元数据（必需）
├── scripts/              # 脚本目录
│   ├── collectors/       # 数据采集器
│   ├── llm/              # LLM 模块
│   ├── daily-report.py   # 日报命令
│   ├── weekly-report.py  # 周报命令
│   ├── range-report.py   # 区间报告命令
│   └── search.py         # 搜索命令
├── assets/               # 资源文件
│   └── config.json       # 配置文件模板
└── README.md             # 说明文档
```

## 🚀 快速开始

### 在 Claude Code 中使用（推荐）

```
/daily-report          # 📅 生成今日日报（AI 增强版）
/weekly-report         # 📊 生成本周周报（AI 增强版）
/range-report --week   # 📈 生成日期区间报告
/search AIJourney      # 🔍 搜索历史对话
```

### 命令行使用

```bash
# 生成今日日报（默认 AI 增强）
python3 scripts/daily-report.py

# 生成本周周报
python3 scripts/weekly-report.py

# 生成日期区间报告
python3 scripts/range-report.py --days 7    # 最近7天
python3 scripts/range-report.py --week      # 本周
python3 scripts/range-report.py --month     # 本月
python3 scripts/range-report.py --start 2026-04-01 --end 2026-04-15
```

## ⚙️ 配置

### 配置文件 (`assets/config.json`)

```json
{
  "claude_code_path": "~/.claude",
  "codebuddy_storage_path": "~/Library/Application Support/CodeBuddy/storage",
  "git_search_paths": ["~/work", "~/projects", "~/code"],
  "report_dir": "./reports",
  "llm": {
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.3,
    "max_tokens": 4000
  }
}
```

### 环境变量

| 环境变量 | 说明 |
|----------|------|
| `AIJOURNEY_CLAUDE_PATH` | Claude Code 数据路径 |
| `AIJOURNEY_CODEBUDDY_PATH` | CodeBuddy 数据路径 |
| `AIJOURNEY_GIT_PATHS` | Git 仓库搜索路径 |
| `AIJOURNEY_REPORT_DIR` | 报告输出目录 |

## 📦 安装

### 通过 OpenClaw CLI

```bash
# 安装
skillhub install ai_journey

# 卸载
skillhub uninstall ai_journey
```

### 本地开发安装

```bash
# 本地安装测试
cp -r ./openclaw-skill ~/.openclaw/workspace/skills/ai_journey
```

### 打包发布

```bash
# 打包 Skill（生成可发布的 zip 包）
zip -r aijourney-openclaw-skill.zip openclaw-skill/

# 发布到 ClawHub
skillhub publish ./openclaw-skill
```

## 🛡️ 隐私说明

- ✅ 所有数据仅存储在本地
- ✅ 使用 Claude Code 内置 LLM，数据不上传云端

## 📄 许可证

MIT License
