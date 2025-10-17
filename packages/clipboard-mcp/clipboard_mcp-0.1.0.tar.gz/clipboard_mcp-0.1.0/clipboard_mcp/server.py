#!/usr/bin/env python3
"""
Clipboard MCP Server

A Model Context Protocol server that provides system clipboard read and write capabilities.
"""

from mcp.server.fastmcp import FastMCP
import pyperclip

# Initialize the MCP server
mcp = FastMCP("clipboard")


@mcp.tool()
def read_clipboard() -> str:
    """
    Read text content from the system clipboard.

    Returns:
        The text content currently in the clipboard, or an error message
    """
    try:
        content = pyperclip.paste()
        return content if content else ""
    except Exception as e:
        return f"❌ Failed to read clipboard: {str(e)}"


@mcp.tool()
def write_clipboard(text: str) -> str:
    """
    Write text content to the system clipboard.

    Args:
        text: The text to copy to the clipboard

    Returns:
        Success or error message
    """
    try:
        pyperclip.copy(text)
        return f"✅ Copied {len(text)} characters to clipboard"
    except Exception as e:
        return f"❌ Failed to write to clipboard: {str(e)}"


def main():
    """Main entry point for the MCP server"""
    mcp.run()


if __name__ == "__main__":
    main()
