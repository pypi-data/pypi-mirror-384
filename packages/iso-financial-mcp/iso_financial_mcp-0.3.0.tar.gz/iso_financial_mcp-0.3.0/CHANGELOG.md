# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2025-01-15

### Added
- **Meta-tools for consolidated data retrieval**:
  - `get_ticker_complete_analysis`: Single ticker analysis in 1 call - retrieves ALL financial data (info, prices, news, SEC filings, earnings, short volume, Google Trends) in parallel
  - `get_multi_ticker_analysis`: Multi-ticker parallel analysis - analyze multiple tickers simultaneously with a single call
  - `format_snapshot_for_llm`: Token-optimized formatting for LLM consumption
  - `format_multi_snapshot_for_llm`: Consolidated multi-ticker formatting
- **Token optimization features**:
  - Intelligent data truncation (50-70% token reduction)
  - Compact formatting with configurable limits
  - Smart aggregation of historical data
- **Enhanced error handling**:
  - Graceful degradation with partial error reporting
  - Detailed error context and suggestions
  - Resilient parallel execution with `asyncio.gather`
- **Comprehensive test suite**:
  - Unit tests for all meta-tool functions
  - Integration tests for parallel execution
  - Performance benchmarks and validation
  - Test coverage with pytest-cov

### Changed
- Improved parallel data fetching with asyncio.gather for 5-10x performance improvement
- Enhanced error messages with actionable suggestions and context
- Optimized data structures for reduced memory footprint
- Updated documentation with meta-tool examples and migration guide

### Performance
- **5-10x faster data retrieval** vs individual tool calls
- **Reduced LLM iterations** from 25+ to <20 for newsletter generation
- **70% token reduction** through intelligent formatting
- **Parallel execution** for multi-ticker analysis (3 tickers in ~5s vs ~45s sequential)

### Deprecated
- Individual tools (get_info, get_news, etc.) are now considered legacy
  - Still fully functional for backward compatibility
  - Meta-tools are recommended for new implementations
  - See MIGRATION_GUIDE.md for migration examples

## [0.2.2] - 2024-12-15

### Added
- Google Trends integration with search volume analysis
- Momentum indicators and related queries
- Peak detection for trend analysis
- 24-hour caching for trends data

### Fixed
- Rate limiting improvements for Google Trends API
- Cache invalidation edge cases
- Error handling for unavailable trend data

### Changed
- Updated pytrends dependency to 4.9.0+
- Improved trend data formatting
- Enhanced documentation for trends endpoints

## [0.2.1] - 2024-12-01

### Added
- News headlines integration via Yahoo Finance RSS feeds
- Source attribution and duplicate detection
- Summary extraction and publication timestamps
- 2-hour caching for news data

### Fixed
- RSS feed parsing edge cases
- Duplicate news detection algorithm
- Timestamp parsing for various date formats

### Changed
- Improved news formatting for better readability
- Enhanced error messages for RSS feed failures
- Updated feedparser dependency

## [0.2.0] - 2024-11-15

### Added
- **Enhanced data sources for quantitative analysis**:
  - SEC EDGAR API integration for real-time filings (8-K, S-3, 424B, 10-Q, 10-K)
  - FINRA short volume data with trend analysis and ratios
  - Earnings calendar with EPS estimates, actuals, and surprise percentages
- **Advanced caching system**:
  - Multi-tier caching with configurable TTL per data source
  - Memory-efficient cache management
  - Automatic cache cleanup
- **Rate limiting framework**:
  - Per-endpoint rate limiting with exponential backoff
  - Burst protection with token bucket algorithm
  - API-specific limits respecting provider constraints

### Changed
- Refactored data source architecture for better modularity
- Improved error handling with graceful degradation
- Enhanced documentation with quantitative analysis examples
- Updated dependencies for better performance

### Performance
- Implemented connection pooling for HTTP clients
- Optimized cache lookup performance
- Reduced memory usage for large datasets

## [0.1.5] - 2024-10-20

### Added
- Options analysis endpoints (expirations, option chains)
- Institutional holders and major shareholders data
- Analyst recommendations and price targets

### Fixed
- Options data parsing for various expiration formats
- Institutional holdings data validation
- Recommendations formatting edge cases

### Changed
- Improved options data structure
- Enhanced holder information formatting
- Updated yfinance dependency to 0.2.28+

## [0.1.0] - 2024-09-15

### Added
- Initial release with core Yahoo Finance integration
- Basic market data endpoints (info, prices, actions)
- Financial statements (balance sheet, income, cash flow)
- Company information and corporate actions
- FastMCP server implementation
- Async/await architecture throughout
- Basic caching with in-memory storage
- Comprehensive test suite with pytest
- MIT License
- Documentation and usage examples

### Technical Features
- Python 3.10+ support
- UV package manager integration
- Type hints throughout codebase
- Error handling and validation
- HTTP server mode with uvicorn
- MCP protocol compliance

## [Unreleased]

### Planned Features
- Real-time WebSocket streaming for market data
- Advanced technical indicators (RSI, MACD, Bollinger Bands)
- Sector and industry comparison tools
- Portfolio tracking and analysis
- Backtesting framework integration
- Machine learning model integration
- Custom alert system
- Enhanced visualization tools

---

## Version History Summary

| Version | Release Date | Key Features | Performance Impact |
|---------|--------------|--------------|-------------------|
| 0.3.0 | 2025-01-15 | Meta-tools, token optimization | 5-10x faster, 70% token reduction |
| 0.2.2 | 2024-12-15 | Google Trends integration | Improved trend analysis |
| 0.2.1 | 2024-12-01 | News headlines RSS feeds | Enhanced sentiment analysis |
| 0.2.0 | 2024-11-15 | SEC, FINRA, Earnings data | Quantitative analysis support |
| 0.1.5 | 2024-10-20 | Options, holders, recommendations | Options analysis capability |
| 0.1.0 | 2024-09-15 | Initial release | Core functionality |

## Migration Notes

### Upgrading to 0.3.0
- **Recommended**: Migrate to meta-tools for better performance
- **Backward Compatible**: All existing tools continue to work
- **Action Required**: None - upgrade is seamless
- **Benefits**: 5-10x faster execution, 70% token reduction
- **Documentation**: See MIGRATION_GUIDE.md for examples

### Upgrading to 0.2.0
- **New Dependencies**: Added aiohttp, beautifulsoup4, pytrends, feedparser
- **Configuration**: Optional cache TTL configuration available
- **Breaking Changes**: None - fully backward compatible

### Upgrading to 0.1.5
- **New Features**: Options analysis requires yfinance 0.2.28+
- **Breaking Changes**: None

## Support and Contributions

- **Issues**: [GitHub Issues](https://github.com/Niels-8/isofinancial-mcp/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Niels-8/isofinancial-mcp/discussions)
- **Contributing**: See CONTRIBUTING.md for guidelines
- **License**: MIT License - see LICENSE file

## Acknowledgments

Special thanks to all contributors and the open-source community for making this project possible.

---

**Note**: This changelog follows [Keep a Changelog](https://keepachangelog.com/) principles and [Semantic Versioning](https://semver.org/) for version numbering.
