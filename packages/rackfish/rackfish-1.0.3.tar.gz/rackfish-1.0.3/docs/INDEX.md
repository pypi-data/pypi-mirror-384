# rackfish Documentation Index

Complete documentation for the rackfish dynamic Redfish client library.

## 📚 Documentation Files

### Getting Started

- **[../README.md](../README.md)** - Main documentation, installation, quick start, and overview
  - Features and benefits
  - Quick start examples
  - Architecture overview
  - Supported vendors

### Usage Examples

- **[EXAMPLES.md](EXAMPLES.md)** - Comprehensive code examples for 150+ Redfish operations
  - User management (create, delete, update)
  - Storage and logical drives
  - BIOS and firmware management
  - Certificate and security operations
  - Power control and FRU management
  - Network configuration (IP, DNS, NTP, VLAN)
  - System health monitoring
  - Event subscriptions
  - Virtual media (KVM/VMM)
  - LDAP configuration
  - And much more...

- **[USE_CASES.md](USE_CASES.md)** - Complete index of all supported use cases
  - Organized by category
  - Quick reference table with function names
  - Maps original function names to rackfish patterns

### Advanced Topics

- **[OEM_LINKS_SURFACING.md](OEM_LINKS_SURFACING.md)** - Details on automatic OEM and Links surfacing
  - How vendor extensions are surfaced
  - Collision avoidance mechanism
  - Before/after code comparisons
  - Benefits and backward compatibility

- **[SINGULAR_COLLECTION_ACCESS.md](SINGULAR_COLLECTION_ACCESS.md)** - Singular access to single-member collections
  - Convenient `client.System` instead of `next(iter(client.Systems))`
  - Works for any collection with exactly one member
  - Best practices and error handling
  - Usage examples and limitations

- **[ETAG_SUPPORT.md](ETAG_SUPPORT.md)** - ETag support for PATCH requests
  - Automatic If-Match header inclusion
  - Prevents HTTP 412 errors
  - Usage examples and troubleshooting

- **[SSL_CONFIGURATION.md](SSL_CONFIGURATION.md)** - SSL/TLS configuration guide
  - Secure vs insecure connections
  - Self-signed certificate handling
  - Custom CA bundles
  - Best practices and troubleshooting

### Testing

- **[TESTS.md](TESTS.md)** - Test suite documentation
  - How to run tests
  - Test coverage overview
  - Expected output

## 🧪 Test Files

Located in `../tests/`:

- **test_common_usage.py** - Tests for common Redfish operations
  - Resource traversal and collection iteration
  - OEM/Links surfacing
  - Action invocation
  - PATCH updates
  - Create/delete operations

- **test_oem_links_surfacing.py** - Tests for OEM and Links surfacing
  - OEM property surfacing (Huawei, Dell vendors)
  - Links resource surfacing (Chassis, ManagedBy)
  - Collision avoidance
  - OEM action binding

- **test_recursion_fix.py** - Tests for recursion guard
  - 50-level deep nested structure handling
  - Lazy loading verification

- **test_etag_support.py** - Tests for ETag functionality
  - ETag extraction and usage
  - PATCH with If-Match header
  - Backward compatibility

- **test_singular_collection_access.py** - Tests for singular collection access
  - Single member access (success cases)
  - Multiple members (error handling)
  - Empty collections (error handling)
  - Nested collections support
  - Client-level and resource-level access

## 💻 Example Files

Located in `../examples/`:

- **examples_comprehensive.py** - Full working examples
  - Real-world usage patterns
  - User management
  - Power control
  - Storage management
  - Network configuration
  - Health monitoring
  - Log collection
  - Boot configuration
  - Virtual media
  - LDAP configuration
  - (Most write operations commented out for safety)

- **demo_surfacing_comprehensive.py** - OEM/Links surfacing demonstration
  - Mock Huawei BMC simulation
  - Before/after comparison
  - Backward compatibility verification

- **example_oem_links.py** - OEM/Links usage examples
  - Benefits demonstration
  - Navigation pattern improvements

## 🔧 Source Files

Located in `../rackfish/`:

- **client.py** - Main library implementation
  - `RedfishClient` class - HTTP client and session management
  - `RedfishResource` class - Dynamic resource object graph
  - Lazy loading mechanism
  - OEM/Links surfacing logic
  - Action binding and validation

## 📋 Configuration Files

- `../requirements.txt` - Python dependencies (only `requests`)
- `../pyproject.toml` - Project configuration and metadata

## 🤖 AI Agent Instructions

- **[../.github/copilot-instructions.md](../.github/copilot-instructions.md)** - Guidelines for AI coding agents
  - Architecture details
  - Design patterns
  - Extension guidelines
  - Common pitfalls

## 🚀 Quick Navigation by Task

### Common Tasks

#### Learn the basics

→ Start with [../README.md](../README.md)

#### See code examples

→ Go to [EXAMPLES.md](EXAMPLES.md)

#### Find a specific use case

→ Check [USE_CASES.md](USE_CASES.md) index

#### Understand OEM surfacing

→ Read [OEM_LINKS_SURFACING.md](OEM_LINKS_SURFACING.md)

#### Configure SSL/TLS

→ See [SSL_CONFIGURATION.md](SSL_CONFIGURATION.md)

#### Understand ETag support

→ Read [ETAG_SUPPORT.md](ETAG_SUPPORT.md)

#### Use singular collection access

→ Read [SINGULAR_COLLECTION_ACCESS.md](SINGULAR_COLLECTION_ACCESS.md)

#### Run tests

→ See [TESTS.md](TESTS.md)

#### Write real code

→ Look at `../examples/examples_comprehensive.py`

#### Understand architecture

→ Read [../.github/copilot-instructions.md](../.github/copilot-instructions.md)

## 📊 Coverage Summary

### Supported Operations: 150+

- ✅ User management (10+ operations)
- ✅ Event subscriptions (3 operations)
- ✅ Storage & logical drives (15+ operations)
- ✅ BIOS & firmware (15+ operations)
- ✅ Certificates & security (20+ operations)
- ✅ Power & FRU control (8+ operations)
- ✅ Storage Processor (SP) (15+ operations)
- ✅ Network & VLAN (20+ operations)
- ✅ System health & sensors (25+ operations)
- ✅ Sessions & authentication (2 operations)
- ✅ Logs (SEL) (3 operations)
- ✅ KVM, VMM, VNC (10+ operations)
- ✅ LDAP (4 operations)
- ✅ Miscellaneous (20+ operations)

## 🏆 Key Features

1. **Zero Config** - Works with any Redfish-compliant BMC
2. **Lazy Loading** - Fast and memory-efficient
3. **OEM Surfacing** - Vendor extensions automatically accessible
4. **Type Safe** - Action parameter validation
5. **Pythonic** - Natural dot notation for navigation
6. **Well Tested** - Comprehensive test coverage
7. **Documented** - 150+ examples and detailed docs

## 📝 Contributing

See [../.github/copilot-instructions.md](../.github/copilot-instructions.md) for:

- Code architecture
- Extension guidelines
- Design patterns
- Testing approach

## 🔗 Related Files

- `../CHANGELOG.md` - Version history and changes
- `../CONTRIBUTING.md` - Contribution guidelines
- `../LICENSE` - MIT License
- `.python-version` - Python version specification

---

**Last Updated:** October 15, 2025

**Version:** 1.0.3

**Supported Python:** 3.8+

**Dependencies:** requests only
