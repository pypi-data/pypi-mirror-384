# Changelog

All notable changes to the DcisionAI MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-15

### Added
- Initial release of DcisionAI MCP Server
- 6 core optimization tools:
  - `classify_intent` - Intent classification for optimization requests
  - `analyze_data` - Data analysis and preprocessing
  - `build_model` - Mathematical model building with Qwen 30B
  - `solve_optimization` - Optimization solving and results
  - `get_workflow_templates` - Industry workflow templates
  - `execute_workflow` - End-to-end workflow execution
- 21 pre-built workflows across 7 industries:
  - Manufacturing (3 workflows)
  - Healthcare (3 workflows)
  - Retail (3 workflows)
  - Marketing (3 workflows)
  - Financial (3 workflows)
  - Logistics (3 workflows)
  - Energy (3 workflows)
- AgentCore Gateway integration
- Qwen 30B integration for mathematical optimization
- Comprehensive CLI with 6 commands
- Multi-IDE support (Cursor, Kiro, Claude Code, VS Code)
- Production-ready error handling and logging
- Docker support
- Comprehensive documentation
- Test suite with pytest
- Configuration management with YAML support
- Rate limiting and security features

### Features
- **Industry-Specific Workflows**: Pre-built optimization workflows for major industries
- **Qwen 30B Integration**: Superior mathematical reasoning for complex optimization problems
- **AgentCore Gateway**: Cloud-native deployment with AWS Bedrock integration
- **Multi-IDE Support**: Works with popular AI coding assistants
- **Production Ready**: Comprehensive error handling, logging, and monitoring
- **CLI Interface**: Easy server management and testing
- **Docker Support**: Containerized deployment options
- **Comprehensive Documentation**: Detailed API reference and examples

### Technical Details
- Python 3.8+ support
- Async/await architecture
- HTTP client with timeout and retry logic
- Structured logging with configurable levels
- Environment-based configuration
- JWT token authentication
- Rate limiting and security features
- Comprehensive test coverage

## [Unreleased]

### Planned Features
- Additional industry workflows
- Custom workflow creation
- Advanced analytics and reporting
- Multi-tenant support
- Enhanced security features
- Performance optimizations
- Additional IDE integrations
