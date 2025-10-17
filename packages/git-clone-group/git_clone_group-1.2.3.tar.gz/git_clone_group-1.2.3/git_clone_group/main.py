"""
Main orchestrator module for git_clone_group.

This module contains the main business logic for downloading code from GitLab
groups and their subgroups, coordinating between different components.
"""

import asyncio

from .config import GitLabConfig, ProjectStats
from .gitlab_client import GitLabClient
from .group_processor import process_group, cal_next_sub_group_ids, get_group_stats
from .session import session_manager
from .exceptions import GitLabError


async def download_code(config: GitLabConfig, parent_id: int) -> None:
    """Download code for a group and all its subgroups with error handling."""
    try:
        print("Scanning groups and projects...")
        stats = ProjectStats()

        async with GitLabClient(config) as client:
            group_ids = await cal_next_sub_group_ids(config, parent_id)

            if await client.have_next_projects(parent_id):
                group_ids.add(parent_id)

            # 获取并显示初始统计信息
            initial_stats = await get_group_stats(config, group_ids)
            print(f"\nSummary:")
            print(f"- Total groups to process: {initial_stats['total_groups']}")
            print(
                f"- Total projects to clone/update: {initial_stats['total_projects']}"
            )

            # 请求用户确认（在非交互环境中默认取消）
            try:
                response = input("\nDo you want to proceed? [y/N]: ")
            except EOFError:
                response = "n"
            if response.lower() != "y":
                print("Operation cancelled by user")
                return

            print("\nStarting clone/pull operations...")
            sem = asyncio.Semaphore(config.max_concurrent_tasks)

            async def bounded_process(group_id):
                async with sem:
                    await process_group(config, group_id, stats)

            tasks = [bounded_process(group_id) for group_id in group_ids]
            await asyncio.gather(*tasks, return_exceptions=True)

            # 显示最终统计信息
            print("\nOperation completed!")
            print("Summary:")
            print(f"- Repositories cloned: {stats.cloned}")
            print(f"- Repositories updated: {stats.updated}")
            print(f"- Empty repositories: {stats.empty}")
            print(f"- Failed operations: {stats.failed}")
            print(
                f"- Total repositories processed: {stats.cloned + stats.updated + stats.empty}"
            )

            if stats.empty_repos:
                print("\nEmpty repositories:")
                for repo in sorted(stats.empty_repos):
                    print(f"  - {repo}")

    except Exception as e:
        print(f"Error in download_code: {e}")
    finally:
        # 确保会话被正确关闭
        await session_manager.close()


async def download_code_by_name(config: GitLabConfig, group_name: str) -> None:
    """Download code for a group by name and all its subgroups."""
    try:
        print(f"Looking up group: {group_name}...")

        async with GitLabClient(config) as client:
            # 根据组名获取组ID
            group_id = await client.get_group_id_by_name(group_name)
            print(f"Found group '{group_name}' with ID: {group_id}")

        # 使用现有的 download_code 函数
        await download_code(config, group_id)

    except GitLabError as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Error in download_code_by_name: {e}")


async def download_all_groups(config: GitLabConfig, assume_yes: bool = False) -> None:
    """When no group is specified, list all accessible groups with project counts and prompt to proceed.

    Flow:
    - List all accessible groups
    - For each group, compute target group IDs (including subgroups with projects)
    - Summarize per top-level group: number of effective groups and total projects
    - Print a concise report
    - Ask for confirmation (unless assume_yes)
    - If confirmed, process all groups concurrently
    """
    try:
        print("Scanning accessible groups...")
        async with GitLabClient(config) as client:
            groups = await client.get_all_groups()

        if not groups:
            print("No accessible groups found for this token.")
            return

        # Build per-group stats
        per_group_info = (
            []
        )  # [(group_id, full_path, effective_group_ids, total_projects)]
        grand_total_projects = 0
        grand_total_effective_groups = 0

        for g in groups:
            gid = g["id"]
            full_path = g.get("full_path") or g.get("path") or g.get("name")
            try:
                effective_ids = await cal_next_sub_group_ids(config, gid)
                # Include self if it has projects
                async with GitLabClient(config) as client:
                    if await client.have_next_projects(gid):
                        effective_ids.add(gid)

                stats = await get_group_stats(config, effective_ids)
                total_projects = stats["total_projects"]
            except Exception as e:
                print(f"Failed to analyze group {full_path} (ID {gid}): {e}")
                effective_ids = set()
                total_projects = 0

            per_group_info.append((gid, full_path, effective_ids, total_projects))
            grand_total_projects += total_projects
            grand_total_effective_groups += len(effective_ids)

        # Print summary
        print("\nAccessible groups summary:")
        for idx, (gid, full_path, eff_ids, total_projects) in enumerate(
            per_group_info, 1
        ):
            print(
                f"{idx}. {full_path} (ID: {gid}) -> groups to process: {len(eff_ids)}, projects: {total_projects}"
            )
        print("\nOverall:")
        print(f"- Top-level groups: {len(per_group_info)}")
        print(
            f"- Effective groups to process (incl. subgroups with projects): {grand_total_effective_groups}"
        )
        print(f"- Total projects: {grand_total_projects}")

        # Confirm
        proceed = assume_yes
        if not proceed:
            try:
                resp = (
                    input("\nProceed to clone/pull ALL listed groups? [y/N]: ")
                    .strip()
                    .lower()
                )
            except EOFError:
                resp = "n"
            proceed = resp == "y"
        if not proceed:
            print("Operation cancelled by user")
            return

        # Process all effective groups across all top-level groups
        # De-duplicate group IDs across top-level groups
        all_effective_group_ids = set()
        for _, _, eff_ids, _ in per_group_info:
            all_effective_group_ids.update(eff_ids)

        if not all_effective_group_ids:
            print("Nothing to process.")
            return

        print("\nStarting clone/pull operations across all groups...")
        stats = ProjectStats()
        sem = asyncio.Semaphore(config.max_concurrent_tasks)

        async def bounded_process(group_id):
            async with sem:
                await process_group(config, group_id, stats)

        tasks = [bounded_process(gid) for gid in all_effective_group_ids]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Final summary
        print("\nOperation completed!")
        print("Summary:")
        print(f"- Repositories cloned: {stats.cloned}")
        print(f"- Repositories updated: {stats.updated}")
        print(f"- Empty repositories: {stats.empty}")
        print(f"- Failed operations: {stats.failed}")
        print(
            f"- Total repositories processed: {stats.cloned + stats.updated + stats.empty}"
        )

        if stats.empty_repos:
            print("\nEmpty repositories:")
            for repo in sorted(stats.empty_repos):
                print(f"  - {repo}")

    except Exception as e:
        print(f"Error in download_all_groups: {e}")
    finally:
        await session_manager.close()
