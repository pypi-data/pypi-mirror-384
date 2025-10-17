"""MCP server utilities with caching and robust error handling."""

import asyncio
import logging
from contextlib import asynccontextmanager
from datetime import timedelta
from typing import Any, AsyncGenerator

import anyio
import httpx
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from cachebox import TTLCache
from fastmcp.client.logging import LogMessage
from mcp import types as mcp_types
from mcp.client import streamable_http
from mcp.shared.exceptions import McpError
from mcp.shared.message import SessionMessage
from pydantic_ai import RunContext, exceptions
from pydantic_ai.mcp import MCPServerStdio, MCPServerStreamableHTTP, ToolResult
from pydantic_ai.toolsets.abstract import ToolsetTool

from aixtools.context import SessionIdTuple
from aixtools.logging.logging_config import get_logger

MCP_TOOL_CACHE_TTL = 300  # 5 minutes
DEFAULT_MCP_CONNECTION_TIMEOUT = 30
DEFAULT_MCP_READ_TIMEOUT = float(60 * 5)  # 5 minutes
CACHE_KEY = "TOOL_LIST"

logger = get_logger(__name__)


# Default log_handler for MCP clients
LOGGING_LEVEL_MAP = logging.getLevelNamesMapping()


async def default_mcp_log_handler(message: LogMessage):
    """
    Handles incoming logs from the MCP server and forwards them
    to the standard Python logging system.
    """
    msg = message.data.get("msg")
    extra = message.data.get("extra")

    # Convert the MCP log level to a Python log level
    level = LOGGING_LEVEL_MAP.get(message.level.upper(), logging.INFO)

    # Log the message using the standard logging library
    logger.log(level, msg, extra=extra)


def get_mcp_client(
    url: str | None = None,
    command: str | None = None,
    args: list[str] = None,
    log_handler: callable = default_mcp_log_handler,  # type: ignore
) -> MCPServerStreamableHTTP | MCPServerStdio:
    """
    Create an MCP client instance based on the provided URL or command.
    By providing a log_handler, incoming logs from the MCP server can be shown, which improves debugging.

    Args:
        url (str | None): The URL of the MCP server.
        command (str | None): The command to start a local MCP server (STDIO MCP).
        args (list[str] | None): Additional arguments for the command (STDIO MCP).
    """
    if args is None:
        args = []
    if url:
        return MCPServerStreamableHTTP(url="http://127.0.0.1:8089/mcp/", log_handler=log_handler)
    if command:
        return MCPServerStdio(command=command, args=args, log_handler=log_handler)
    raise ValueError("Either url or command must be provided to create MCP client.")


def get_mcp_headers(session_id_tuple: SessionIdTuple) -> dict[str, str] | None:
    """
    Generate headers for MCP server requests.

    This function creates a dictionary of headers to be used in requests to
    the MCP servers. If a `user_id` or `session_id` is provided, they are
    included in the headers.

    Args:
        session_id_tuple (SessionIdTuple): user_id and session_id tuple
    Returns:
        dict[str, str] | None: A dictionary of headers for MCP server requests,
                               or None if neither user_id nor session_id is
                               provided. When None is returned, default headers
                               from the client or transport will be used.
    """
    headers = None
    user_id, session_id = session_id_tuple
    if session_id or user_id:
        headers = {}
        if session_id:
            headers["session-id"] = session_id
        if user_id:
            headers["user-id"] = user_id
    return headers


