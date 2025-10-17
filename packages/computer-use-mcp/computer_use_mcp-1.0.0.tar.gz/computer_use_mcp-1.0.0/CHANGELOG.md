# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-17

### Added
- Initial production-ready release
- **7 MCP Tools**:
  - `browse_web` - Synchronous web browsing with immediate completion
  - `start_web_task` - Start background browsing tasks
  - `check_web_task` - Monitor task progress with compact & full modes
  - `wait` - Pause execution (1-60 seconds) for rate limiting
  - `stop_web_task` - Cancel running background tasks
  - `list_web_tasks` - View all tasks and their status
  - `get_web_screenshots` - Retrieve session screenshots
- **Progress Tracking**: Real-time monitoring with compact mode (90% size reduction)
- **Safety Framework**: Proper acknowledgment of Gemini safety decisions
- **Context-Aware Polling**: Built-in rate limiting with recommended delay timestamps
- **Performance Optimizations**: 4-5x faster than baseline implementations
- **Screenshot Capture**: Automatic screenshots of each browsing step
- **MCP Protocol Compliance**: Follows 2025 best practices
- **Comprehensive Documentation**: README, LICENSE, examples, and best practices

### Changed
- Renamed tools from developer-centric to user-friendly names
- Updated tool descriptions to follow MCP best practices
- Improved error handling and response formats

### Fixed
- Safety decision acknowledgment (resolves 400 INVALID_ARGUMENT error)
- Safety decision extraction from function_call instead of content.parts
- Context window bloat with compact progress mode

### Performance
- Conditional wait states (0.3-3s vs 6s per action)
- Fast page loads (`domcontentloaded` vs `networkidle`)
- Single screenshot per turn (eliminates duplicates)
- Parallel function execution for batch operations
- Optimized for 1440x900 resolution (Gemini recommendation)

### Security
- Safety decision framework implementation
- Environment-based API key configuration
- Comprehensive logging for audit trails
- Screenshot-based verification capability

## [Unreleased]

### Planned Features
- Human-in-the-loop confirmation UI
- Domain allowlist/blocklist for navigation
- Retry logic with exponential backoff
- Cookie and session management
- Form auto-fill templates
- Multi-tab support
- Mobile viewport emulation
- Proxy support

---

[1.0.0]: https://github.com/yourusername/gemini-web-automation-mcp/releases/tag/v1.0.0
