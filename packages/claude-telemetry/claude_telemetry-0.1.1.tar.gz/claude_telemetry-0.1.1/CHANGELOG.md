# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and
this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Initial public release! 🎉
- OpenTelemetry instrumentation for Claude agents
- Comprehensive telemetry capture (prompts, tool calls, tokens, costs)
- Logfire integration with LLM-specific UI features
- Support for any OTEL-compatible backend
- CLI tool (`claudia`) for quick agent execution
- Interactive and non-interactive agent modes
- MCP server support (HTTP and stdio)
- Comprehensive test suite
- Pre-commit hooks for code quality
- CI/CD pipeline with GitHub Actions

### Features

- 🤖 Captures every prompt, tool call, token count, and cost as structured OTEL spans
- 📊 Works with Logfire, Datadog, Honeycomb, Grafana, and any OTEL collector
- 🔧 Hook-based telemetry (no monkey-patching required)
- 💡 Enhanced Logfire features with LLM-specific UI tagging
- 🎨 Beautiful console output with emoji indicators
- ⚡ Async-first API with sync convenience wrappers
- 🔌 Extensible and maintainable architecture

## Release History

<!-- Versions will be added here as they are released -->

---

**Note**: This project uses [setuptools-scm](https://github.com/pypa/setuptools-scm) for
automatic version management from git tags.
