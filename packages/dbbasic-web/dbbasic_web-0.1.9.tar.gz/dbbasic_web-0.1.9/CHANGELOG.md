# Changelog

All notable changes to dbbasic-web will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-10-12

### Added
- Initial release of dbbasic-web
- Filesystem-based routing (no route tables or decorators)
- Hierarchical API handlers (one file handles multiple sub-routes)
- Integration with dbbasic-tsv for TSV-based storage
- Integration with dbbasic-queue for background jobs
- Integration with dbbasic-pipe for message bus
- Integration with dbbasic-sessions for authentication
- Built-in WebSocket support with room management
- Server-Sent Events (SSE) support
- Jinja2 template rendering
- Static file serving
- Flat-file storage helpers
- ASGI application with uvicorn
- CLI commands: serve, worker, shell, init
- Example API handlers (hello.py, user.py)
- Comprehensive documentation in README.md

### Performance
- ~4000 requests/second (40x faster than traditional CGI)
- Direct module imports without middleware overhead
- Efficient filesystem-based routing

### Philosophy
- Restores Unix principles lost in modern web frameworks
- No Redis or SQL database required
- TSV files for storage, queues, and streams
- Each module under 500 lines of code
- Total framework ~8000 lines vs 200k+ for Django

[0.1.0]: https://github.com/dbbasic/dbbasic-web/releases/tag/v0.1.0
