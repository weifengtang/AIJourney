# AI Journey 🤖📊

> **Claude Code 原生 Skill** - 自动采集 AI 对话历史，生成智能日报/周报，让每一次 AI 协作都被永久记录

![GitHub stars](https://img.shields.io/github/stars/weifengtang/AIJourney?style=social)
![GitHub forks](https://img.shields.io/github/forks/weifengtang/AIJourney?style=social)
![GitHub issues](https://img.shields.io/github/issues/weifengtang/AIJourney)
![GitHub license](https://img.shields.io/github/license/weifengtang/AIJourney)
![Python Version](https://img.shields.io/badge/python-3.9%2B-blue)
![Platform](https://img.shields.io/badge/platform-macOS%20%7C%20Windows%20%7C%20Linux-green)

---

## ✨ 为什么选择 AI Journey？

在 AI 时代，我们每天与 AI 进行大量协作，但这些宝贵的对话历史往往被遗忘。**AI Journey** 帮助您：

- 🤖 **自动采集** - 智能捕获 Claude Code、CodeBuddy、Git 提交记录
- 🧠 **AI 增强** - 使用 Claude Code 内置 LLM 生成高质量智能报告
- 📱 **跨平台** - 完美支持 macOS、Windows、Linux
- 🔒 **隐私保护** - 所有数据本地处理，不上传云端
- ⚡ **一键生成** - 简单命令即可生成日报/周报

---

## 🚀 快速开始

### 在 Claude Code 中使用（推荐）

直接输入斜杠命令，即刻生成报告：

```
/daily-report          # 📅 生成今日日报（AI 增强版）
/weekly-report         # 📊 生成本周周报（AI 增强版）
/range-report --week   # 📈 生成日期区间报告
/search AIJourney      # 🔍 搜索历史对话
```

### 命令行使用

```bash
# 生成今日日报（默认 AI 增强）
python3 commands/daily-report.py

# 生成本周周报
python3 commands/weekly-report.py

# 生成日期区间报告
python3 commands/range-report.py --days 7    # 最近7天
python3 commands/range-report.py --week      # 本周
python3 commands/range-report.py --month     # 本月
python3 commands/range-report.py --start 2026-04-01 --end 2026-04-15
```

---

## 📁 项目结构

```
AIJourney/
├── .claude-plugin/          # Claude Code 插件配置
│   └── plugin.json          # 插件元数据和命令定义
├── commands/                # 斜杠命令处理
│   ├── daily-report.py      # /daily-report - AI 增强日报（默认）
│   ├── weekly-report.py     # /weekly-report - AI 增强周报
│   ├── range-report.py      # /range-report - 日期区间报告
│   └── search.py            # /search - 搜索历史对话
├── collectors/              # 数据采集器
│   ├── base.py              # 基础采集器类
│   ├── claude_code.py       # Claude Code 采集器
│   ├── codebuddy.py         # CodeBuddy 采集器
│   └── git_commits.py       # Git 提交采集器
├── llm/                     # LLM 报告增强模块
│   └── report_enhancer.py   # AI 报告增强器
├── openclaw-skill/          # OpenClaw Skill 打包目录
├── config.py                # 配置模块（跨平台路径管理）
├── config.json              # 配置文件示例
└── reports/                 # 生成的报告文件
```

---

## 🎯 支持的数据源

| 数据源 | 说明 | 跨平台支持 |
|--------|------|------------|
| **Claude Code** | 自动采集对话历史 | ✅ macOS / Windows / Linux |
| **CodeBuddy** | 自动采集代码助手会话 | ✅ macOS / Windows / Linux |
| **Git** | 自动扫描项目提交记录 | ✅ macOS / Windows / Linux |

---

## 🔧 配置说明

### 环境变量配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `AIJOURNEY_CLAUDE_PATH` | Claude Code 数据路径 | 自动识别平台 |
| `AIJOURNEY_CODEBUDDY_PATH` | CodeBuddy 数据路径 | 自动识别平台 |
| `AIJOURNEY_GIT_PATHS` | Git 仓库搜索路径 | 常用目录列表 |
| `AIJOURNEY_REPORT_DIR` | 报告输出目录 | `./reports` |
| `AIJOURNEY_LLM_PROVIDER` | LLM 提供商 | 自动检测 |

### 配置文件示例 (`config.json`)

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

---

## 🤖 AI 增强功能

AI Journey 在 Claude Code 环境中**自动使用内置 LLM**，无需额外配置 API Key：

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

**LLM 配置优先级**：
1. 环境变量 `AIJOURNEY_LLM_PROVIDER`（用户显式指定）
2. **Claude Code 内置 LLM**（自动检测，无需 API Key）
3. 配置文件 `config.json`
4. Mock 模式（演示用）

---

## 📊 报告示例

### 日报输出示例

```markdown
# 📅 日报 - 2026年04月20日

## 📊 工作概览
| 项目 | 详情 |
|------|------|
| **日期** | 2026-04-20 |
| **Claude 会话数** | 5 |
| **Git 提交记录** | 97 |
| **总记录数** | 102 |

## 🎯 今日成果
1. **技能查询与 AI Journey 集成** - 完成了可用技能列表查询功能
2. **数据采集系统验证** - 验证了 Claude Code 会话采集和 Git 提交采集

## 💡 技术亮点
- 多数据源支持: Claude Code 历史会话 + 多目录 Git 提交自动发现
- 智能 AI 增强: 使用内置 LLM 自动提炼工作成果
```

---

## 📦 OpenClaw Skill

`openclaw-skill/` 目录是为 **OpenClaw 生态系统**准备的打包目录，可发布到技能市场供其他用户使用。

```bash
# 打包 Skill
zip -r aijourney-skill.zip openclaw-skill/

# 本地安装测试
cp -r ./openclaw-skill ~/.openclaw/workspace/skills/ai_journey
```

---

## 🛡️ 隐私说明

- ✅ 所有数据**仅存储在本地**
- ✅ 数据源直接读取本地工具存储，不经过第三方
- ✅ 在 Claude Code 中运行时，使用内置 LLM，数据不上传
- ⚠️ Git 提交信息可能包含敏感内容，请自行审查

---

## 🤝 贡献指南

欢迎贡献代码！请遵循以下步骤：

1. Fork 本仓库
2. 创建功能分支 `git checkout -b feature/your-feature`
3. 提交更改 `git commit -m "feat: 添加新功能"`
4. 推送到分支 `git push origin feature/your-feature`
5. 创建 Pull Request

---

## 📄 许可证

MIT License

---

⭐ **如果这个项目对你有帮助，请给个 Star！**

---

