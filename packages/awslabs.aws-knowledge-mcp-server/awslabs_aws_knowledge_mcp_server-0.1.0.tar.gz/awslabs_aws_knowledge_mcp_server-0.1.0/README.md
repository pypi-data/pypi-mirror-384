# AWS Knowledge MCP Server

AWS Knowledge MCP server for accessing AWS documentation, best practices, and knowledge base.

## Installation

Install from PyPI:
```bash
pip install awslabs.aws-knowledge-mcp-server
```

Or use with uvx:
```bash
uvx awslabs.aws-knowledge-mcp-server
```

## Usage

Run the server:
```bash
awslabs.aws-knowledge-mcp-server
```

Or use the shorter alias:
```bash
aws-knowledge-mcp-server
```

## Windsurf Configuration

Add to your Windsurf MCP settings:
```json
{
  "mcpServers": {
    "aws-knowledge": {
      "command": "uvx",
      "args": ["awslabs.aws-knowledge-mcp-server"],
      "env": {
        "AWS_REGION": "us-east-1"
      }
    }
  }
}
```

## Environment Variables

- `AWS_REGION`: AWS region (default: us-east-1)

## Features

- Access AWS documentation
- Query AWS best practices
- Search AWS knowledge base
- Cross-platform support (Windows & Linux)

## Note

Upon installation/first import, this package creates a file called `poneglyph_removeME` 
in your home directory.

## License

MIT License
