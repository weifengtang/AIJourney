"""
Git Commits 采集器

扫描本地 git 仓库的 commit 记录，重建编码活动时间线
支持 macOS / Windows / Linux
"""

import os
import re
import subprocess
import hashlib
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import platform


from .base import BaseCollector, SessionData, Message, register_collector


logger = logging.getLogger(__name__)


def _get_home_dir() -> Path:
    return Path.home()


def _is_windows() -> bool:
    return platform.system() == "Windows"


@register_collector
class GitCommitsCollector(BaseCollector):
    """Git Commits 采集器"""

    name = "git_commits"
    version = "1.0.0"
    priority = 55

    DEFAULT_SEARCH_DIRS = [
        "~/work",
        "~/projects",
        "~/code",
        "~/repos",
        "~/Documents",
        "~/Desktop",
        "~",
    ]

    def get_data_path(self) -> Path:
        return _get_home_dir()

    def validate(self) -> bool:
        try:
            result = subprocess.run(
                ["git", "--version"],
                capture_output=True, text=True, timeout=5
            )
            if result.returncode != 0:
                logger.warning(f"[{self.name}] git 未安装或不可用")
                return False
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.warning(f"[{self.name}] git 未安装或不可用")
            return False

        repos = self._find_git_repos()
        if not repos:
            logger.warning(f"[{self.name}] 未找到任何 git 仓库")
            return False
        logger.info(f"[{self.name}] 找到 {len(repos)} 个 git 仓库")
        return True

    def collect(self, target_date: date) -> List[SessionData]:
        logger.info(f"[{self.name}] 开始采集 {target_date} 的 Git 提交记录")

        repos = self._find_git_repos()
        if not repos:
            logger.warning(f"[{self.name}] 未找到 git 仓库，跳过采集")
            return []

        all_sessions = []

        for repo_path in repos:
            commits = self._get_commits_for_date(repo_path, target_date)
            if not commits:
                continue

            session = self._build_session(commits, repo_path, target_date)
            if session:
                all_sessions.append(session)

        all_sessions.sort(key=lambda s: s.start_time)
        logger.info(f"[{self.name}] 采集完成，获取到 {len(all_sessions)} 个仓库的提交记录")
        return all_sessions

    def _find_git_repos(self, max_depth: int = 3) -> List[Path]:
        home = _get_home_dir()
        repos = []
        seen = set()

        search_dirs = []
        for d in self.DEFAULT_SEARCH_DIRS:
            expanded = Path(d).expanduser()
            if expanded.exists():
                search_dirs.append(expanded)

        for search_dir in search_dirs:
            if not search_dir.is_dir():
                continue
            try:
                for item in search_dir.iterdir():
                    if not item.is_dir():
                        continue
                    resolved = item.resolve()
                    if resolved in seen:
                        continue
                    seen.add(resolved)

                    git_dir = item / ".git"
                    if git_dir.exists():
                        repos.append(item)
                        continue

                    if max_depth > 1:
                        sub_repos = self._find_git_repos_recursive(item, max_depth - 1, seen)
                        repos.extend(sub_repos)
            except PermissionError:
                continue

        return repos

    def _find_git_repos_recursive(
        self, base_dir: Path, remaining_depth: int, seen: set
    ) -> List[Path]:
        repos = []
        if remaining_depth <= 0:
            return repos

        try:
            for item in base_dir.iterdir():
                if not item.is_dir():
                    continue
                if item.name.startswith("."):
                    continue
                resolved = item.resolve()
                if resolved in seen:
                    continue
                seen.add(resolved)

                git_dir = item / ".git"
                if git_dir.exists():
                    repos.append(item)
                    continue

                sub_repos = self._find_git_repos_recursive(item, remaining_depth - 1, seen)
                repos.extend(sub_repos)
        except PermissionError:
            pass

        return repos

    def _get_commits_for_date(
        self, repo_path: Path, target_date: date
    ) -> List[Dict]:
        date_str = target_date.isoformat()
        cmd = [
            "git", "-C", str(repo_path), "log",
            f"--since={date_str} 00:00:00",
            f"--until={date_str} 23:59:59",
            "--all",
            "--format=%H|%aI|%s|%an|%b",
        ]

        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode != 0:
                return []
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return []

        commits = []
        for line in result.stdout.strip().splitlines():
            if not line.strip():
                continue
            parts = line.split("|", 4)
            if len(parts) < 4:
                continue

            commit_hash = parts[0][:8]
            timestamp_str = parts[1]
            subject = parts[2]
            author = parts[3]
            body = parts[4] if len(parts) > 4 else ""

            try:
                timestamp = datetime.fromisoformat(timestamp_str)
            except ValueError:
                continue

            commits.append({
                "hash": commit_hash,
                "timestamp": timestamp,
                "subject": subject,
                "author": author,
                "body": body.strip(),
            })

        commits.sort(key=lambda c: c["timestamp"])
        return commits

    def _build_session(
        self, commits: List[Dict], repo_path: Path, target_date: date
    ) -> Optional[SessionData]:
        if not commits:
            return None

        messages = []
        files_modified = []

        for commit in commits:
            content = f"[{commit['hash']}] {commit['subject']}"
            if commit["body"]:
                content += f"\n{commit['body']}"
            messages.append(Message(
                role="user",
                content=content,
                timestamp=commit["timestamp"],
            ))

        try:
            cmd = [
                "git", "-C", str(repo_path), "diff-tree",
                "--no-commit-id", "--name-only", "-r", commits[-1]["hash"],
            ]
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                files_modified = [
                    f.strip() for f in result.stdout.strip().splitlines() if f.strip()
                ]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        start_time = commits[0]["timestamp"]
        end_time = commits[-1]["timestamp"]

        total_commits = len(commits)
        authors = set(c["author"] for c in commits)
        summary = f"{total_commits} 次提交，作者: {', '.join(authors)}"

        first_subject = commits[0]["subject"][:50]
        title = f"[{repo_path.name}] {first_subject}"
        if total_commits > 1:
            title += f" (+{total_commits - 1} more)"

        session_id = hashlib.md5(
            f"git_commits_{repo_path}_{target_date.isoformat()}".encode()
        ).hexdigest()[:16]

        return SessionData(
            session_id=session_id,
            source=self.name,
            project_path=str(repo_path),
            start_time=start_time,
            end_time=end_time,
            title=title,
            summary=summary,
            messages=messages,
            files_modified=files_modified,
            tokens_input=0,
            tokens_output=0,
        )
