# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-01-21

### Added
- Initial release of MLflow Descope Auth plugin
- Flow-based authentication using Descope web component
- Session validation middleware with auto-refresh
- User store adapter for MLflow integration
- Permission mapping (Descope roles → MLflow permissions)
- Configuration via environment variables
- Login/logout routes
- Health check endpoint
- Comprehensive test suite (>80% coverage)
- Documentation (README, Quickstart, examples)
- Docker Compose examples
- Type hints throughout codebase

### Features
- Support for any Descope Flow (OAuth, SAML, Magic Link, OTP, etc.)
- Automatic token refresh
- Admin role configuration
- Customizable permission mapping
- Secure cookie-based session management
- FastAPI-based implementation
- MLflow plugin system integration

### Documentation
- Complete README with setup instructions
- Quickstart guide
- Docker deployment examples
- Code examples (basic and custom config)
- Contributing guidelines
- License (Apache 2.0)

[0.1.0]: https://github.com/descope/mlflow-descope-auth/releases/tag/v0.1.0
