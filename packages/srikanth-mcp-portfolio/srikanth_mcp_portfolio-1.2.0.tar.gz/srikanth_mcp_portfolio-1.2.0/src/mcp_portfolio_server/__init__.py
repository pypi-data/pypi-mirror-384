"""Portfolio MCP Server - A Model Context Protocol server for portfolio data."""

__version__ = "1.0.0"
__author__ = "Srikanth Karthikeyan"
__email__ = "srikanthkarthi2003@gmail.com"

import asyncio
from .server import main as async_main

def main():
    """Synchronous entry point for the MCP server."""
    asyncio.run(async_main())

__all__ = ["main"]