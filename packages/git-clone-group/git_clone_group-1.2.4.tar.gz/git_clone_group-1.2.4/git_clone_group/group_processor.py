"""
Group processing operations for GitLab groups and their projects.

This module handles the processing of GitLab groups, including discovering
subgroups, processing projects within groups, and calculating statistics.
"""

import asyncio
from typing import Set, Dict
from tqdm import tqdm

from .config import GitLabConfig, ProjectStats
from .gitlab_client import GitLabClient
from .git_operations import clone_or_pull_project
from .exceptions import GitLabPermissionError


async def process_group(
    config: GitLabConfig, group_id: int, stats: ProjectStats
) -> None:
    """Process a single group asynchronously with error handling."""
    async with GitLabClient(config) as client:
        page = 1
        while True:
            try:
                projects = await client.get_projects(group_id, page)
                if not projects:
                    break

                sem = asyncio.Semaphore(config.max_concurrent_tasks)

                async def bounded_clone(project):
                    async with sem:
                        try:
                            await clone_or_pull_project(config, project, stats)
                            return True
                        except Exception as e:
                            print(
                                f"Error processing {project['path_with_namespace']}: {e}"
                            )
                            stats.failed += 1
                            # 记录失败项目，便于之后重试
                            client.failed_projects.append(project)
                            return False

                tasks = []
                for project in projects:
                    task = asyncio.create_task(bounded_clone(project))
                    tasks.append(task)

                with tqdm(
                    total=len(tasks), desc=f"Group {group_id} - Page {page}"
                ) as pbar:
                    for task in tasks:
                        try:
                            success = await task
                            # 已在 bounded_clone 内部记录失败
                        except Exception as e:
                            print(f"Unexpected error: {e}")
                            # 此处无法获取具体 project 对象，跳过添加
                            stats.failed += 1
                        finally:
                            pbar.update(1)

                # 重试失败的项目
                await client.retry_failed_projects(stats)

                page += 1
            except Exception as e:
                print(f"Error processing group {group_id} page {page}: {e}")
                break


async def cal_next_sub_group_ids(config: GitLabConfig, parent_id: int) -> Set[int]:
    """Calculate all subgroup IDs recursively."""
    parent_list = set()
    async with GitLabClient(config) as client:
        sub_ids = await client.get_sub_groups(parent_id)
        has_projects = await client.have_next_projects(parent_id)

        if sub_ids:
            if has_projects:
                parent_list.add(parent_id)
            for sub_id in sub_ids:
                parent_list.update(await cal_next_sub_group_ids(config, sub_id))
        elif has_projects:
            parent_list.add(parent_id)

    return parent_list


async def get_group_stats(config: GitLabConfig, group_ids: Set[int]) -> Dict[str, int]:
    """Get statistics for all groups"""
    total_projects = 0
    async with GitLabClient(config) as client:
        for group_id in group_ids:
            page = 1
            while True:
                projects = await client.get_projects(group_id, page)
                if not projects:
                    break
                total_projects += len(projects)
                page += 1

    return {"total_groups": len(group_ids), "total_projects": total_projects}
