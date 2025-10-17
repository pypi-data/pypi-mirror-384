# Timesheet MCP Server

[![PyPI version](https://badge.fury.io/py/timesheet-mcp-server.svg)](https://badge.fury.io/py/timesheet-mcp-server)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A Model Context Protocol (MCP) server for timesheet management system, built with FastMCP 2.0.

## 🚀 Quick Start

### Installation

Using uvx (recommended):
```bash
uvx timesheet-mcp-server
```

Using pip:
```bash
pip install timesheet-mcp-server
```

### Configuration

Set up your Claude Desktop config file:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "timesheet": {
      "command": "uvx",
      "args": ["timesheet-mcp-server"],
      "env": {
        "TIMESHEET_API_BASE_URL": "http://127.0.0.1:8080/api",
        "TIMESHEET_API_TOKEN": "your-jwt-token"
      }
    }
  }
}
```

## ✨ Features

### Time Entry Queries (2)
- Get my time entries with filters
- Get recent time entries

### User Queries (3)
- Search users by name
- Get user details
- Get user time entries

### Project Queries (7)
- List projects with filters
- Get my projects
- Get project tree structure
- Get project members
- Get project details
- Get project time plan
- List business lines

### Reports & Statistics (5)
- Time statistics with grouping
- Time entry reports
- Project time reports
- Working days information
- Time entry warnings

## 📖 Usage Examples

After setting up, you can use natural language in Claude Desktop:

```
Please show me my time entries

List all projects

Search for user "John Doe"

Get time statistics for this week

Show me project details for project #123
```

## 🔧 Environment Variables

- `TIMESHEET_API_BASE_URL` - API base URL (required)
- `TIMESHEET_API_TOKEN` - JWT token for authentication (required)
- `MCP_TRANSPORT` - Transport method (default: stdio)
- `MCP_LOG_LEVEL` - Logging level (default: INFO)

## 🛠️ Development

Clone the repository:
```bash
git clone https://github.com/yangyuezheng/ai-emp.git
cd ai-emp/timesheet-mcp-server-v2
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Run tests:
```bash
python test_tools.py
```

## 📚 Documentation

- [Full Documentation](https://github.com/yangyuezheng/ai-emp/tree/feature/mcp-server-v2-fastmcp/timesheet-mcp-server-v2)
- [Internal Distribution Guide](https://github.com/yangyuezheng/ai-emp/blob/feature/mcp-server-v2-fastmcp/timesheet-mcp-server-v2/docs/internal-distribution-guide.md)
- [Testing Guide](https://github.com/yangyuezheng/ai-emp/blob/feature/mcp-server-v2-fastmcp/timesheet-mcp-server-v2/docs/testing-guide.md)

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## 📞 Support

- Issues: [GitHub Issues](https://github.com/yangyuezheng/ai-emp/issues)
- Documentation: [GitHub Docs](https://github.com/yangyuezheng/ai-emp/tree/feature/mcp-server-v2-fastmcp/timesheet-mcp-server-v2/docs)

## 🙏 Acknowledgments

- [FastMCP](https://gofastmcp.com) - MCP framework
- [Model Context Protocol](https://spec.modelcontextprotocol.io) - Protocol specification
- [Claude](https://claude.ai) - AI assistant

---

**Version:** 2.0.0
**Status:** Production Ready ✅
