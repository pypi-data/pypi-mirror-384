# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Google Search integration
- Multi-language support enhancement
- Result caching mechanism
- Rate limiting and retry logic
- WebSocket support for streaming results

## [0.1.0] - 2025-10

### Added
- Initial release of Search MCP Server
- Baidu search integration with `search_baidu` tool
- AI-powered search with intelligent reranking (`AI_search_baidu`)
- Web content extraction from single URL (`extractTextFromUrl`)
- Batch web content extraction (`extractTextFromUrls`)
- Support for pagination following in content extraction
- Regex-based text filtering
- Multiple AI agents (Qwen Flash) for parallel result reranking
- FastMCP framework integration
- Comprehensive documentation and examples
- MIT License

### Features
- **search_baidu**: Basic Baidu search with structured results
- **AI_search_baidu**: AI-enhanced search with reranking and full content extraction
- **extractTextFromUrl**: Clean text extraction with trafilatura
- **extractTextFromUrls**: Batch URL processing
- Configurable timeout and user-agent settings
- Support for rel="next" pagination
- Async operation support

### Technical
- Python 3.10+ support
- Type hints throughout codebase
- Pydantic models for data validation
- Error handling and fallback mechanisms
- Comprehensive .gitignore
- PyPI-ready package structure

### Documentation
- Detailed README with usage examples
- API documentation for all tools
- MCP client configuration examples
- Publishing guide (PUBLISHING.md)
- License (MIT)

### Dependencies
- fastmcp >= 0.1.0
- agno >= 0.1.0
- requests >= 2.31.0
- baidusearch >= 1.0.0
- trafilatura >= 1.6.0
- beautifulsoup4 >= 4.12.0
- lxml >= 4.9.0
- pydantic >= 2.0.0
- pycountry >= 22.0.0

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

---

**Note**: This project follows semantic versioning. Versions are tagged as `vX.Y.Z` where:
- X = Major version (breaking changes)
- Y = Minor version (new features, backward compatible)
- Z = Patch version (bug fixes, backward compatible)
