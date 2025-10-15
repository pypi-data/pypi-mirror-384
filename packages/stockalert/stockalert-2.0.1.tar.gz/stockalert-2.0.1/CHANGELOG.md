# Changelog

All notable changes to the StockAlert Python SDK will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.1] - 2025-10-14

### Fixed
- **Critical**: Fixed duplicate `/api/v1` in API endpoint paths
  - All endpoints now use correct relative paths (`/alerts` instead of `/api/v1/alerts`)
  - Prevents 404 errors from malformed URLs like `https://stockalert.pro/api/v1/api/v1/alerts`
  - Affected 10 endpoints: list, create, get, update, pause, activate, delete, history, stats, verify
- **Type Safety**: Updated `pause()` and `activate()` return types
  - Changed from `Alert` to `Dict[str, Any]` to match API response format
  - API returns `{alertId, status}` instead of full Alert object
  - Updated CLI commands to handle new response format
- **Validation**: Corrected `earnings_announcement` threshold requirement
  - Moved from `no_threshold` to `requires_threshold` list
  - Aligns with v1 API requirement (threshold = days before event)

### Added
- Comprehensive live test suite (`test_sdk_live.py`)
  - 22 test cases covering all SDK functionality
  - Tests authentication, CRUD operations, pagination, error handling
  - Automatic cleanup of test data
  - 95.5% success rate (21/22 passing)
- Detailed test documentation (`TEST_RESULTS.md`)
  - Performance metrics and recommendations
  - Lists all bugs found and fixed during testing

### Changed
- All linting (ruff) and type checking (mypy) errors resolved
- CI/CD pipeline now passes on all Python versions (3.8-3.12)

## [2.0.0] - 2025-01-14

### 🚀 MAJOR RELEASE: v1 API Migration

This is a major release with breaking changes due to the migration to the unified v1 API.

### Breaking Changes

#### API Endpoint Migration
- **Base URL changed**: `/api/public/v1` → `/api/v1`
- All API responses now use v1 envelope format with `{success, data, meta}`

#### Alert Methods
- `alerts.update(alert_id, status)` method signature changed
  - **Before**: `update(alert_id, "paused")` for status changes
  - **After**: Use dedicated methods `pause(alert_id)` and `activate(alert_id)`
  - **New**: `update()` now supports partial updates of condition, threshold, notification, parameters

#### Pagination
- Changed from offset-based to page-based pagination
  - **Before**: `list(offset=0, limit=50)`
  - **After**: `list(page=1, limit=50)`

### Added

#### New Alert Methods
- `alerts.pause(alert_id)` - Pause an active alert
- `alerts.activate(alert_id)` - Reactivate a paused alert
- `alerts.history(alert_id, page, limit)` - Get alert history with pagination
- `alerts.stats()` - Get alert statistics (status counts, total)
- `alerts.verify(token)` - Verify guest alert via email token

#### New Webhook Methods
- `webhooks.get(webhook_id)` - Get webhook by ID

#### Enhanced Types
- Alert type extended with v1 fields:
  - `triggered_at` - Timestamp when alert was triggered
  - `user_id` - Owner UUID
  - `email` - Guest alert email
  - `verified` - Email verification status
  - `verification_token` - Verification token
  - `last_evaluated_at` - Last evaluation timestamp
  - `last_metric_value` - Last metric value
  - `stock` - Enriched stock data (on GET by ID)

- PaginatedResponse updated for v1 structure:
  - `meta.pagination` with page, limit, total, totalPages
  - `meta.rateLimit` with rate limit info
  - Backward compatibility maintained

### Changed

#### Validation
- `earnings_announcement` and `dividend_ex_date` now require threshold values
  - These represent "days before" the event (e.g., 7 days before earnings)

#### Webhook Signature Verification
- `verify_signature()` now supports both formats: `sha256=...` prefix and raw hex

#### Error Handling
- Enhanced error extraction from v1 API format (`error.message`)
- Improved rate limit error handling with proper message extraction
- Consistent error handling across sync and async clients

### Fixed
- Async client resource initialization (webhooks and api_keys client references)
- Rate limit error message extraction from v1 format
- Type checking issues with mypy

### Migration Guide

#### Update Method Calls
```python
# Before
client.alerts.update(alert_id, "paused")

# After
client.alerts.pause(alert_id)
client.alerts.activate(alert_id)
```

#### Update Pagination
```python
# Before
alerts = client.alerts.list(offset=0, limit=50)

# After
alerts = client.alerts.list(page=1, limit=50)
```

#### Use New Features
```python
# Get alert history
history = client.alerts.history(alert_id, page=1, limit=50)

# Get statistics
stats = client.alerts.stats()

# Partial update
client.alerts.update(alert_id, threshold=150.0, notification="email")
```

## [1.2.0] - 2024-01-07

### Added
- CLI tool for command-line usage (`stockalert` command)
- GitHub issue and PR templates
- Contributing guidelines
- Code of Conduct
- Pre-commit hooks for code quality
- Support for all alert operations via CLI

### Features
- List, create, get, update, and delete alerts from command line
- JSON output format for scripting
- Environment variable support for API key
- Interactive confirmations for destructive operations

## [1.1.1] - 2024-01-07

### Added
- CHANGELOG.md to track version history
- Enhanced README with more examples
- py.typed for PEP 561 compliance
- Logging module with configurable levels
- More tests (coverage increased to 46.71%)

- Comprehensive test suite

### Features
- Create, read, update, and delete alerts
- List alerts with filtering and pagination
- Webhook management
- API key management (coming soon)
- Support for all notification channels (email, SMS)

[1.1.0]: https://github.com/stockalert-pro/python-sdk/releases/tag/v1.1.0
