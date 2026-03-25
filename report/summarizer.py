"""
会话摘要生成器

使用 LLM 或规则提取生成会话摘要
"""

import json
import hashlib
import logging
import requests
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime

from collectors.base import SessionData, Message


logger = logging.getLogger(__name__)


@dataclass
class SessionSummary:
    """会话摘要"""
    goal: str                          # 目标
    key_questions: List[str]           # 关键问题
    achievements: List[str]            # 主要成果
    files_modified: List[str]          # 修改文件
    tech_points: List[str]             # 技术要点
    summary_method: str                # 摘要方法：llm / rule
    
    def to_dict(self) -> dict:
        return {
            "goal": self.goal,
            "key_questions": self.key_questions,
            "achievements": self.achievements,
            "files_modified": self.files_modified,
            "tech_points": self.tech_points,
            "summary_method": self.summary_method,
        }
    
    def to_markdown(self) -> str:
        """转换为 Markdown 格式"""
        lines = []
        
        if self.goal:
            lines.append(f"- **目标**: {self.goal}")
        
        if self.key_questions:
            lines.append("- **关键问题**:")
            for q in self.key_questions[:3]:
                lines.append(f"  - {q}")
        
        if self.achievements:
            lines.append("- **主要成果**:")
            for a in self.achievements[:5]:
                lines.append(f"  - {a}")
        
        if self.files_modified:
            lines.append(f"- **修改文件**: {', '.join(self.files_modified[:5])}")
        
        if self.tech_points:
            lines.append(f"- **技术要点**: {', '.join(self.tech_points[:5])}")
        
        return "\n".join(lines)


