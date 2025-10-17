"""
This module defines global context variables for request-specific information
that can be used for logging, tracing, and other purposes across applications
that use aixtools.
"""

from contextvars import ContextVar

# Define context variables with default values.
# These can be populated by middleware or where they are initialized
session_id_var: ContextVar[str | None] = ContextVar("session_id", default=None)
user_id_var: ContextVar[str | None] = ContextVar("user_id", default=None)

DEFAULT_USER_ID = "default_user"
DEFAULT_SESSION_ID = "default_session"

SessionIdTuple = tuple[str, str]