def get_configured_mcp_servers(
    session_id_tuple: SessionIdTuple, mcp_urls: list[str], timeout: int = DEFAULT_MCP_CONNECTION_TIMEOUT
):
    """
    Retrieve the configured MCP server instances with optional caching.

    Context values `user_id` and `session_id` are included in the headers for each server request.

    Each server is wrapped in a try-except block to isolate them from each other.
    If one server fails, it won't affect the others.

    Args:
        session_id_tuple (SessionIdTuple): A tuple containing (user_id, session_id).
        mcp_urls: (list[str], optional): A list of MCP server URLs to use.
        timeout (int, optional): Timeout in seconds for MCP server connections. Defaults to 30 seconds.
    Returns:
        list[MCPServerStreamableHTTP]: A list of configured MCP server instances. If
                              neither user_id nor session_id is provided, the
                              server instances will use default headers defined
                              by the underlying HTTP implementation.
    """
    headers = get_mcp_headers(session_id_tuple)

    return [CachedMCPServerStreamableHTTP(url=url, headers=headers, timeout=timeout) for url in mcp_urls]


class CachedMCPServerStreamableHTTP(MCPServerStreamableHTTP):
    """StreamableHTTP MCP server with cachebox-based TTL caching and robust error handling.

    This class addresses the cancellation propagation issue by:
    1. Using complete task isolation to prevent CancelledError propagation
    2. Implementing comprehensive error handling for all MCP operations
    3. Using fallback mechanisms when servers become unavailable
    4. Overriding pydantic_ai methods to fix variable scoping bug
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._tools_cache = TTLCache(maxsize=1, ttl=MCP_TOOL_CACHE_TTL)
        self._tools_list = None
        self._isolation_lock = asyncio.Lock()  # Lock for critical operations

    async def _run_direct_or_isolated(self, func, fallback, timeout: float | None):
        """Run a coroutine in complete isolation to prevent cancellation propagation.

        Args:
            func: Function that returns a coroutine to run
            fallback: Function that takes an exception and returns a fallback value
            timeout: Timeout in seconds. If None, then direct run is performed

        Returns:
            The result of the coroutine on success, or fallback value on any exception
        """
        try:
            if timeout is None:
                return await func()

            task = asyncio.create_task(func())

            # Use asyncio.wait to prevent cancellation propagation
            done, pending = await asyncio.wait([task], timeout=timeout)

            if pending:
                # Cancel pending tasks safely
                for t in pending:
                    t.cancel()
                    try:
                        await t
                    except (asyncio.CancelledError, Exception):  # pylint: disable=broad-except
                        pass
                raise TimeoutError(f"Task timed out after {timeout} seconds")

            # Get result from completed task
            completed_task = done.pop()
            if exc := completed_task.exception():
                raise exc
            return completed_task.result()

        except exceptions.ModelRetry as exc:
            logger.warning("MCP %s: %s ModelRetry: %s", self.url, func.__name__, exc)
            raise
        except TimeoutError as exc:
            logger.warning("MCP %s: %s timed out: %s", self.url, func.__name__, exc)
            return fallback(exc)
        except asyncio.CancelledError as exc:
            logger.warning("MCP %s: %s was cancelled", self.url, func.__name__)
            return fallback(exc)
        except anyio.ClosedResourceError as exc:
            logger.warning("MCP %s: %s closed resource.", self.url, func.__name__)
            return fallback(exc)
        except Exception as exc:  # pylint: disable=broad-except
            if str(exc) == "Attempted to exit cancel scope in a different task than it was entered in":
                logger.warning("MCP %s: %s enter/exit cancel scope task mismatch.", self.url, func.__name__)
            else:
                logger.warning("MCP %s: %s exception %s: %s", self.url, func.__name__, type(exc), exc)
            return fallback(exc)

    @property
    def _transport_client(self):
        """Override base transport client with wrapper logging and suppressing exceptions"""
        return patched_streamablehttp_client

    @asynccontextmanager
    async def client_streams(self):
        """Override base client_streams with wrapper logging and suppressing exceptions"""
        try:
            async with super().client_streams() as streams:  # pylint: disable=contextmanager-generator-missing-cleanup
                try:
                    yield streams
                except Exception as exc:  # pylint: disable=broad-except
                    logger.error("MCP %s: client_streams; %s: %s", self.url, type(exc).__name__, exc)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("MCP %s: client_streams: %s: %s", self.url, type(exc).__name__, exc)

    async def __aenter__(self):
        """Enter the context of the cached MCP server with complete cancellation isolation."""
        async with self._isolation_lock:

            async def direct_init():
                return await super(CachedMCPServerStreamableHTTP, self).__aenter__()  # pylint: disable=super-with-arguments

            def fallback(_exc):
                self._client = None
                return self

            return await self._run_direct_or_isolated(direct_init, fallback, timeout=None)

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Exit the context of the cached MCP server with complete cancellation isolation."""
        async with self._isolation_lock:
            # If we're being cancelled, just clean up
            if exc_type is asyncio.CancelledError:
                logger.warning("MCP %s: __aexit__ called with cancellation - cleaning up", self.url)
                self._client = None
                return True

            # If client is already None, skip cleanup
            if not self._client:
                logger.warning("MCP %s: is uninitialized -> skipping cleanup", self.url)
                return True

            async def direct_cleanup():
                return await super(CachedMCPServerStreamableHTTP, self).__aexit__(exc_type, exc_val, exc_tb)  # pylint: disable=super-with-arguments

            def fallback(_exc):
                self._client = None
                return True  # Suppress exceptions to prevent propagation

            return await self._run_direct_or_isolated(direct_cleanup, fallback, timeout=None)

    async def list_tools(self) -> list[mcp_types.Tool]:
        """Override to fix variable scoping bug and add caching with cancellation isolation."""
        # If client is not initialized, return empty list
        if not self._client:
            logger.warning("MCP %s: is uninitialized -> no tools", self.url)
            return []

        # First, check if we have a valid cached result
        if CACHE_KEY in self._tools_cache:
            logger.info("Using cached tools for %s", self.url)
            return self._tools_cache[CACHE_KEY]

        # Create isolated task to prevent cancellation propagation
        async def isolated_list_tools():
            """Isolated list_tools with variable scoping bug fix."""
            result = None  # Initialize to prevent UnboundLocalError
            async with self:  # Ensure server is running
                result = await self._client.list_tools()
            if result:
                self._tools_list = result.tools or []
                self._tools_cache[CACHE_KEY] = self._tools_list
                logger.info("MCP %s: list_tools returned %d tools", self.url, len(self._tools_list))
            else:
                logger.warning("MCP %s: list_tools returned no result", self.url)
            return self._tools_list or []

        def fallback(_exc):
            return self._tools_list or []

        return await self._run_direct_or_isolated(isolated_list_tools, fallback, timeout=5.0)

    async def call_tool(
        self,
        name: str,
        tool_args: dict[str, Any],
        ctx: RunContext[Any],
        tool: ToolsetTool[Any],
    ) -> ToolResult:
        """Call tool with complete isolation from cancellation using patched pydantic_ai."""
        logger.info("MCP %s: call_tool '%s' started.", self.url, name)

        # Early returns for uninitialized servers
        if not self._client:
            logger.warning("MCP %s: is uninitialized -> cannot call tool", self.url)
            return f"There was an error with calling tool '{name}': MCP connection is uninitialized."

        # Create isolated task to prevent cancellation propagation
        async def isolated_call_tool():
            """Isolated call_tool using patched pydantic_ai methods."""
            return await super(CachedMCPServerStreamableHTTP, self).call_tool(name, tool_args, ctx, tool)  # pylint: disable=super-with-arguments

        def fallback(exc):
            return f"Exception {type(exc)} when calling tool '{name}': {exc}. Consider alternative approaches."

        result = await self._run_direct_or_isolated(isolated_call_tool, fallback, timeout=3600.0)
        logger.info("MCP %s: call_tool '%s' completed.", self.url, name)
        return result

    async def direct_call_tool(
        self, name: str, args: dict[str, Any], metadata: dict[str, Any] | None = None
    ) -> ToolResult:
        """Override to fix variable scoping bug in direct_call_tool."""
        result = None  # Initialize to prevent UnboundLocalError
        async with self:  # Ensure server is running
            try:
                result = await self._client.send_request(
                    mcp_types.ClientRequest(
                        mcp_types.CallToolRequest(
                            method="tools/call",
                            params=mcp_types.CallToolRequestParams(
                                name=name,
                                arguments=args,
                                _meta=mcp_types.RequestParams.Meta(**metadata) if metadata else None,
                            ),
                        )
                    ),
                    mcp_types.CallToolResult,
                )
            except McpError as e:
                raise exceptions.ModelRetry(e.error.message)

        if not result:
            raise exceptions.ModelRetry("No result from MCP server")

        content = [await self._map_tool_result_part(part) for part in result.content]

        if result.isError:
            text = "\n".join(str(part) for part in content)
            raise exceptions.ModelRetry(text)

        return content[0] if len(content) == 1 else content