class SessionSummarizer:
    """会话摘要生成器"""
    
    SUMMARY_PROMPT = """请总结以下 AI 协作会话，输出结构化摘要。

## 会话内容
{messages}

## 输出格式（严格 JSON）
{{
  "goal": "一句话描述会话目标",
  "key_questions": ["问题1", "问题2"],
  "achievements": ["成果1", "成果2"],
  "files_modified": ["文件1", "文件2"],
  "tech_points": ["技术点1", "技术点2"]
}}

## 要求
1. goal: 一句话概括会话主要目标
2. key_questions: 用户提出的 2-3 个核心问题
3. achievements: 完成的主要工作（用 ✅ 开头）
4. files_modified: 提到的文件路径
5. tech_points: 涉及的技术关键词

只输出 JSON，不要其他内容。"""

    def __init__(self, settings_path: Optional[Path] = None):
        """
        初始化摘要生成器
        
        Args:
            settings_path: settings.json 路径
        """
        self.settings_path = settings_path or Path(__file__).parent.parent / "settings.json"
        self.settings = self._load_settings()
        self.cache_dir = Path(self.settings.get("summary", {}).get("cache_dir", "./output/.summary_cache"))
        
        if self.settings.get("summary", {}).get("cache_enabled", True):
            self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _load_settings(self) -> dict:
        """加载配置"""
        if self.settings_path.exists():
            with open(self.settings_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"llm": {"enabled": False}, "summary": {}}
    
    def _get_cache_key(self, session: SessionData) -> str:
        """生成缓存 key"""
        content = f"{session.session_id}_{session.start_time}_{len(session.messages)}"
        return hashlib.md5(content.encode()).hexdigest()
    
    def _get_cached_summary(self, cache_key: str) -> Optional[SessionSummary]:
        """获取缓存的摘要"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return SessionSummary(**data)
            except Exception as e:
                logger.warning(f"[summarizer] 读取缓存失败: {e}")
        return None
    
    def _save_cached_summary(self, cache_key: str, summary: SessionSummary):
        """保存摘要到缓存"""
        cache_file = self.cache_dir / f"{cache_key}.json"
        try:
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.warning(f"[summarizer] 保存缓存失败: {e}")
    
    def summarize(self, session: SessionData) -> SessionSummary:
        """
        生成会话摘要
        
        Args:
            session: 会话数据
        
        Returns:
            会话摘要
        """
        # 检查缓存
        if self.settings.get("summary", {}).get("cache_enabled", True):
            cache_key = self._get_cache_key(session)
            cached = self._get_cached_summary(cache_key)
            if cached:
                logger.info(f"[summarizer] 使用缓存摘要: {session.session_id[:8]}")
                return cached
        
        # 生成摘要
        if self.settings.get("llm", {}).get("enabled", False):
            summary = self._summarize_with_llm(session)
        else:
            summary = self._summarize_with_rules(session)
        
        # 保存缓存
        if self.settings.get("summary", {}).get("cache_enabled", True):
            self._save_cached_summary(cache_key, summary)
        
        return summary
    
    def _summarize_with_llm(self, session: SessionData) -> SessionSummary:
        """使用 LLM 生成摘要"""
        llm_config = self.settings.get("llm", {})
        
        # 准备消息内容
        max_msgs = llm_config.get("max_messages", 50)
        messages_content = self._format_messages(session.messages[:max_msgs])
        
        # 准备 prompt
        prompt = self.SUMMARY_PROMPT.format(messages=messages_content)
        
        try:
            # 调用 API
            api_key = llm_config.get("api_key", "")
            api_base_url = llm_config.get("api_base_url", "")
            model = llm_config.get("model", "ark-code-latest")
            max_tokens = llm_config.get("max_tokens", 1000)
            timeout = llm_config.get("timeout", 30)
            
            if not api_key:
                logger.warning("[summarizer] API key 未配置，使用规则提取")
                return self._summarize_with_rules(session)
            
            response = requests.post(
                f"{api_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "max_tokens": max_tokens,
                    "messages": [{"role": "user", "content": prompt}]
                },
                timeout=timeout
            )
            
            if response.status_code == 200:
                data = response.json()
                content = data["choices"][0]["message"]["content"]
                
                # 解析 JSON
                summary_data = self._parse_llm_response(content)
                
                return SessionSummary(
                    goal=summary_data.get("goal", ""),
                    key_questions=summary_data.get("key_questions", []),
                    achievements=summary_data.get("achievements", []),
                    files_modified=summary_data.get("files_modified", []),
                    tech_points=summary_data.get("tech_points", []),
                    summary_method="llm"
                )
            else:
                logger.warning(f"[summarizer] LLM API 调用失败: {response.status_code}")
                return self._summarize_with_rules(session)
                
        except Exception as e:
            logger.warning(f"[summarizer] LLM 调用异常: {e}")
            return self._summarize_with_rules(session)
    
    def _parse_llm_response(self, content: str) -> dict:
        """解析 LLM 响应"""
        try:
            # 尝试直接解析
            return json.loads(content)
        except json.JSONDecodeError:
            # 尝试提取 JSON
            import re
            match = re.search(r'\{[\s\S]*\}', content)
            if match:
                try:
                    return json.loads(match.group())
                except:
                    pass
        return {}
    
    def _summarize_with_rules(self, session: SessionData) -> SessionSummary:
        """使用规则提取摘要"""
        import re
        
        # 1. 提取用户问题
        key_questions = []
        for msg in session.messages:
            if msg.role == "user":
                content = re.sub(r'<[^>]+>', '', msg.content).strip()
                content = content.replace('\n', ' ')[:100]
                if content and len(content) > 10:
                    key_questions.append(content)
                if len(key_questions) >= 3:
                    break
        
        # 2. 提取文件路径
        all_content = " ".join(m.content for m in session.messages[:50])
        file_pattern = r'[\`\']?(/[a-zA-Z0-9_\-./]+\.[a-zA-Z]{1,10})[\`\']?'
        files = list(set(re.findall(file_pattern, all_content)))
        files = sorted([f for f in files if len(f) < 100 and not f.startswith('/var/')])[:10]
        
        # 3. 提取成果（✅ 开头的句子）
        achievements = []
        achievement_pattern = r'✅\s*([^\n]{10,100})'
        achievements = re.findall(achievement_pattern, all_content)[:5]
        
        # 4. 提取技术关键词
        tech_keywords = [
            "Claude Code", "CodeBuddy", "SQLite", "JSON", "API",
            "采集器", "配置", "路径", "Token", "消息", "摘要",
            "Python", "JavaScript", "TypeScript", "React", "Vue",
        ]
        tech_points = []
        for kw in tech_keywords:
            if kw.lower() in all_content.lower():
                tech_points.append(kw)
        
        return SessionSummary(
            goal=session.title or "会话摘要",
            key_questions=key_questions,
            achievements=achievements,
            files_modified=files,
            tech_points=tech_points[:5],
            summary_method="rule"
        )
    
    def _format_messages(self, messages: List[Message]) -> str:
        """格式化消息列表"""
        lines = []
        for i, msg in enumerate(messages, 1):
            role = "用户" if msg.role == "user" else "助手"
            content = msg.content[:500]  # 限制长度
            lines.append(f"[{i}] {role}: {content}")
        return "\n".join(lines)
