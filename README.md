# SumAll - 程序员每日工作会话自动归档框架

自动采集多个开发工具的会话数据，生成结构化的工作日报。

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 运行（采集今天的数据）
python main.py

# 指定日期
python main.py --date 2026-03-25

# 指定输出目录
python main.py --output ./my_reports

# 指定采集器
python main.py --collectors claude_code codebuddy

# 调试模式
python main.py --log-level DEBUG
```

## 项目结构

```
SumAll/
├── main.py              # 主程序入口
├── config.py            # 配置管理
├── collectors/          # 采集器模块
│   ├── __init__.py
│   ├── base.py          # 采集器基类
│   ├── claude_code.py   # Claude Code 采集器
│   ├── codebuddy.py     # CodeBuddy 采集器
│   ├── vscode.py        # VSCode 采集器
│   └── idea.py          # IDEA 采集器
├── output/              # 输出目录
├── logs/                # 日志目录
├── spec/                # 需求文档
│   ├── Me2AI/           # 用户维护层
│   └── AI2AI/           # AI 维护层
└── rules/               # 项目规范
```

## 支持的采集器

| 采集器 | 数据源 | 状态 |
|--------|--------|------|
| Claude Code | `~/.claude/` | ✅ 空实现 |
| CodeBuddy | `~/Library/Application Support/CodeBuddy/` | ✅ 空实现 |
| VSCode | `~/Library/Application Support/Code/User/History/` | ✅ 空实现 |
| IDEA | `~/Library/Application Support/JetBrains/` | ✅ 空实现 |

## 输出格式

- **JSON**: `daily_report_YYYYMMDD.json`
- **Markdown**: `daily_report_YYYYMMDD.md`

## 开发状态

- [x] M0: 概要设计完成
- [x] M1: 框架完成
- [x] M1.1: 扩展采集器完成（空实现）
- [ ] M2: 日报生成完成
- [ ] M3: Claude Code 插件完成
- [ ] M3: CodeBuddy 插件完成

## 许可证

MIT
