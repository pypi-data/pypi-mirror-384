# Clipboard MCP Server

A Model Context Protocol (MCP) server that provides system clipboard read and write capabilities for AI assistants like Claude.

## Features

- **read_clipboard**: Read text content from the system clipboard
- **write_clipboard**: Write text content to the system clipboard
- Cross-platform support (Linux, Windows, WSL)

## Installation

```bash
pip install -e ~/clipboard-mcp
```

## Usage

Add to your Claude Code MCP configuration:

```bash
claude mcp add --scope user clipboard-mcp clipboard-mcp
```

## Requirements

### Linux
- `xclip` or `xsel` (install with `sudo apt install xclip xsel`)

### Windows/WSL
- PowerShell (usually pre-installed)
- `clip.exe` (usually pre-installed)

## License

MIT
