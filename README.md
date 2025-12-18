# getllamp-mcp

MCP Server for Z-machine interactive fiction games using the Jericho library.

## Overview

This is a standalone [Model Context Protocol (MCP)](https://modelcontextprotocol.io/) server that lets LLMs play classic text adventure games (Zork, Hitchhiker's Guide, etc.) through the Jericho Z-machine interpreter.

## Features

- **16 MCP Tools**: Game control, save/restore, valid actions, object inspection
- **Session Management**: Multiple concurrent game sessions with timeout cleanup
- **Feature Toggles**: Enable/disable valid actions, object tree, walkthrough hints
- **Game State**: Score tracking, inventory, location info

## Installation

```bash
# With uv
uv pip install -e .
python -m spacy download en_core_web_sm

# With pip
pip install -e .
python -m spacy download en_core_web_sm
```

## Usage

### Standalone Server

```bash
# Run with stdio transport (for Claude Desktop, Gemini CLI, etc.)
getllamp-mcp --games-dir /path/to/games

# With feature flags
getllamp-mcp --enable-valid-actions --enable-object-tree
```

### Gemini CLI Configuration

Add to `~/.gemini/settings.json`:

```json
{
  "mcpServers": {
    "getllamp": {
      "command": "/path/to/getllamp-mcp/.venv/bin/python",
      "args": ["-m", "mcp_server.server", "--games-dir", "/path/to/games"],
      "cwd": "/path/to/getllamp-mcp"
    }
  }
}
```

## Available Tools

| Tool | Description |
|------|-------------|
| `list_available_games` | List Z-machine games in games directory |
| `start_game` | Start a new game session |
| `play_action` | Execute an action in the game |
| `get_game_state` | Get current score, location, inventory |
| `look` | Look around current location |
| `check_inventory` | List carried items |
| `get_valid_actions` | Get valid commands (if enabled) |
| `get_nearby_objects` | Get objects in current location |
| `get_world_tree` | Get full object tree (if enabled) |
| `save_game` | Save to a named slot |
| `restore_game` | Restore from a slot |
| `list_saves` | List save slots |
| `export_save` | Export save as base64 |
| `import_save` | Import save from base64 |
| `close_session` | End a game session |
| `list_sessions` | List active sessions |

## License

MIT
