# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.0.3] - 2025-10-15

### Added

- Singular collection access: Access single-member collections directly (e.g., `client.System` instead of `next(iter(client.Systems))`)
- Works at all resource hierarchy levels (client and nested resources)
- Automatic fallback to traditional methods when collection doesn't have exactly one member
- Comprehensive test suite for singular access (`test_singular_collection_access.py`)
- Documentation for singular collection access feature
- New test suite for ETag functionality (`test_etag_support.py`)

### Fixed

- Added ETag support for PATCH requests via If-Match header to prevent HTTP 412 errors
- PATCH operations now automatically include ETags when available in resource metadata
- Resources without ETags continue to work normally (backward compatible)
- Suppressed urllib3 InsecureRequestWarning when `verify_ssl=False` is used

## [1.0.1] - 2025-10-15

### Fixed

- Updated version metadata for proper PyPI package versioning
- Corrected git tag alignment with actual version numbers

### Changed

- Improved release process documentation
- Enhanced version consistency across project files

## [1.0.0] - 2025-10-15

### Added

- Initial release of rackfish
- Dynamic Redfish client with lazy loading
- Automatic OEM and Links property surfacing
- Action method binding with ActionInfo validation
- Collection iteration support
- Session and basic authentication
- Support for 150+ common Redfish operations
- Comprehensive documentation and examples
- Full test suite with 100% passing tests
- Support for Huawei, Dell, HPE, Lenovo, Supermicro and all Redfish-compliant BMCs

### Features

- Zero external dependencies (except `requests`)
- Lazy resource fetching for performance
- Dynamic attribute mapping from JSON
- Collision-safe OEM/Links surfacing
- Type-safe action parameter validation
- Pythonic API with natural dot notation
- Thread-safe HTTP session management
- Recursion guard for deeply nested structures

### Documentation

- Complete API documentation
- 150+ usage examples
- Use case index
- Test suite documentation
- Comprehensive README
- GitHub/PyPI ready structure

[1.0.1]: https://github.com/thefrolov/rackfish/releases/tag/v1.0.1
[1.0.0]: https://github.com/thefrolov/rackfish/releases/tag/v1.0.0
