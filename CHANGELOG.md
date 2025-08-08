# Changelog

All notable changes to the Budget Cash Envelope MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2025-08-08

### Added
- **Budget Health Analysis Prompt**: Intelligent financial analysis prompt that provides personalized budget insights
  - Envelope health scoring with status indicators (healthy, overspent, underutilized, nearly_depleted)
  - Spending pattern analysis across configurable time periods
  - Actionable budget recommendations based on transaction data
  - Executive summary with overall health scores and key metrics
- **Complete MCP Protocol Support**: Added missing `resources/list` and `prompts/list` handlers
  - Resolves Claude Desktop compatibility issues and server crashes
  - Full MCP protocol compliance for better client integration
- **Server Version API**: New `get_server_version` tool for client version queries
  - Runtime version access via `importlib.metadata`
  - Comprehensive version information including metadata
  - Single source of truth from `pyproject.toml`

### Changed
- **Type Safety Improvements**: Complete mypy compliance across all modules
  - Fixed Optional type annotations using modern `| None` syntax
  - Added proper type ignores for dynamic FastMCP attributes
  - Enhanced schema test flexibility for FastMCP's `anyOf` patterns

### Fixed
- **MCP Server Crashes**: Fixed "Method not found" errors when connecting with Claude Desktop
- **Code Quality**: Resolved all mypy, ruff, and black formatting issues
- **Test Coverage**: Updated schema tests to handle FastMCP type generation patterns

### Technical Details
- Added comprehensive prompt system with structured analysis algorithms
- Implemented version utilities module for consistent version access
- Enhanced error handling and logging throughout prompt functionality
- Maintained backwards compatibility with existing tool functionality

## [0.1.0] - 2025-01-XX

### Added
- Initial Budget Cash Envelope MCP Server implementation
- Core envelope management (create, read, update, delete)
- Transaction tracking with income/expense categorization
- MotherDuck cloud integration for data synchronization
- FastMCP and standard MCP SDK server implementations
- Bearer token authentication middleware
- Comprehensive test suite with 264+ tests
- Docker containerization and HTTPS support

[Unreleased]: https://github.com/drwestman/budget-mcp-server/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/drwestman/budget-mcp-server/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/drwestman/budget-mcp-server/releases/tag/v0.1.0