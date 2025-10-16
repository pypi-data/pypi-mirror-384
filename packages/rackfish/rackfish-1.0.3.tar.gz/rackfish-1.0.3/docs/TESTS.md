# rackfish: Common Redfish Usage Test Suite

This test suite covers the most common Redfish usage scenarios for the rackfish library.

## Test Cases

- Basic resource traversal and collection iteration
- OEM and Links property surfacing
- Action invocation (e.g., Reset)
- PATCH update via attribute assignment
- Create and delete resource in a collection

## How to Run

```bash
python test_common_usage.py
```

## Expected Output

```
Test: Basic Redfish resource traversal and collection iteration
  Traversal and collection iteration: OK
Test: OEM and Links surfacing
  OEM/Links surfacing: OK
Test: Action invocation (Reset)
  Action invocation: OK
Test: PATCH update via attribute assignment
  PATCH update: OK
Test: Create and delete resource in collection
  Create/Delete: OK

All common Redfish usage tests passed!
```

## Notes
- Uses a mock RedfishClient for safe, fast, and repeatable tests
- Covers both standard and vendor-specific (OEM) Redfish extensions
- Demonstrates the ergonomic benefits of property surfacing
- See also: [EXAMPLES.md](EXAMPLES.md) for code walkthroughs and usage patterns
