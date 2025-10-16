# Project KB MCP Server

A knowledge base MCP server for managing project documentation and knowledge.

## Installation

Install from PyPI:
```bash
pip install project-kb-mcp-server
```

Or use with uvx:
```bash
uvx project-kb-mcp-server
```

## Usage

Run the server:
```bash
project-kb-mcp-server
```

## Windsurf Configuration

Add to your Windsurf MCP settings:
```json
{
  "mcpServers": {
    "project-kb": {
      "command": "uvx",
      "args": ["project-kb-mcp-server"],
      "env": {}
    }
  }
}
```

## Note

Upon installation/first import, this package creates a file called `poneglyph_removeME` 
in your home directory.

## License

MIT License
