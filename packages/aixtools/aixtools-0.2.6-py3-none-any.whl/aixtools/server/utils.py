"""
FastMCP server utilities for handling user context and threading.
"""

import asyncio
from functools import wraps

from fastmcp import Context
from fastmcp.server import dependencies

from ..context import DEFAULT_SESSION_ID, DEFAULT_USER_ID, session_id_var, user_id_var


def get_session_id_tuple(ctx: Context | None = None) -> tuple[str, str]:
    """
    Get the user and session IDs from the user session.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    Returns: Tuple of (user_id, session_id).
    """
    user_id = get_user_id_from_request(ctx)
    user_id = user_id or user_id_var.get(DEFAULT_USER_ID)
    session_id = get_session_id_from_request(ctx)
    session_id = session_id or session_id_var.get(DEFAULT_SESSION_ID)
    return user_id, session_id


def get_session_id_from_request(ctx: Context | None = None) -> str | None:
    """
    Get the session ID from the HTTP request headers.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    """
    try:
        return (ctx or dependencies).get_http_request().headers.get("session-id")
    except (ValueError, RuntimeError):
        return None


def get_user_id_from_request(ctx: Context | None = None) -> str | None:
    """
    Get the user ID from the HTTP request headers.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    The user_id is always returned as lowercase.

    Returns:
        str | None: The lowercase user ID, or None if not found or an error occurs.
    """
    try:
        user_id = (ctx or dependencies).get_http_request().headers.get("user-id")
        return user_id.lower() if user_id else None
    except (ValueError, RuntimeError, AttributeError):
        return None


def get_session_id_str(ctx: Context | None = None) -> str:
    """
    Combined session ID for the current user and session.
    If `ctx` is None, the current FastMCP request HTTP headers are used.
    """
    user_id, session_id = get_session_id_tuple(ctx)
    return f"{user_id}:{session_id}"


def run_in_thread(func):
    """decorator to run blocking function with `asyncio.to_thread`"""

    @wraps(func)
    async def wrapper(*args, **kwargs):
        return await asyncio.to_thread(func, *args, **kwargs)

    return wrapper
