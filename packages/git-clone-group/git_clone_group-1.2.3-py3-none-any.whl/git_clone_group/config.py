"""
Configuration classes and data structures for git_clone_group.

This module contains all configuration-related data classes and settings.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, List


@dataclass
class GitLabConfig:
    """Configuration class for GitLab connection and clone operations."""

    gitlab_addr: str
    token: str
    dest_dir: Path
    branch: Optional[str] = None  # 指定要克隆或拉取的分支
    max_retries: int = 3
    timeout: int = 30
    max_concurrent_tasks: int = 5


@dataclass
class ProjectStats:
    """项目统计信息"""

    cloned: int = 0
    updated: int = 0
    empty: int = 0
    failed: int = 0
    empty_repos: Optional[List[str]] = None  # 存储空仓库列表

    def __post_init__(self):
        """Initialize empty_repos list if not provided."""
        if self.empty_repos is None:
            self.empty_repos = []
