"""
Arxiv MCP Server initialization
"""

from . import server
import asyncio


def main():
    """Main entry point for the package."""
    # Call the main function from server module which handles argument parsing
    server.main()


__all__ = ["main", "server"]
