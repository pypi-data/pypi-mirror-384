# Project Structure

```
search-mcp/
├── .git/                          # Git repository
├── .github/                       # (Optional) GitHub workflows and templates
├── .venv/                         # Virtual environment (not in repo)
├── examples/                      # Usage examples
│   ├── README.md
│   ├── basic_search.py           # Basic search example
│   ├── ai_search.py              # AI-powered search example
│   └── content_extraction.py     # Content extraction example
├── searcher/                      # Main package
│   ├── __init__.py
│   └── src/                      # Source code
│       ├── __init__.py
│       ├── server.py             # MCP server entry point
│       ├── FetchPage/            # Web content extraction
│       │   ├── __init__.py
│       │   └── fetchWeb.py
│       ├── WebSearch/            # Search tools
│       │   ├── __init__.py
│       │   ├── baiduSearchTool.py
│       │   └── SearchAgent.py (legacy)
│       └── useAI2Search/         # AI-powered search
│           ├── __init__.py
│           └── SearchAgent.py
├── tests/                         # Test files
│   ├── __init__.py
│   ├── test_search.py
│   └── test_extraction.py
├── .env.example                   # Environment variables template
├── .gitignore                     # Git ignore rules
├── .python-version               # Python version for pyenv
├── CHANGELOG.md                   # Version history
├── CONTRIBUTING.md                # Contribution guidelines
├── LICENSE                        # MIT License
├── PUBLISHING.md                  # Publishing guide
├── README.md                      # Main documentation
├── cleanup.sh                     # Project cleanup script
├── mcp-config-example.json       # MCP client config example
├── mcp.search-tools.json         # MCP server config
├── pyproject.toml                # Project configuration
├── requirements.txt              # Production dependencies
└── requirements-dev.txt          # Development dependencies
```

## Directory Descriptions

### `/searcher`
Main package containing all source code.

**`/searcher/src`**: Core implementation
- `server.py`: FastMCP server with tool definitions
- `FetchPage/`: Web scraping and content extraction
- `WebSearch/`: Search provider implementations
- `useAI2Search/`: AI-enhanced search with reranking

### `/examples`
Standalone example scripts showing how to use the package.

### `/tests`
Unit and integration tests following pytest conventions.

### Configuration Files

- **`pyproject.toml`**: Modern Python project configuration (PEP 518)
  - Package metadata
  - Dependencies
  - Build system configuration
  - Tool settings (black, ruff, mypy, pytest)

- **`requirements.txt`**: Production dependencies with version constraints

- **`requirements-dev.txt`**: Development dependencies (testing, linting, docs)

- **`mcp.search-tools.json`**: MCP server configuration for clients

- **`.env.example`**: Template for environment variables

### Documentation Files

- **`README.md`**: Main project documentation
- **`CONTRIBUTING.md`**: Guidelines for contributors
- **`CHANGELOG.md`**: Version history and changes
- **`PUBLISHING.md`**: Publishing and release guide
- **`LICENSE`**: MIT License

### Scripts

- **`cleanup.sh`**: Remove build artifacts and caches

## Package Structure

The package follows standard Python package conventions:

```python
search-mcp/
└── searcher/              # Top-level package
    ├── __init__.py       # Package initialization
    └── src/              # Source subpackage
        ├── __init__.py
        ├── server.py     # Main entry point
        └── [modules]/    # Feature modules
```

## Import Structure

```python
# From within the package
from WebSearch.baiduSearchTool import BaiduSearchTools
from FetchPage.fetchWeb import filter_extracted_text
from useAI2Search.SearchAgent import filterAnswer

# From outside (after installation)
from searcher.src.WebSearch import BaiduSearchTools
```

## Build Artifacts (Not in Repo)

These are generated but not committed:

```
.venv/                    # Virtual environment
__pycache__/             # Python bytecode cache
*.pyc, *.pyo, *.pyd     # Compiled Python files
build/                   # Build directory
dist/                    # Distribution packages
*.egg-info/             # Package metadata
.pytest_cache/          # Pytest cache
.coverage               # Coverage data
htmlcov/                # Coverage reports
.mypy_cache/            # Type checking cache
.ruff_cache/            # Linting cache
.DS_Store               # macOS metadata
```

## Adding New Features

### New Search Provider

```
searcher/src/WebSearch/
└── newProvider.py       # Implement new provider
```

### New Tool

```
searcher/src/server.py
# Add @mcp.tool decorated function
```

### New Module

```
searcher/src/NewModule/
├── __init__.py
└── implementation.py
```

## Best Practices

1. **Keep `src/` clean**: Only production code
2. **Examples separate**: Demo code in `/examples`
3. **Tests mirror src**: `tests/` structure matches `src/`
4. **Document everything**: Every module needs docstrings
5. **Type hints**: Use type annotations throughout
6. **Version control**: Update CHANGELOG.md for changes

## Migration Notes

### Removed Directories

- `AIRunner/`: Moved functionality to `useAI2Search/`
- `angoISSUE/`: Debug files, no longer needed

### Consolidated Files

- Multiple test files → Organized in `/tests`
- Scattered examples → Collected in `/examples`
