"""
FastMCP logging implementation for Model Context Protocol.
"""

import sys
from typing import Any

from fastmcp import FastMCP
from pydantic import AnyUrl


class FastMcpLog(FastMCP):
    """A FastMCP with hooks for logging."""

    async def _call_tool(self, key: str, arguments: dict[str, Any]):
        print(f"Calling tool: {key} with arguments: {arguments}", file=sys.stderr)
        ret = await super()._call_tool(key, arguments)
        print(f"Tool returned: {ret}", file=sys.stderr)
        return ret

    async def _read_resource(self, uri: AnyUrl | str):
        print(f"Reading resource: {uri}", file=sys.stderr)
        ret = await super()._read_resource(uri)
        print(f"Resource contents: {ret}", file=sys.stderr)
        return ret

    async def get_prompt(self, key: str, arguments: dict[str, Any] | None = None):
        print(f"Getting prompt: {key} with arguments: {arguments}", file=sys.stderr)
        ret = await super()._get_prompt(key, arguments)
        print(f"Prompt result: {ret}", file=sys.stderr)
        return ret
