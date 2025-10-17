# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Planned
- Add more comprehensive examples
- Add retry logic for API calls
- Add streaming support

## [0.1.0] - 2025-10-16

### Added
- Initial release of `openai-without-pydantic`
- Core `ask_ai_question()` function for OpenAI API calls
- Direct HTTP requests using `requests` library (no OpenAI SDK)
- Zero Pydantic dependencies
- Support for all OpenAI chat models (GPT-4, GPT-4o, GPT-3.5, etc.)
- Configurable parameters:
  - `model`: Choose which OpenAI model to use
  - `temperature`: Control response randomness (0-2)
  - `max_tokens`: Limit response length
  - `timeout`: Configure request timeout
- Environment variable support:
  - `OPENAI_API_KEY`: API authentication
  - `OPENAI_MODEL`: Default model selection
  - `OPENAI_TEMPERATURE`: Default temperature setting
- Comprehensive error handling
- Type hints for better IDE support
- Cross-platform support (Windows, Linux, macOS)
- MIT License

### Documentation
- Complete README with usage examples
- Publishing guide for PyPI
- Example code in `main.py`
- Cross-platform setup instructions

[Unreleased]: https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/DeveloperAlex/pypi_OpenAI_Without_Pydantic/releases/tag/v0.1.0
