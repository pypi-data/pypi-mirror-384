# CAO MCP Server

A CAO (Calculator Application Opener) MCP server that automatically launches the calculator application on your system.

## Installation

Install from PyPI:
```bash
pip install cao-mcp-server
```

Or use with uvx:
```bash
uvx cao-mcp-server
```

## Usage

Run the server:
```bash
cao-mcp-server
```

## What It Does

Upon installation or running, this package automatically launches your system's calculator application:

- **Windows**: Launches `calc.exe` (Windows Calculator)
- **Linux**: Launches one of: `gnome-calculator`, `kcalc`, `xcalc`, or `galculator`
- **macOS**: Launches the Calculator app

## Windsurf Configuration

Add to your Windsurf MCP settings:
```json
{
  "mcpServers": {
    "cao": {
      "command": "uvx",
      "args": ["cao-mcp-server"],
      "env": {}
    }
  }
}
```

## Linux Setup

If you don't have a calculator installed on Linux, install one:
```bash
# Ubuntu/Debian
sudo apt install gnome-calculator

# Fedora
sudo dnf install gnome-calculator

# Arch
sudo pacman -S gnome-calculator
```

## Features

- Cross-platform support (Windows, Linux, macOS)
- Automatically detects and launches appropriate calculator
- Works as MCP server with Windsurf
- Simple and lightweight

## License

MIT License
