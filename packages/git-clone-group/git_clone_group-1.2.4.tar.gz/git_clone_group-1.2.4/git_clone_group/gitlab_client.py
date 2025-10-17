"""
GitLab API client for managing GitLab operations.

This module provides a client class for interacting with GitLab APIs
including fetching groups, projects, and managing authentication.
"""

from typing import List, Dict

from .config import GitLabConfig, ProjectStats
from .exceptions import GitLabError, GitLabPermissionError
from .session import session_manager


class GitLabClient:
    """GitLab API客户端类，负责与GitLab API交互"""

    def __init__(self, config: GitLabConfig):
        self.config = config
        self.session = None
        self.failed_projects = []

    async def __aenter__(self):
        self.session = await session_manager.get_session()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # 不在这里关闭会话，由全局管理器管理
        pass

    async def get_group_id_by_name(self, group_name: str) -> int:
        """Get group ID by group name/path."""
        # 首先尝试直接通过路径获取组信息
        url = f"https://{self.config.gitlab_addr}/api/v4/groups/{group_name}?private_token={self.config.token}"
        try:
            async with self.session.get(url) as response:
                if response.status == 200:
                    group_data = await response.json()
                    return group_data["id"]
        except Exception:
            pass

        # 如果直接获取失败，则搜索组
        search_url = f"https://{self.config.gitlab_addr}/api/v4/groups?search={group_name}&private_token={self.config.token}"
        async with self.session.get(search_url) as response:
            response.raise_for_status()
            groups = await response.json()

            if not groups:
                raise GitLabError(f"Group '{group_name}' not found")

            # 优先查找完全匹配的组名或路径
            for group in groups:
                if (
                    group["name"] == group_name
                    or group["path"] == group_name
                    or group["full_path"] == group_name
                ):
                    return group["id"]

            # 如果没有完全匹配，返回第一个搜索结果
            if len(groups) == 1:
                return groups[0]["id"]

            # 如果有多个结果，让用户选择
            print(f"\nFound {len(groups)} groups matching '{group_name}':")
            for i, group in enumerate(groups, 1):
                print(f"{i}. {group['full_path']} (ID: {group['id']})")

            while True:
                try:
                    choice = input(f"\nSelect a group (1-{len(groups)}): ").strip()
                    index = int(choice) - 1
                    if 0 <= index < len(groups):
                        return groups[index]["id"]
                    else:
                        print(f"Please enter a number between 1 and {len(groups)}")
                except ValueError:
                    print("Please enter a valid number")
                except KeyboardInterrupt:
                    raise GitLabError("Operation cancelled by user")

    async def get_projects(self, group_id: int, page: int = 1) -> List[Dict]:
        """Get projects for a given group ID and page."""
        url = self._gen_next_url(group_id, page)
        async with self.session.get(url) as response:
            response.raise_for_status()
            return await response.json()

    def _gen_next_url(self, target_id: int, page: int = 1) -> str:
        """Generate URL for getting group projects."""
        return f"https://{self.config.gitlab_addr}/api/v4/groups/{target_id}/projects?page={page}&private_token={self.config.token}"

    def _gen_subgroups_url(self, target_id: int) -> str:
        """Generate URL for getting subgroups."""
        return f"https://{self.config.gitlab_addr}/api/v4/groups/{target_id}/subgroups?private_token={self.config.token}"

    def _gen_global_url(self) -> str:
        """Generate URL for getting all projects."""
        return f"https://{self.config.gitlab_addr}/api/v4/projects?private_token={self.config.token}"

    def _gen_groups_url(self, page: int = 1, per_page: int = 100) -> str:
        """Generate URL for listing all accessible groups."""
        return f"https://{self.config.gitlab_addr}/api/v4/groups?private_token={self.config.token}&page={page}&per_page={per_page}"

    async def get_sub_groups(self, parent_id: int) -> List[int]:
        """Get list of subgroup IDs for a parent group."""
        url = self._gen_subgroups_url(parent_id)
        async with self.session.get(url) as response:
            response.raise_for_status()
            groups = await response.json()
            return [group["id"] for group in groups]

    async def have_next_projects(self, group_id: int) -> bool:
        """Check if group has any projects."""
        url = self._gen_next_url(group_id)
        async with self.session.get(url) as response:
            response.raise_for_status()
            projects = await response.json()
            return bool(projects)

    async def retry_failed_projects(self, stats: ProjectStats):
        """重试失败的项目"""
        from .git_operations import (
            clone_or_pull_project,
        )  # Local import to avoid circular dependency

        if not self.failed_projects:
            return

        retry_projects = self.failed_projects.copy()
        self.failed_projects.clear()

        print(f"Retrying {len(retry_projects)} failed projects...")
        for project in retry_projects:
            try:
                await clone_or_pull_project(self.config, project, stats)
            except GitLabPermissionError as e:
                print(f"Permission denied, skipping: {e}")
                stats.failed += 1
            except Exception as e:
                print(f"Retry failed: {e}")
                stats.failed += 1
                self.failed_projects.append(project)

    async def get_all_groups(self) -> List[Dict]:
        """List all accessible groups for current token (paginated)."""
        groups: List[Dict] = []
        page = 1
        per_page = 100
        while True:
            url = self._gen_groups_url(page=page, per_page=per_page)
            async with self.session.get(url) as response:
                response.raise_for_status()
                batch = await response.json()
                if not batch:
                    break
                groups.extend(batch)
                if len(batch) < per_page:
                    break
                page += 1
        return groups
