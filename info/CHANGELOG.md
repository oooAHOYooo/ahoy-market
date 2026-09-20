# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Desktop packaging with PyInstaller
- GitHub Actions workflow for automated releases
- Cross-platform builds (macOS, Windows, Linux)
- Downloads page auto-refresh functionality

### Changed
- Consolidated password hashing to bcrypt with legacy SHA-256 migration
- Enhanced security headers and CSRF protection
- Improved rate limiting with environment-driven configuration

### Fixed
- Structured logging implementation
- Health check endpoints with version information
- Request ID propagation across all logs

### Security
- Added Content Security Policy (CSP) headers
- Implemented CSRF token validation
- Enhanced session security with secure cookies
- Added Sentry error tracking integration

## [1.0.6] - 2026-04-22

### Added
- Shared radio manifest endpoint at `GET /api/radio/live`
- Shared client composable for live radio timeline math across home and `/radio`
- Explicit `playbackSource` handling in the player store for radio vs on-demand playback
- Compact `/radio` hero layout with live song info, station timing, and ambient owl world framing
- Radio-specific documentation covering manifest architecture and current UX rules

### Changed
- Refactored `/radio` out of the full-screen takeover and back into the normal app shell
- Kept the bottom dock visible and usable while radio is open
- Changed radio controls from play/pause semantics to `tune in / mute / unmute`
- Moved home and radio page station state to the same source of truth
- Simplified radio mode in the mini-player so it behaves like live radio instead of a queue player

### Fixed
- Removed radio mode `next`, `previous`, shuffle, repeat, and queue controls
- Added an explicit `Back To Live Radio` recovery action on the radio page after on-demand override
- Removed redundant mini-player radio navigation that conflicted with the bottom dock
- Fixed duplicate radio playback start behavior when joining the station

### Notes
- The station timeline now keeps moving even when the user is not actively listening
- On-demand playback is still allowed to override radio, but radio can rejoin the current live point
- The owl/game layer is still ambient v1 polish, not a finished social or world-building system

## [0.1.0] - 2024-12-19

### Added
- Desktop packaging with PyInstaller for macOS, Windows, and Linux
- Security headers middleware with CSP and HSTS
- Bcrypt password hashing with automatic legacy SHA-256 migration
- CSRF protection with JSON error handling
- Environment-driven rate limiting configuration
- Sentry error tracking integration
- Comprehensive smoke test suite
- Render deployment validation script
- GitHub Actions workflow for automated desktop app releases
- Downloads page with auto-refresh functionality
- Release drafter for automated changelog generation

### Changed
- Unified password hashing across all authentication endpoints
- Enhanced logging with structured JSON output in production
- Improved health check endpoints with version information
- Consolidated security configuration

### Fixed
- Request ID propagation in all log entries
- Rate limiting exemptions for media endpoints
- CSRF token validation for API endpoints
- Database connection handling in health checks

### Security
- Added comprehensive security headers (X-Content-Type-Options, X-Frame-Options, etc.)
- Implemented Content Security Policy with violation reporting
- Enhanced session security with secure cookie settings
- Added Sentry integration for production error tracking
- Consolidated authentication with bcrypt password hashing
