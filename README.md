# AI Journey 🤖�

> **Claude Code 原生 Skill** - 自动采集 AI 对话历史，生成智能日报/周报，让每一次 AI 协作都被永久记录

## ✨ 核心价值

- **自动采集** - 智能采集 Claude Code、CodeBuddy、Git 提交记录
- **智能报告** - 使用 Claude Code 内置 LLM 生成高质量报告
- **跨平台** - 完美支持 macOS、Windows、Linux
- **隐私保护** - 所有数据本地处理，不上传云端
- **灵活配置** - 支持环境变量、配置文件、自动路径识别

## 📁 项目结构

```
AIJourney/
├── .claude-plugin/          # Claude Code 插件配置
│   └── plugin.json          # 插件元数据和命令定义
├── commands/                # 斜杠命令处理
│   ├── daily-report.py      # /daily-report - AI 增强日报（默认）
│   ├── daily-report-ai.py   # /daily-report-ai - AI 增强日报
│   ├── weekly-report.py     # /weekly-report - AI 增强周报
│   ├── range-report.py      # /range-report - 日期区间报告
│   └── search.py            # /search - 搜索历史对话
├── collectors/              # 数据采集器
│   ├── base.py              # 基础采集器类
│   ├── claude_code.py       # Claude Code 采集器
│   ├── codebuddy.py         # CodeBuddy 采集器
│   └── git_commits.py       # Git 提交采集器
├── llm/                     # LLM 报告增强模块
│   └── report_enhancer.py   # AI 报告增强器（支持 Claude Code 内置 LLM）
├── openclaw-skill/          # OpenClaw Skill 打包目录（用于发布到 OpenClaw 生态）
├── config.py                # 配置模块（跨平台路径管理）
├── config.json              # 配置文件示例
└── reports/                 # 生成的报告文件
    ├── daily/               # 日报目录
    └── weekly/              # 周报目录
```

## � 工作流程图

```
用户请求 /daily-report
        ↓
┌─────────────────────────────────────────────┐
│          1. 数据采集阶段                    │
│  ┌─────────┐  ┌─────────┐  ┌───────────┐   │
│  │Claude   │  │CodeBuddy│  │ Git 提交  │   │
│  │ Code    │  │         │  │           │   │
│  └────┬────┘  └────┬────┘  └─────┬─────┘   │
│       │            │             │          │
└───────┼────────────┼─────────────┼─────────┘
        ↓            ↓             ↓
┌─────────────────────────────────────────────┐
│          2. 数据汇总阶段                    │
│     将各数据源会话合并、去重、排序           │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│          3. AI 增强阶段                     │
│     调用 Claude Code 内置 LLM               │
│     - 总结提炼关键信息                      │
│     - 生成自然语言描述                      │
│     - 提取核心成果和价值                    │
└─────────────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────┐
│          4. 报告生成阶段                    │
│     输出结构化 Markdown 报告                │
│     保存到 reports/ 目录                    │
└─────────────────────────────────────────────┘
        ↓
     返回报告内容
```

### 🤖 完整架构图

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

数据源:
├── Claude Code (~/.claude/projects/)
├── CodeBuddy (~/Library/Application Support/CodeBuddy/storage)
└── Git (自动扫描常用目录)
```

## � 快速开始

### 在 Claude Code 中使用（推荐）

直接使用斜杠命令：

```
/daily-report          # 生成今日日报
/daily-report-ai       # 生成 AI 增强日报
/weekly-report         # 生成本周周报
/range-report --week   # 生成日期区间报告
/search AIJourney      # 搜索关键词
```

### 命令行使用

```bash
# 生成今日日报
python3 commands/daily-report.py

# 生成 AI 增强日报
python3 commands/daily-report-ai.py

# 生成本周周报
python3 commands/weekly-report.py

# 生成日期区间报告
python3 commands/range-report.py --days 7
python3 commands/range-report.py --week
python3 commands/range-report.py --month
python3 commands/range-report.py --start 2026-04-01 --end 2026-04-15

