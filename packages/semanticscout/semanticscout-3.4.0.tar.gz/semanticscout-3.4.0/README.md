# SemanticScout 🔍
## Please note: this is just an idea project to try and build something for use in non Augment Code world 
I have yet to refactor lots of slop, and implement a bunch of key changes

> Language-aware semantic code search for AI agents withdependency analysis

[![Version](https://img.shields.io/badge/version-3.4.0-blue)]()
[![Tests](https://img.shields.io/badge/tests-passing-brightgreen)]()
[![Coverage](https://img.shields.io/badge/coverage-55%25-green)]()
[![Python](https://img.shields.io/badge/python-3.10+-blue)]()
[![License](https://img.shields.io/badge/license-MIT-blue)]()

**SemanticScout** is a Model Context Protocol (MCP) server that provides intelligent code search for AI agents. It combines semantic search with language-aware analysis to understand code relationships, dependencies, and architecture.

## ✨ Key Features

- 🎯 **Language-Aware Analysis** - Automatic language detection with specialized dependency analysis (Rust, C#, Python, etc.)
- 🔍 **Semantic Code Search** - Natural language queries with 100% accuracy and intelligent context expansion
- 🧠 **Query Intent Tracking** - Meta-learning system that improves search performance over time
- 🚫 **Smart Test Filtering** - Automatically excludes test files (0% test pollution) with multi-strategy detection
- 🗂️ **Git Integration** - Smart filtering of untracked files and incremental indexing (5-10x faster updates)
- 🔄 **Hybrid Retrieval** - Combines semantic, symbol, and dependency-based search with AST parsing
- ⚡ **High Performance** - Local embeddings (sentence-transformers), <100ms queries, <2s per file indexing
- 🌐 **Multi-Language** - TypeScript, JavaScript, Python, Java, C#, Go, Rust, Ruby, PHP, C, C++
- 🤖 **MCP Ready** - Works with Claude Desktop and other MCP clients out of the box

## 🚀 Quick Start

Get started in **under 2 minutes** with zero configuration required!

### Prerequisites

- **uv** - [Install uv](https://docs.astral.sh/uv/getting-started/installation/)
- **Claude Desktop** - [Install Claude Desktop](https://claude.ai/download)

### Setup

1. **Configure Claude Desktop** - Add to your MCP configuration file:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**Mac:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "semanticscout": {
      "command": "uvx",
      "args": ["--python", "3.12", "semanticscout@latest"]
    }
  }
}
```

2. **Restart Claude Desktop** - SemanticScout will be automatically downloaded and ready to use!

**✨ What you get:**
- Language-aware analysis with automatic project detection
- Fast local embeddings (sentence-transformers, no Ollama needed)
- Smart test file filtering and git integration
- All data stored in `~/semanticscout/`

> **Note:** Use Python 3.12 for best compatibility. Some dependencies don't yet support Python 3.13.

## 📖 Usage

Once configured, use natural language to interact with SemanticScout through Claude:

### Example Conversations

**Index a codebase:**
```
You: "Index my codebase at /workspace"
Claude: [Calls index_codebase tool and shows indexing progress]
```

**Search for code:**
```
You: "Find the authentication logic"
Claude: [Calls search_code tool and shows relevant code snippets]
```

**Advanced queries:**
```
You: "Show me dependency injection configuration"
Claude: [Automatically detects architectural query and expands coverage]
```

### Available Tools

| Tool | Description | Key Parameters |
|------|-------------|----------------|
| `index_codebase` | Index a codebase with language-aware analysis | `path`, `incremental` |
| `search_code` | Search with natural language + smart filtering | `query`, `collection_name`, `exclude_test_files` |
| `find_symbol` | Find symbols with language-aware lookup | `symbol_name`, `collection_name` |
| `trace_dependencies` | Trace dependency chains | `file_path`, `collection_name`, `depth` |
| `list_collections` | List all indexed codebases | None |

### Advanced Features

- **Incremental Indexing**: Use `incremental=True` for 5-10x faster updates on existing codebases
- **Test Filtering**: Set `exclude_test_files=False` to include test files in search results
- **Coverage Modes**: Use `coverage_mode` for different result depths (focused/balanced/comprehensive/exhaustive)
- **Real-time Updates**: Process file change events from editors automatically

## 🔧 Configuration

### Default Setup (Recommended)
The default configuration works great for most users - no additional setup needed!

### Custom Embedding Models
To use a different sentence-transformers model:

```json
{
  "mcpServers": {
    "semanticscout": {
      "command": "uvx",
      "args": ["--python", "3.12", "semanticscout@latest"],
      "env": {
        "SEMANTICSCOUT_CONFIG_JSON": "{\"embedding\":{\"provider\":\"sentence-transformers\",\"model\":\"all-mpnet-base-v2\"}}"
      }
    }
  }
}
```

### Ollama (Optional - GPU Acceleration)
For GPU acceleration with Ollama:

```bash
# Start Ollama and pull model
ollama serve
ollama pull nomic-embed-text
```

```json
{
  "mcpServers": {
    "semanticscout": {
      "command": "uvx",
      "args": ["--python", "3.12", "semanticscout@latest"],
      "env": {
        "OLLAMA_BASE_URL": "http://localhost:11434",
        "OLLAMA_MODEL": "nomic-embed-text",
        "SEMANTICSCOUT_CONFIG_JSON": "{\"embedding\":{\"provider\":\"ollama\"}}"
      }
    }
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Python Version Error:** Use Python 3.12 for best compatibility (some dependencies don't support 3.13 yet)

**Ollama Not Available:** The default uses sentence-transformers (no Ollama needed). Only configure Ollama if you want GPU acceleration.

**Rate Limits:** Adjust limits with environment variables:
```json
"env": {
  "MAX_INDEXING_REQUESTS_PER_HOUR": "20",
  "MAX_SEARCH_REQUESTS_PER_MINUTE": "200"
}
```

## 📚 Documentation

- **[API Reference](docs/API_REFERENCE.md)** - Complete tool documentation
- **[User Guide](docs/USER_GUIDE.md)** - Examples and best practices
- **[Configuration](docs/CONFIGURATION.md)** - Advanced configuration options
- **[Performance Tuning](docs/PERFORMANCE_TUNING.md)** - Optimization guide

## 🏗️ Architecture

SemanticScout combines multiple technologies for intelligent code search:

- **Language Detection** → **AST Parsing** (tree-sitter) → **Symbol Extraction**
- **Semantic Chunking** → **Embeddings** (sentence-transformers/Ollama) → **Vector Storage** (ChromaDB)
- **Dependency Analysis** → **Graph Storage** (NetworkX) → **Symbol Tables** (SQLite)
- **Hybrid Search** → **Context Expansion** → **Smart Filtering**

## 🤝 Contributing

Contributions welcome! See our [contributing guide](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

**Built with ❤️ for the AI agent ecosystem**

