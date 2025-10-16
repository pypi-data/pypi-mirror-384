# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-16

### Added
- Initial release of Anannas AI integration for Pipecat
- `AnannasLLMService` class extending `OpenAILLMService`
- Support for 500+ models through unified Anannas AI gateway
- OpenAI-compatible interface for seamless integration
- Function calling example demonstrating voice conversation with tool use
- Comprehensive documentation and usage examples
- PyPI package distribution as `pipecat-anannas`

### Features
- Streaming responses support
- Function calling / tool use support
- Context management
- Built-in observability (cache analytics, token metrics, function call analytics)
- BYOK (Bring Your Own Key) support for enterprise
- ~0.48ms overhead with smart routing

### Documentation
- Complete README with installation, usage, and examples
- Function calling example in `examples/` directory
- API documentation following Google-style docstrings
- Links to Anannas AI documentation and resources

### Compatibility
- Tested with Pipecat v0.0.86+
- Python 3.10+
- Compatible with all Pipecat features (streaming, function calling, multi-modal)

[0.1.0]: https://github.com/upsurgeio/anannas-pipecat-integration/releases/tag/v0.1.0

