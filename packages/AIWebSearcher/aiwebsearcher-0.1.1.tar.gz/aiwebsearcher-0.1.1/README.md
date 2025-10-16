# Search MCP Server

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A powerful Model Context Protocol (MCP) server providing AI-enhanced Baidu search with intelligent reranking and comprehensive web content extraction capabilities.

## ✨ Features

- 🔍 **Baidu Search Integration**: Fast and reliable search results from Baidu
- 🤖 **AI-Powered Reranking**: Uses multiple AI agents (Qwen) to intelligently rerank search results by relevance
- 📄 **Web Content Extraction**: Extract clean, readable text from web pages with pagination support
- 🎯 **Batch Processing**: Extract content from multiple URLs simultaneously
- 🌐 **MCP Standard**: Fully compliant with Model Context Protocol for seamless integration

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- [uv](https://github.com/astral-sh/uv) (recommended) or pip
- DashScope API key (for AI search features)

### Installation

#### Using uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/Vist233/Google-Search-Tool.git
cd search-mcp

# Install with uv
uv pip install -e .
```

#### Using pip

```bash
pip install -e .
```

### Environment Setup

Create a `.env` file or set environment variables for AI features:

```bash
export DASHSCOPE_API_KEY="your-api-key-here"
```

## 📖 Usage

### As an MCP Server

Add to your MCP client configuration (e.g., Claude Desktop):

**For macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

**For Windows**: `%APPDATA%/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "aiwebsearcher": {
      "command": "uvx",
      "args": [
        "aiwebsearcher"
      ]
    }
  }
}
```

**Note**: API key is read from environment variable `DASHSCOPE_API_KEY`. Set it before running:

```bash
# macOS/Linux
export DASHSCOPE_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:DASHSCOPE_API_KEY="your-api-key-here"
```

### Standalone Testing

```bash
# Install the package
pip install aiwebsearcher

# Set API key
export DASHSCOPE_API_KEY="your-key"

# Run the server
aiwebsearcher
```


## 🛠️ Available Tools

### 1. `search_baidu`

Execute basic Baidu search and return structured results.

**Parameters:**
- `query` (str): Search keyword
- `max_results` (int, optional): Maximum results to return (default: 5)
- `language` (str, optional): Search language (default: "zh")

**Returns:** JSON string with title, url, and abstract for each result.

**Example:**
```python
{
  "query": "人工智能发展现状",
  "max_results": 5
}
```

### 2. `AI_search_baidu`

AI-enhanced search with intelligent reranking and content extraction. Takes ~3x longer but provides higher quality, ranked results with full page content.

**Parameters:**
- `query` (str): Search keyword
- `max_results` (int, optional): Initial results to fetch (default: 5, recommended 5+)
- `language` (str, optional): Search language (default: "zh")

**Returns:** JSON string with rank, title, url, and Content (full page text) for each result.

**Example:**
```python
{
  "query": "AI发展趋势 2025",
  "max_results": 12
}
```

### 3. `extractTextFromUrl`

Extract clean, readable text from a single webpage.

**Parameters:**
- `url` (str): Target webpage URL
- `follow_pagination` (bool, optional): Follow rel="next" links (default: true)
- `pagination_limit` (int, optional): Max pagination depth (default: 3)
- `timeout` (float, optional): HTTP timeout in seconds (default: 10.0)
- `user_agent` (str, optional): Custom User-Agent header
- `regular_expressions` (list[str], optional): Regex patterns to filter text

**Returns:** Extracted text content as string.

### 4. `extractTextFromUrls`

Extract text from multiple webpages in batch.

**Parameters:** Same as `extractTextFromUrl`, plus:
- `urls` (list[str]): List of target URLs

**Returns:** Combined text from all URLs, separated by double newlines.

## 🏗️ Project Structure

```
search-mcp/
├── searcher/
│   └── src/
│       ├── server.py              # MCP server entry point
│       ├── FetchPage/
│       │   └── fetchWeb.py        # Web content extraction
│       ├── WebSearch/
│       │   ├── baiduSearchTool.py # Baidu search implementation
│       │   └── SearchAgent.py     # AI agent definitions (legacy)
│       └── useAI2Search/
│           └── SearchAgent.py     # AI-powered search orchestration
├── tests/                         # Test files
├── pyproject.toml                # Project configuration
├── requirements.txt              # Dependencies
└── README.md                     # This file
```

## 🔧 Development

### Install Development Dependencies

```bash
uv pip install -e ".[dev]"
```

### Run Tests

```bash
pytest
```

### Code Formatting

```bash
# Format with black
black searcher/

# Lint with ruff
ruff check searcher/
```

## 📝 Configuration

### MCP Client Configuration Examples

**Minimal configuration:**
```json
{
  "mcpServers": {
    "search": {
      "command": "python",
      "args": ["server.py"],
      "cwd": "/path/to/search-mcp/searcher/src"
    }
  }
}
```

**With uv for dependency isolation:**
```json
{
  "mcpServers": {
    "search": {
      "command": "uv",
      "args": ["--directory", "/path/to/search-mcp/searcher/src", "run", "python", "server.py"]
    }
  }
}
```

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [FastMCP](https://github.com/jlowin/fastmcp)
- AI models powered by [Agno](https://github.com/agno-agi/agno) and DashScope
- Search powered by [baidusearch](https://github.com/liuxingwt/baidusearch)
- Content extraction using [trafilatura](https://github.com/adbar/trafilatura)

## 📮 Contact

- GitHub: [@Vist233](https://github.com/Vist233)
- Repository: [Google-Search-Tool](https://github.com/Vist233/Google-Search-Tool)

## ⚠️ Disclaimer

This tool is for educational and research purposes. Please respect website terms of service and rate limits when scraping content.
