"""
Shell History 采集器

采集用户的 Shell 命令历史记录，支持：
- macOS: zsh_history, bash_history
- Windows: PowerShell PSReadLine 历史
"""

import os
import re
import hashlib
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import logging
import platform

from .base import BaseCollector, SessionData, Message, register_collector


logger = logging.getLogger(__name__)


def _get_home_dir() -> Path:
    return Path.home()


def _is_macos() -> bool:
    return platform.system() == "Darwin"


def _is_windows() -> bool:
    return platform.system() == "Windows"


def _is_linux() -> bool:
    return platform.system() == "Linux"


@register_collector
class ShellHistoryCollector(BaseCollector):
    """Shell History 采集器"""

    name = "shell_history"
    version = "1.0.0"
    priority = 50

    def get_data_path(self) -> Path:
        return _get_home_dir()

    def validate(self) -> bool:
        history_files = self._find_history_files()
        if not history_files:
            logger.warning(f"[{self.name}] 未找到任何 shell 历史文件")
            return False
        logger.info(f"[{self.name}] 找到 {len(history_files)} 个历史文件: {list(history_files.keys())}")
        return True

    def collect(self, target_date: date) -> List[SessionData]:
        logger.info(f"[{self.name}] 开始采集 {target_date} 的 Shell 历史记录")

        history_files = self._find_history_files()
        if not history_files:
            logger.warning(f"[{self.name}] 未找到历史文件，跳过采集")
            return []

        all_sessions = []

        for shell_type, file_path in history_files.items():
            logger.info(f"[{self.name}] 处理 {shell_type}: {file_path}")
            commands = self._parse_history_file(file_path, shell_type, target_date)

            if not commands:
                logger.info(f"[{self.name}] {shell_type} 在 {target_date} 无命令记录")
                continue

            session = self._build_session(commands, shell_type, target_date)
            if session:
                all_sessions.append(session)

        logger.info(f"[{self.name}] 采集完成，获取到 {len(all_sessions)} 个会话")
        return all_sessions

    def _find_history_files(self) -> Dict[str, Path]:
        home = _get_home_dir()
        files = {}

        if _is_macos() or _is_linux():
            zsh_history = home / ".zsh_history"
            if zsh_history.exists():
                files["zsh"] = zsh_history

            bash_history = home / ".bash_history"
            if bash_history.exists():
                files["bash"] = bash_history

            fish_history = home / ".local/share/fish/fish_history"
            if fish_history.exists():
                files["fish"] = fish_history

        elif _is_windows():
            ps_history = home / "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
            if ps_history.exists():
                files["powershell"] = ps_history

            cmd_history = home / "AppData/Roaming/Microsoft/Windows/PowerShell/PSReadLine/ConsoleHost_history.txt"
            if cmd_history.exists() and "cmd" not in files:
                files["cmd"] = cmd_history

        return files

    def _parse_history_file(
        self, file_path: Path, shell_type: str, target_date: date
    ) -> List[Tuple[datetime, str]]:
        try:
            if shell_type == "zsh":
                return self._parse_zsh_history(file_path, target_date)
            elif shell_type == "bash":
                return self._parse_bash_history(file_path, target_date)
            elif shell_type == "fish":
                return self._parse_fish_history(file_path, target_date)
            elif shell_type in ("powershell", "cmd"):
                return self._parse_powershell_history(file_path, target_date)
            else:
                return []
        except Exception as e:
            logger.error(f"[{self.name}] 解析 {file_path} 失败: {e}")
            return []

    def _parse_zsh_history(
        self, file_path: Path, target_date: date
    ) -> List[Tuple[datetime, str]]:
        commands = []
        no_timestamp_cmds = []
        current_timestamp = None

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            try:
                content = file_path.read_text(encoding="latin-1", errors="replace")
            except Exception as e:
                logger.error(f"[{self.name}] 无法读取 {file_path}: {e}")
                return []

        has_timestamps = False

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue

            if line.startswith(": "):
                match = re.match(
                    r"^: (\d+):\d+;(.*)$", line
                )
                if match:
                    has_timestamps = True
                    ts_str = match.group(1)
                    try:
                        current_timestamp = datetime.fromtimestamp(int(ts_str))
                    except (ValueError, OSError):
                        current_timestamp = None
                    cmd = match.group(2).strip()
                    if cmd and current_timestamp and current_timestamp.date() == target_date:
                        commands.append((current_timestamp, cmd))
                else:
                    if line:
                        no_timestamp_cmds.append(line)
            else:
                if current_timestamp and current_timestamp.date() == target_date:
                    commands.append((current_timestamp, line))
                else:
                    no_timestamp_cmds.append(line)

        if not has_timestamps and no_timestamp_cmds:
            logger.info(f"[{self.name}] zsh_history 无时间戳，将所有命令归入 {target_date}")
            file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
            for cmd in no_timestamp_cmds:
                if cmd:
                    commands.append((file_mtime, cmd))

        return commands

    def _parse_bash_history(
        self, file_path: Path, target_date: date
    ) -> List[Tuple[datetime, str]]:
        commands = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            commands.append((datetime.combine(target_date, datetime.min.time()), line))

        return commands

    def _parse_fish_history(
        self, file_path: Path, target_date: date
    ) -> List[Tuple[datetime, str]]:
        commands = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        current_cmd = ""
        current_ts = None

        for line in content.splitlines():
            if line.startswith("- cmd: "):
                if current_cmd and current_ts and current_ts.date() == target_date:
                    commands.append((current_ts, current_cmd))
                current_cmd = line[7:].strip().strip("'").strip('"')
            elif line.startswith("  when: "):
                try:
                    ts = int(line[8:].strip())
                    current_ts = datetime.fromtimestamp(ts)
                except (ValueError, OSError):
                    current_ts = None
            elif line == "- end":
                if current_cmd:
                    if current_ts and current_ts.date() == target_date:
                        commands.append((current_ts, current_cmd))
                    elif current_ts is None:
                        commands.append((datetime.combine(target_date, datetime.min.time()), current_cmd))
                current_cmd = ""
                current_ts = None

        if current_cmd and current_ts and current_ts.date() == target_date:
            commands.append((current_ts, current_cmd))

        return commands

    def _parse_powershell_history(
        self, file_path: Path, target_date: date
    ) -> List[Tuple[datetime, str]]:
        commands = []

        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            return []

        file_mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        estimated_lines = content.count("\n")
        if estimated_lines > 0:
            avg_interval = max(
                (file_mtime - file_mtime.replace(hour=8, minute=0, second=0)).total_seconds() / max(estimated_lines, 1),
                1,
            )

        current_time = file_mtime.replace(hour=0, minute=0, second=0, microsecond=0)

        for line in content.splitlines():
            line = line.strip()
            if not line:
                continue
            current_time += timedelta(seconds=avg_interval)
            if current_time.date() == target_date:
                commands.append((current_time, line))

        return commands

    def _build_session(
        self, commands: List[Tuple[datetime, str]], shell_type: str, target_date: date
    ) -> Optional[SessionData]:
        if not commands:
            return None

        commands.sort(key=lambda x: x[0])

        messages = []
        for ts, cmd in commands:
            messages.append(Message(
                role="user",
                content=cmd,
                timestamp=ts,
            ))

        start_time = commands[0][0]
        end_time = commands[-1][0]

        unique_cmds = len(set(cmd for _, cmd in commands))
        summary = f"执行 {len(commands)} 条命令（{unique_cmds} 条去重），Shell: {shell_type}"

        title_cmds = [cmd for _, cmd in commands[:5]]
        title = f"Shell ({shell_type}): {'; '.join(title_cmds[:3])}"
        if len(title_cmds) > 3:
            title += " ..."

        session_id = hashlib.md5(
            f"shell_history_{shell_type}_{target_date.isoformat()}".encode()
        ).hexdigest()[:16]

        return SessionData(
            session_id=session_id,
            source=self.name,
            project_path=None,
            start_time=start_time,
            end_time=end_time,
            title=title,
            summary=summary,
            messages=messages,
            files_modified=[],
            tokens_input=0,
            tokens_output=0,
        )
