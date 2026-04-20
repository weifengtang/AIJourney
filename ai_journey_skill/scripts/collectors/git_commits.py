"""
Git 提交记录采集器（优化版）

优化点：
1. Git 仓库缓存机制（P0）
2. Git 增量采集（P0）
3. 搜索剪枝优化（P1）
"""

import subprocess
from datetime import date, datetime
from pathlib import Path
from typing import List, Dict, Tuple
import logging
import os

from .base import BaseCollector, SessionData, Message, register_collector
from config import get_config
from utils.cache import cache_manager

logger = logging.getLogger(__name__)


# 搜索剪枝：跳过的目录名称
SKIP_DIRS = {
    'node_modules', '.git', '.venv', 'venv', '__pycache__',
    '.npm', '.yarn', 'build', 'dist', '.idea', '.vscode',
    'vendor', 'target', 'Caches', '.Trash', 'Library'
}

# 最大搜索深度
MAX_SEARCH_DEPTH = 6


@register_collector
class GitCommitsCollector(BaseCollector):
    """Git 提交记录采集器（优化版）"""
    
    name = "git_commits"
    version = "3.0.0"
    priority = 30
    
    def __init__(self):
        self._cached_repos = None
    
    def get_data_path(self) -> Path:
        """获取数据源路径（返回第一个搜索路径）"""
        return get_config().git_search_paths[0] if get_config().git_search_paths else Path('.')
    
    def _search_git_repos_with_cache(self, search_path: Path) -> List[Path]:
        """
        搜索 Git 仓库，使用缓存机制（P0）
        
        Args:
            search_path: 搜索路径
        
        Returns:
            Git 仓库路径列表
        """
        # 尝试使用内存缓存
        if self._cached_repos is not None:
            logger.debug(f"[{self.name}] 使用内存缓存的仓库列表")
            return self._cached_repos
        
        # 尝试加载文件缓存
        cache_data = cache_manager.load_cache("git_repos")
        if cache_data is not None:
            repos_data = cache_data.get("data", [])
            self._cached_repos = [Path(r) for r in repos_data]
            logger.debug(f"[{self.name}] 使用文件缓存的仓库列表，共 {len(self._cached_repos)} 个")
            return self._cached_repos
        
        # 执行全目录搜索
        logger.info(f"[{self.name}] 首次搜索 Git 仓库...")
        repos = []
        
        try:
            repos = self._search_git_repos_recursive(search_path, current_depth=0)
        except Exception as e:
            logger.error(f"[{self.name}] 搜索 Git 仓库失败: {e}")
        
        # 去重
        repos = list(dict.fromkeys(repos))
        
        # 保存缓存
        self._cached_repos = repos
        cache_manager.save_cache("git_repos", [str(r) for r in repos], ttl_days=7)
        
        logger.info(f"[{self.name}] 发现 {len(repos)} 个 Git 仓库")
        return repos
    
    def _search_git_repos_recursive(self, path: Path, current_depth: int) -> List[Path]:
        """
        递归搜索 Git 仓库（带剪枝优化）
        
        Args:
            path: 当前路径
            current_depth: 当前深度
        
        Returns:
            Git 仓库路径列表
        """
        repos = []
        
        # 超过最大深度，停止搜索
        if current_depth > MAX_SEARCH_DEPTH:
            return repos
        
        try:
            # 检查权限
            if not os.access(path, os.R_OK):
                return repos
            
            for child in path.iterdir():
                # 跳过符号链接
                if child.is_symlink():
                    continue
                
                # 跳过黑名单目录
                if child.name in SKIP_DIRS:
                    continue
                
                # 跳过隐藏目录（除了 .git）
                if child.name.startswith('.') and child.name != '.git':
                    continue
                
                try:
                    if child.is_dir():
                        # 检查是否是 Git 仓库
                        git_dir = child / ".git"
                        if git_dir.exists() and git_dir.is_dir():
                            repos.append(child)
                        else:
                            # 继续递归搜索
                            repos.extend(self._search_git_repos_recursive(child, current_depth + 1))
                except PermissionError:
                    continue
                except Exception as e:
                    logger.debug(f"[{self.name}] 访问 {child} 失败: {e}")
                    continue
        
        except PermissionError:
            pass
        except Exception as e:
            logger.debug(f"[{self.name}] 搜索路径 {path} 失败: {e}")
        
        return repos
    
    def _get_cached_commits(self, repo_path: Path, target_date: date) -> set:
        """
        获取已缓存的提交记录（增量采集）
        
        Args:
            repo_path: 仓库路径
            target_date: 目标日期
        
        Returns:
            已采集的提交哈希集合
        """
        cache_key = f"git_commits_{repo_path.name}_{target_date}"
        cache_data = cache_manager.load_cache(cache_key)
        
        if cache_data is not None:
            return set(cache_data.get("data", []))
        
        return set()
    
    def _save_cached_commits(self, repo_path: Path, target_date: date, commit_hashes: set) -> None:
        """
        保存提交记录到缓存
        
        Args:
            repo_path: 仓库路径
            target_date: 目标日期
            commit_hashes: 提交哈希集合
        """
        cache_key = f"git_commits_{repo_path.name}_{target_date}"
        cache_manager.save_cache(cache_key, list(commit_hashes), ttl_days=30)
    
    def collect(self, target_date: date, save_raw: bool = True) -> List[SessionData]:
        """
        采集指定日期的 Git 提交记录（优化版）
        
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
        在指定路径下搜索所有 Git 仓库并获取提交记录（优化版）
        
        Args:
            search_path: 搜索路径
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        commits = []
        
        # 使用缓存的仓库列表
        repos = self._search_git_repos_with_cache(search_path)
        
        for repo_path in repos:
            logger.debug(f"[{self.name}] 处理 Git 仓库: {repo_path}")
            
            try:
                repo_commits = self._get_commits_for_repo(repo_path, target_date)
                commits.extend(repo_commits)
            except Exception as e:
                logger.error(f"[{self.name}] 获取仓库 {repo_path} 提交记录失败: {e}")
        
        return commits
    
    def _get_commits_for_repo(self, repo_path: Path, target_date: date) -> List[SessionData]:
        """
        获取单个仓库指定日期的提交记录（增量采集）
        
        Args:
            repo_path: 仓库路径
            target_date: 目标日期
        
        Returns:
            会话数据列表
        """
        commits = []
        
        # 加载已缓存的提交
        cached_hashes = self._get_cached_commits(repo_path, target_date)
        
        # 构建 git log 命令
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
            if result.stderr:
                logger.debug(f"[{self.name}] git log 警告: {result.stderr.strip()}")
            return commits
        
        new_hashes = set()
        
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
                
                # 跳过已采集的提交（增量采集）
                if commit_hash in cached_hashes:
                    continue
                
                new_hashes.add(commit_hash)
                
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
        
        # 保存新采集的提交
        if new_hashes:
            self._save_cached_commits(repo_path, target_date, cached_hashes | new_hashes)
        
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
        repo_name = repo_path.name
        
        title = f"[{repo_name}] {message[:40]}" + ('...' if len(message) > 40 else '')
        
        summary = f"提交者: {author}\n提交消息: {message}"
        
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
            if '|' in line and line.strip():
                parts = line.split('|')[0].strip()
                if parts and not parts.startswith(' '):
                    files.append(parts)
        
        return files