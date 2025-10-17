"""
Session management for aiohttp clients.

This module provides a global session manager for reusing HTTP connections
across the application.
"""

import aiohttp
import warnings
import logging

# 禁用所有 aiohttp 相关警告
warnings.filterwarnings("ignore", category=ResourceWarning)
# 禁用 aiohttp 内部日志
logging.getLogger("aiohttp").setLevel(logging.ERROR)


class SessionManager:
    """全局会话管理器"""

    def __init__(self):
        self._session = None

    async def get_session(self) -> aiohttp.ClientSession:
        """Get or create an aiohttp ClientSession."""
        if self._session is None:
            self._session = aiohttp.ClientSession()
        return self._session

    async def close(self):
        """Close the session if it exists."""
        if self._session is not None:
            await self._session.close()
            self._session = None


# 创建全局会话管理器
session_manager = SessionManager()
