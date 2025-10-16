# Examples

This directory contains example scripts demonstrating how to use the Search MCP Server functionality.

## Available Examples

### 1. Basic Search (`basic_search.py`)

Demonstrates basic Baidu search functionality without AI enhancement.

```bash
cd examples
python basic_search.py
```

**Features:**
- Simple search query execution
- Structured result parsing
- No API key required

### 2. AI-Powered Search (`ai_search.py`)

Shows AI-enhanced search with intelligent reranking and content extraction.

```bash
export DASHSCOPE_API_KEY="your-api-key"
cd examples
python ai_search.py
```

**Features:**
- AI-powered result reranking
- Full page content extraction
- Parallel processing with multiple AI agents
- Requires DASHSCOPE_API_KEY

### 3. Content Extraction (`content_extraction.py`)

Demonstrates extracting clean text from web pages.

```bash
cd examples
python content_extraction.py
```

**Features:**
- Clean text extraction with trafilatura
- HTML parsing and cleaning
- Pagination support (optional)

## Running Examples

### Prerequisites

```bash
# Install the package
pip install -e ..

# Or install dependencies
pip install -r ../requirements.txt
```

### With Environment Variables

```bash
# Set API key
export DASHSCOPE_API_KEY="your-key-here"

# Run example
python ai_search.py
```

### Modifying Examples

Feel free to modify these examples:

```python
# Change search query
query = "Your search query here"

# Adjust result count
max_results = 10

# Change language
language = "en"  # or "zh"
```

## Integration Examples

### Using as MCP Server

See `../mcp-config-example.json` for MCP client configuration.

### Programmatic Usage

```python
from WebSearch.baiduSearchTool import BaiduSearchTools

# Initialize
tool = BaiduSearchTools()

# Search
results = tool.baidu_search("query", max_results=5)
```

## Troubleshooting

### Import Errors

If you get import errors, ensure the package is installed:

```bash
cd ..
pip install -e .
```

### API Key Issues

For AI features, ensure DASHSCOPE_API_KEY is set:

```bash
echo $DASHSCOPE_API_KEY
```

### Network Issues

Some examples require internet access. Check your connection and firewall settings.

## Contributing

Found a bug or have an improvement? See [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines.
