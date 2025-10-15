# Overleaf MCP Server

MCP server that lets compatible clients (e.g., Claude Desktop, Cursor, VS Code) interact with Overleaf projects via tools and resources.

## Features

- List projects and files.
- Read files.
- Safe, read-only mode.

Adjust to match your implementation.

## Requirements

- Python 3.10+
- An Overleaf account (or session cookie)

## Configure a client

### Claude Desktop

Edit claude_desktop_config.json:

```json
{
  "mcpServers": {
    "overleaf": {
      "command": "uv",
      "args": [
        "run",
        "mcp",
        "run",
        "/Volumes/Life/Python/Overleaf/overleaf_mcp/__main__.py"
      ],
      "env": {
        "PROJECT_ID": "<YOUR_PROJECT_ID>",
        "OVERLEAF_TOKEN": "<YOUR_OVERLEAF_TOKEN>"
      },
      "timeout": 120000
    }
  }
}
```

If you have a console script, set "command": "overleaf-mcp" and remove "args".

### Cursor (settings.json)

```json
{
  "mcpServers": {
    "overleaf": {
      "command": "uv",
      "args": [
        "run",
        "mcp",
        "run",
        "/Volumes/Life/Python/Overleaf/overleaf_mcp/__main__.py"
      ],
      "env": {
        "PROJECT_ID": "<YOUR_PROJECT_ID>",
        "OVERLEAF_TOKEN": "<YOUR_OVERLEAF_TOKEN>"
      }
    }
  }
}
```

### VS Code MCP (.vscode/mcp.json)

```jsonc
{
  "servers": {
    "my-mcp-server-overleaf": {
      "type": "stdio",
      "command": "uv",
      "args": [
        "run",
        "mcp",
        "run",
        "/Volumes/Life/Python/Overleaf/overleaf_mcp/__main__.py"
      ],
      "env": {
        "PROJECT_ID": "<YOUR_PROJECT_ID>",
        "OVERLEAF_TOKEN": "<YOUR_OVERLEAF_TOKEN>"
      }
    }
  },
  "inputs": []
}
```

## Tools

<TBD>
