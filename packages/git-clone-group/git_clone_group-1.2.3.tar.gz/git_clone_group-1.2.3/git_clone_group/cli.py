"""
Command Line Interface for git_clone_group.

This module provides the command-line interface for the git_clone_group tool,
handling argument parsing and coordinating with the main application logic.
"""

import argparse
import asyncio
from pathlib import Path

from .config import GitLabConfig
from .main import download_code, download_code_by_name


def cli() -> None:
    """Command line interface with improved argument handling."""
    parser = argparse.ArgumentParser(
        description="Clone all projects from a GitLab group and its subgroups",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Clone by group ID
  gcg -g gitlab.com -t token -i 123 -d ./repos
  
  # Clone by group name/path
  gcg -g gitlab.com -t token -n my-group -d ./repos
  
  # Clone specific branch
  gcg -g gitlab.com -t token -n my-group -b develop
        """,
    )

    parser.add_argument(
        "--gitlab-addr",
        "-g",
        required=True,
        help="GitLab server address (e.g. gitlab.com)",
    )
    parser.add_argument(
        "--token",
        "-t",
        required=True,
        help="GitLab private token (create from Settings > Access Tokens)",
    )

    # 创建互斥组，只能选择其中一个；若都不指定，则进入“全部组”的模式
    group_spec = parser.add_mutually_exclusive_group(required=False)
    group_spec.add_argument(
        "--group-id",
        "-i",
        type=int,
        help="GitLab group ID to clone (found in group page URL or settings)",
    )
    group_spec.add_argument(
        "--group-name",
        "-n",
        help="GitLab group name/path to clone (e.g. 'my-group' or 'namespace/my-group')",
    )
    parser.add_argument(
        "--dest-dir",
        "-d",
        default=".",
        help="Destination directory for cloned repositories (default: current directory)",
    )
    parser.add_argument(
        "--branch",
        "-b",
        help="Specify a branch to clone/pull (default: repository's default branch)",
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Assume 'yes' to confirmation prompts (useful for non-interactive runs)",
    )

    args = parser.parse_args()

    config = GitLabConfig(
        gitlab_addr=args.gitlab_addr,
        token=args.token,
        dest_dir=Path(args.dest_dir),
        branch=args.branch,
        max_retries=3,
        timeout=30,
        max_concurrent_tasks=5,
    )

    try:
        if args.group_id:
            asyncio.run(download_code(config, args.group_id))
        elif args.group_name:
            asyncio.run(download_code_by_name(config, args.group_name))
        else:
            # 未指定 group-id 或 group-name，执行全部可访问组的统计并确认
            from .main import download_all_groups

            asyncio.run(download_all_groups(config, assume_yes=args.yes))
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
    except Exception as e:
        print(f"Fatal error: {e}")
    finally:
        # 确保清理所有资源
        asyncio.new_event_loop()


if __name__ == "__main__":
    cli()
