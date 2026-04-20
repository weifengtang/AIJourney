"""
Git 提交记录采集器

采集 Git 仓库的提交记录
支持跨平台路径自动识别（Windows/macOS/Linux）
支持通过环境变量手动指定搜索路径
"""

import subprocess
from datetime import date, datetime, timezone
from pathlib import Path
from typing import List, Dict, Tuple
import logging

from .base import BaseCollector, SessionData, Message, register_collector
from config import get_config


logger = logging.getLogger(__name__)


@register_collector
class GitCommitsCollector(BaseCollector):
    """Git 提交记录采集器"""
    
    name = "git_commits"
    version = "2.0.0"
    priority = 30
    
    def get_data_path(self) -> Path:
        """获取数据源路径（返回第一个搜索路径）"""
        return get_config().git_search_paths[0] if get_config().git_search_paths else Path('.')
    
    def collect(self, target_date: date, save_raw: bool = True) -> List[SessionData]:
        """
        采集指定日期的 Git 提交记录
        
        Git 数据搜索逻辑：
        - 搜索路径: 配置文件中指定的 git_search_paths
        - 自动发现: 在搜索路径下查找所有 .git 目录
        - 数据获取: 通过 git log 命令获取提交记录
        
        Args:
            target_date: 目标日期
            save_raw: 是否保存原始数据
        
        Returns:
            会话数据列表
        """
        logger.info(f"[{self.name}] 开始采集 {target_date} 的 Git 提交记录")
        
        search_paths = get_config().git_search_paths
        logger.info(f"[{self.name}] 搜索路径: {search_paths}")
        
        all_commits = []
        
        for search_path in search_paths:
            path = Path(search_path).expanduser()
            if not path.exists():
                logger.debug(f"[{self.name}] 搜索路径不存在: {path}")
                continue
            
            commits = self._search_git_repos(path, target_date)
            all_commits.extend(commits)
        
        # 按提交时间排序
        all_commits.sort(key=lambda s: s.start_time)
        
        # 保存原始数据（保持完整，不剪辑）
        if save_raw and all_commits:
            self.save_raw_data(all_commits, Path(search_paths[0]) if search_paths else Path('.'))
        
        logger.info(f"[{self.name}] 采集完成，获取到 {len(all_commits)} 条提交记录")
        return all_commits
    
    def _search_git_repos(self, search_path: Path, target_date: date) -> List[SessionData]:
        """
        在指定路径下搜索所有 Git 仓库并获取提交记录
        
        Args:
            search_path: 搜索路径
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        commits = []
        
        # 查找所有 .git 目录
        git_dirs = list(search_path.rglob(".git"))
        
        for git_dir in git_dirs:
            repo_path = git_dir.parent
            logger.debug(f"[{self.name}] 发现 Git 仓库: {repo_path}")
            
            try:
                repo_commits = self._get_commits_for_repo(repo_path, target_date)
                commits.extend(repo_commits)
            except Exception as e:
                logger.error(f"[{self.name}] 获取仓库 {repo_path} 提交记录失败: {e}")
        
        return commits
    
    def _get_commits_for_repo(self, repo_path: Path, target_date: date) -> List[SessionData]:
        """
        获取单个仓库指定日期的提交记录
        
        Args:
            repo_path: 仓库路径
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        commits = []
        
        # 构建 git log 命令
        # 格式: <timestamp>|<commit_hash>|<author>|<message>
        cmd = [
            'git', 'log',
            '--all',
            '--since', f"{target_date} 00:00:00",
            '--until', f"{target_date} 23:59:59",
            '--format=%at|%H|%an|%s',
            '--no-merges',
        ]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            # 如果有错误但不是致命错误，记录日志继续
            if result.stderr:
                logger.debug(f"[{self.name}] git log 警告: {result.stderr.strip()}")
            return commits
        
        # 解析输出
        for line in result.stdout.strip().split('\n'):
            if not line:
                continue
            
            parts = line.split('|', 3)
            if len(parts) < 4:
                continue
            
            try:
                timestamp = int(parts[0])
                commit_hash = parts[1]
                author = parts[2]
                message = parts[3]
                
                commit_time = datetime.fromtimestamp(timestamp)
                
                # 创建会话数据
                session_data = self._create_session_data(
                    repo_path,
                    commit_hash,
                    author,
                    message,
                    commit_time
                )
                commits.append(session_data)
                
            except Exception as e:
                logger.warning(f"[{self.name}] 解析提交记录失败: {line} - {e}")
        
        return commits
    
    def _create_session_data(self, repo_path: Path, commit_hash: str, 
                           author: str, message: str, commit_time: datetime) -> SessionData:
        """
        创建会话数据
        
        Args:
            repo_path: 仓库路径
            commit_hash: 提交哈希
            author: 作者
            message: 提交消息
            commit_time: 提交时间
        
        Returns:
            SessionData 实例
        """
        # 获取仓库名
        repo_name = repo_path.name
        
        # 生成标题
        title = f"[{repo_name}] {message[:40]}" + ('...' if len(message) > 40 else '')
        
        # 生成摘要
        summary = f"提交者: {author}\n提交消息: {message}"
        
        # 创建模拟消息
        messages = [
            Message(
                role='user',
                content=f"提交代码到 {repo_name}",
                timestamp=commit_time,
            ),
            Message(
                role='assistant',
                content=f"已提交 [{commit_hash[:7]}]: {message}",
                timestamp=commit_time,
            ),
        ]
        
        # 获取修改的文件（使用 git show --stat）
        files_modified = self._get_modified_files(repo_path, commit_hash)
        
        return SessionData(
            session_id=commit_hash,
            source=self.name,
            project_path=str(repo_path),
            start_time=commit_time,
            end_time=commit_time,
            title=title,
            summary=summary,
            messages=messages,
            files_modified=files_modified,
            tokens_input=0,
            tokens_output=0,
        )
    
    def _get_modified_files(self, repo_path: Path, commit_hash: str) -> List[str]:
        """
        获取提交修改的文件列表
        
        Args:
            repo_path: 仓库路径
            commit_hash: 提交哈希
        
        Returns:
            修改的文件列表
        """
        cmd = ['git', 'show', '--stat', commit_hash]
        
        result = subprocess.run(
            cmd,
            cwd=repo_path,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace'
        )
        
        if result.returncode != 0:
            return []
        
        files = []
        for line in result.stdout.strip().split('\n'):
            # 跳过头部信息，只处理文件行
            if '|' in line and line.strip():
                parts = line.split('|')[0].strip()
                if parts and not parts.startswith(' '):
                    files.append(parts)
        
        return files