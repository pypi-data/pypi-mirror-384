"""
Custom exceptions for git_clone_group.

This module defines all custom exceptions used throughout the application.
"""


class GitLabError(Exception):
    """Base exception for GitLab operations."""

    pass


class GitLabPermissionError(GitLabError):
    """Permission denied error for GitLab operations."""

    pass