# 搜索历史对话
python3 commands/search.py "AIJourney"
```

## 🤖 AI 增强功能

AIJourney 在 Claude Code 环境中自动使用内置 LLM，无需额外配置：

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

### LLM 配置优先级

1. **环境变量** `AIJOURNEY_LLM_PROVIDER`（用户显式指定）
2. **Claude Code 内置 LLM**（自动检测，无需 API Key）
3. **配置文件** `config.json`
4. **Mock 模式**（演示用）

## 🎯 支持的数据源

| 数据源 | 说明 | 跨平台支持 |
|--------|------|------------|
| **Claude Code** | 自动采集对话历史 | ✅ macOS / Windows / Linux |
| **CodeBuddy** | 自动采集代码助手会话 | ✅ macOS / Windows / Linux |
| **Git** | 自动扫描项目提交记录 | ✅ macOS / Windows / Linux |

## ⚙️ 配置说明

### 环境变量配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `AIJOURNEY_CLAUDE_PATH` | Claude Code 数据路径 | 自动识别平台 |
| `AIJOURNEY_CODEBUDDY_PATH` | CodeBuddy 数据路径 | 自动识别平台 |
| `AIJOURNEY_GIT_PATHS` | Git 仓库搜索路径（逗号分隔） | 常用目录列表 |
| `AIJOURNEY_REPORT_DIR` | 报告输出目录 | `./reports` |
| `AIJOURNEY_LLM_PROVIDER` | LLM 提供商 | 自动检测 |
| `AIJOURNEY_LLM_API_KEY` | LLM API Key | 可选 |

### 配置文件示例 (`config.json`)

```json
{
  "claude_code_path": "~/.claude",
  "codebuddy_storage_path": "~/Library/Application Support/CodeBuddy/storage",
  "git_search_paths": ["~/work", "~/projects", "~/code"],
  "report_dir": "./reports",
  "llm": {
    "api_key": "",
    "model": "claude-3-sonnet-20240229",
    "temperature": 0.3,
    "max_tokens": 4000
  }
}
```

### 路径自动识别规则

| 操作系统 | Claude Code 路径 | CodeBuddy 路径 |
|----------|-----------------|----------------|
| **macOS** | `~/.claude` | `~/Library/Application Support/CodeBuddy/storage` |
| **Windows** | `%APPDATA%\Claude` | `%APPDATA%\CodeBuddy\storage` |
| **Linux** | `~/.claude` | `~/.config/CodeBuddy/storage` |

## 📊 报告结构

### 日报
```markdown
# 📅 日报 - 2026年04月20日

## 📊 工作概览
| 项目 | 详情 |
|------|------|
| **日期** | 2026-04-20 |
| **总会话数** | 15 |

## 🎯 今日成果
1. **功能开发** - 完成配置系统优化
2. **Bug修复** - 修复跨平台路径问题

## 💡 技术亮点
- 使用策略模式实现统一接口
- 配置优先级设计：环境变量 > 配置文件 > 默认值
```

### AI 增强日报
AI 增强日报使用 Claude Code 内置 LLM 进行智能总结，提炼关键信息和成果价值。

### 区间报告
支持自定义日期范围：
```bash
# 最近 N 天
/range-report --days 7

# 本周
/range-report --week

# 本月
/range-report --month

# 自定义日期
/range-report --start 2026-04-01 --end 2026-04-15

# AI 增强模式
/range-report --week --ai
```

## 📦 OpenClaw Skill 说明

### 什么是 openclaw-skill 目录？

`openclaw-skill/` 目录是为 **OpenClaw 生态系统**准备的打包目录。OpenClaw 是一个 AI Agent 技能市场，允许开发者发布和分享可复用的 AI 技能。

#### 🎯 用途

| 场景 | 说明 |
|------|------|
| **跨平台部署** | 打包后可在任何支持 OpenClaw 的 AI 客户端中使用 |
| **技能市场发布** | 可以发布到 ClawHub（OpenClaw 技能仓库）供其他用户安装 |
| **统一格式** | 遵循 OpenClaw Skill 规范，便于自动化安装和管理 |

#### 📁 openclaw-skill 目录结构

```
openclaw-skill/
├── SKILL.md              # Skill 元数据和使用文档（必需）
├── scripts/              # 脚本目录（所有命令脚本）
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

### 为什么需要这个目录？

1. **规范兼容**：OpenClaw Skill 有严格的目录结构要求
2. **独立部署**：该目录包含完整的运行时代码，可独立打包发布
3. **多平台支持**：一份代码可部署到不同的 AI 客户端

### 打包和发布

```bash
# 打包 Skill（生成可发布的 zip 包）
zip -r aijourney-openclaw-skill.zip openclaw-skill/

# 发布到 ClawHub（需要 OpenClaw CLI）
skillhub publish ./openclaw-skill

# 本地安装测试
cp -r ./openclaw-skill ~/.openclaw/workspace/skills/ai_journey
```

### 与 Claude Code 插件的区别

| 特性 | `.claude-plugin/` | `openclaw-skill/` |
|------|-------------------|-------------------|
| **目标平台** | Claude Code IDE | OpenClaw 生态系统 |
| **安装方式** | 内置插件系统 | skillhub CLI |
| **用途** | 深度集成 Claude Code | 跨平台技能分发 |
| **依赖** | 依赖 Claude Code 环境 | 自包含，独立运行 |

> **提示**：对于大多数用户，直接使用 Claude Code 中的斜杠命令 `/daily-report` 即可，无需关注 `openclaw-skill/` 目录。该目录主要用于开发者发布到技能市场。

## 🛡️ 隐私说明

- ✅ 所有数据**仅存储在本地**
- ✅ 数据源直接读取本地工具存储，不经过第三方
- ✅ 在 Claude Code 中运行时，使用内置 LLM，数据不上传
- ⚠️ Git 提交信息可能包含敏感内容，请自行审查

## 📄 许可证

MIT License
