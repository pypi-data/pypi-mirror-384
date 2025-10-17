import asyncio

from loguru import logger

from .server import mcp

def main() -> None:
    """Main entry point for the web scraping MCP server."""
    logger.info("Starting web scraping MCP server...")
    # FastMCP runs as stdio by default for MCP protocol
    asyncio.run(mcp.run_async())