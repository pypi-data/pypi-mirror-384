"""
Git operations for cloning and pulling repositories.

This module handles all Git-related operations including cloning repositories,
pulling updates, and managing different branches.
"""

import asyncio
from pathlib import Path
from typing import Dict, List

from .config import GitLabConfig, ProjectStats
from .exceptions import GitLabPermissionError


async def clone_or_pull_project(
    config: GitLabConfig, project: Dict, stats: ProjectStats
) -> None:
    """Clone or pull a single project asynchronously."""
    project_url = project["ssh_url_to_repo"]
    project_path = project["path_with_namespace"]
    full_path = config.dest_dir / project_path

    async def run_git_command(command: List[str]) -> str:
        """Execute a git command asynchronously."""
        try:
            proc = await asyncio.create_subprocess_exec(
                *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            stderr_text = stderr.decode()
            stdout_text = stdout.decode().strip()

            if proc.returncode != 0:
                if "Permission denied" in stderr_text:
                    raise GitLabPermissionError(f"Permission denied for {project_path}")
                raise RuntimeError(f"Git command failed: {stderr_text}")
            return stdout_text
        except GitLabPermissionError:
            raise
        except Exception as e:
            raise RuntimeError(f"Git operation failed: {str(e)}")

    async def safe_pull(path: Path) -> None:
        """Safe pull operation with fetch first"""
        try:
            # First fetch to update remote refs
            await run_git_command(["git", "-C", str(path), "fetch", "origin"])

            # 使用配置中指定的分支或项目默认分支
            target_branch = config.branch or project.get("default_branch", "master")

            try:
                # 检查本地分支是否存在
                current_branch = await run_git_command(
                    ["git", "-C", str(path), "rev-parse", "--abbrev-ref", "HEAD"]
                )

                # 如果当前分支不是目标分支，切换到目标分支
                if current_branch != target_branch:
                    try:
                        # 尝试切换到目标分支
                        await run_git_command(
                            ["git", "-C", str(path), "checkout", target_branch]
                        )
                    except RuntimeError:
                        # 如果分支不存在，创建新分支并跟踪远程分支
                        await run_git_command(
                            [
                                "git",
                                "-C",
                                str(path),
                                "checkout",
                                "-b",
                                target_branch,
                                f"origin/{target_branch}",
                            ]
                        )
            except RuntimeError:
                # 如果获取分支失败，检查是否为空仓库
                remote_branches = await run_git_command(
                    ["git", "-C", str(path), "branch", "-r"]
                )
                if not remote_branches:
                    stats.empty += 1
                    stats.empty_repos.append(project_path)
                    return

                # 尝试检出指定分支
                try:
                    await run_git_command(
                        [
                            "git",
                            "-C",
                            str(path),
                            "checkout",
                            "-b",
                            target_branch,
                            f"origin/{target_branch}",
                        ]
                    )
                except RuntimeError:
                    print(
                        f"Failed to checkout branch {target_branch} for {project_path}, skipping pull"
                    )
                    return

            # Pull using specific branch
            await run_git_command(
                ["git", "-C", str(path), "pull", "origin", target_branch]
            )
            stats.updated += 1
        except Exception as e:
            raise RuntimeError(f"Pull failed: {str(e)}")

    async def init_repo(path: Path) -> None:
        """Initialize new repository"""
        try:
            clone_cmd = ["git", "clone", project_url, str(path)]
            if config.branch:
                clone_cmd.extend(["-b", config.branch])
            await run_git_command(clone_cmd)

            if not path.exists():
                raise RuntimeError("Clone completed but directory not found")

            # 检查是否为空仓库
            try:
                await run_git_command(["git", "-C", str(path), "rev-parse", "HEAD"])
                stats.cloned += 1
            except RuntimeError:
                stats.empty += 1
                stats.empty_repos.append(project_path)
        except Exception as e:
            raise RuntimeError(f"Clone failed: {str(e)}")

    # Main operation with retries
    for attempt in range(config.max_retries):
        try:
            if full_path.exists():
                await safe_pull(full_path)
            else:
                await init_repo(full_path)
            return
        except GitLabPermissionError:
            raise
        except Exception as e:
            if attempt == config.max_retries - 1:
                print(
                    f"Failed after {config.max_retries} attempts for {project_path}: {e}"
                )
                stats.failed += 1
                raise
            await asyncio.sleep(1 * (attempt + 1))