class PatchedStreamableHTTPTransport(streamable_http.StreamableHTTPTransport):
    """Patched StreamableHTTPTransport with exception suppression for _handle_post_request."""

    async def _handle_post_request(self, ctx: streamable_http.RequestContext) -> None:
        """Patched _handle_post_request with proper error handling."""
        try:
            await super()._handle_post_request(ctx)
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("MCP %s: _handle_post_request %s: %s", self.url, type(exc).__name__, exc)


@asynccontextmanager
async def patched_streamablehttp_client(  # noqa: PLR0913, pylint: disable=too-many-arguments,too-many-positional-arguments,too-many-locals
    url: str,
    headers: dict[str, str] | None = None,
    timeout: float | timedelta = 30,
    sse_read_timeout: float | timedelta = DEFAULT_MCP_READ_TIMEOUT,
    terminate_on_close: bool = True,
    httpx_client_factory: streamable_http.McpHttpClientFactory = streamable_http.create_mcp_http_client,
    auth: httpx.Auth | None = None,
) -> AsyncGenerator[
    tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
        streamable_http.GetSessionIdCallback,
    ],
    None,
]:
    """Patched version of `streamablehttp_client` with exception suppression."""
    try:
        transport = PatchedStreamableHTTPTransport(url, headers, timeout, sse_read_timeout, auth)

        read_stream_writer, read_stream = anyio.create_memory_object_stream[SessionMessage | Exception](0)
        write_stream, write_stream_reader = anyio.create_memory_object_stream[SessionMessage](0)
        async with anyio.create_task_group() as tg:
            try:
                async with httpx_client_factory(
                    headers=transport.request_headers,
                    timeout=httpx.Timeout(transport.timeout, read=transport.sse_read_timeout),
                    auth=transport.auth,
                ) as client:
                    # Define callbacks that need access to tg
                    def start_get_stream() -> None:
                        tg.start_soon(transport.handle_get_stream, client, read_stream_writer)

                    tg.start_soon(
                        transport.post_writer,
                        client,
                        write_stream_reader,
                        read_stream_writer,
                        write_stream,
                        start_get_stream,
                        tg,
                    )

                    try:
                        yield (
                            read_stream,
                            write_stream,
                            transport.get_session_id,
                        )
                    except GeneratorExit:
                        logger.warning("patched_streamablehttp_client: GeneratorExit caught, closing streams.")
                    finally:
                        if transport.session_id and terminate_on_close:
                            await transport.terminate_session(client)
                        tg.cancel_scope.cancel()
            finally:
                await read_stream_writer.aclose()
                await write_stream.aclose()
    except Exception as exc:  # pylint: disable=broad-except
        if str(exc) == "Attempted to exit cancel scope in a different task than it was entered in":
            logger.warning("MCP %s: patched_streamablehttp_client: enter/exit cancel scope task mismatch.", url)
        else:
            logger.error("MCP %s: patched_streamablehttp_client: %s: %s", url, type(exc).__name__, exc)
