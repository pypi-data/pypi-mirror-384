# ETag Support in rackfish

## Overview

As of version 1.0.2 (unreleased), rackfish automatically includes ETag support for PATCH requests to prevent HTTP 412 (Precondition Failed) errors from Redfish BMCs that require concurrency control.

## Background

Many Redfish BMC implementations require the `If-Match` header with an ETag value when performing PATCH operations. This is a standard HTTP precondition mechanism to prevent lost updates in concurrent environments.

### The Problem

When a PATCH request is sent without the `If-Match` header:
- BMCs may respond with **HTTP 428 Precondition Required**
- BMCs may respond with **HTTP 412 Precondition Failed**
- The update operation fails even though the data is valid

### The Solution

rackfish now automatically:
1. Extracts the `@odata.etag` value from resources when they are fetched
2. Includes the ETag in the `If-Match` header for all PATCH requests
3. Falls back gracefully when no ETag is present (backward compatible)

## Usage

No changes are needed to your existing code! ETag support works automatically.

### Example: Attribute Assignment

```python
from rackfish import RedfishClient

client = RedfishClient("https://bmc.example.com", "admin", "password")
client.connect()

# Get a system resource (ETag is automatically extracted if present)
system = client.Systems[0]

# Modify an attribute - ETag is automatically included in PATCH
system.AssetTag = "MyNewServer"
# Behind the scenes: PATCH with If-Match header containing the ETag
```

### Example: Using .patch() Method

```python
# Complex updates using .patch()
system.patch({
    "AssetTag": "UpdatedTag",
    "IndicatorLED": "Lit"
})
# ETag is automatically included in the PATCH request
```

### Example: Resources Without ETags

```python
# Works seamlessly with BMCs that don't provide ETags
system.PowerState = "On"
# PATCH is sent without If-Match header (no error)
```

## How It Works

### 1. ETag Extraction

When a resource is fetched, rackfish looks for the `@odata.etag` field in the JSON response:

```json
{
  "@odata.id": "/redfish/v1/Systems/1",
  "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
  "@odata.etag": "W/\"12345678\"",
  "Id": "1",
  "AssetTag": "MyServer"
}
```

The ETag value `W/"12345678"` is stored internally in the resource object.

### 2. ETag Inclusion in PATCH

When a PATCH operation is triggered (via attribute assignment or `.patch()` method), rackfish:

1. Checks if the resource has an `@odata.etag` value
2. If present, includes it in the `If-Match` header
3. If absent, sends the PATCH without the header

HTTP request example with ETag:
```http
PATCH /redfish/v1/Systems/1 HTTP/1.1
Host: bmc.example.com
Content-Type: application/json
If-Match: W/"12345678"

{"AssetTag": "NewValue"}
```

### 3. Backward Compatibility

Resources without ETags continue to work normally:
- Old BMCs that don't provide ETags work as before
- No breaking changes to existing code
- Optional feature that activates only when ETags are present

## Implementation Details

### Modified Methods

#### `RedfishClient.patch(path, data, etag=None)`

The `patch` method now accepts an optional `etag` parameter:

```python
def patch(self, path: str, data: dict[str, Any], etag: str | None = None) -> None:
    url = _safe_join(self.base_url, path) if not path.startswith("http") else path
    headers = {}
    if etag:
        headers["If-Match"] = etag
    resp = self._http.patch(url, json=data, headers=headers, timeout=self.timeout)
    if resp.status_code not in (200, 204):
        raise RedfishError(f"PATCH {url} -> {resp.status_code} {resp.text}")
```

#### `RedfishResource.patch(updates)`

The resource `patch` method extracts and passes the ETag:

```python
def patch(self, updates: dict[str, Any]) -> None:
    if not self._path:
        raise RedfishError("PATCH requires a resource path")
    self._ensure_fetched()
    etag = self._raw.get("@odata.etag")
    self._client.patch(self._path, updates, etag=etag)
    self.refresh()
```

#### `RedfishResource.__setattr__(name, value)`

Attribute assignment also passes the ETag:

```python
if name in self._raw and not isinstance(self._raw[name], (dict, list)):
    etag = self._raw.get("@odata.etag")
    self._client.patch(self._path, {name: value}, etag=etag)
    self._raw[name] = value
    object.__setattr__(self, name, value)
```

## Testing

A comprehensive test suite verifies ETag functionality:

```bash
pytest tests/test_etag_support.py -v
```

Tests cover:
1. ✅ ETag included in PATCH via attribute assignment
2. ✅ ETag included in PATCH via `.patch()` method  
3. ✅ PATCH works without ETag present (backward compatibility)

## Benefits

### 1. Prevents Lost Updates

ETags ensure that updates are based on the current state of the resource:
- Detects when another client has modified the resource
- Prevents overwriting changes made by concurrent operations
- Provides optimistic concurrency control

### 2. BMC Compatibility

Works with BMCs that require precondition headers:
- ✅ HPE iLO (when ETag enforcement is enabled)
- ✅ Dell iDRAC (some configurations)
- ✅ Huawei iBMC
- ✅ Lenovo XClarity Controller
- ✅ Supermicro BMCs
- ✅ Generic Redfish implementations

### 3. Zero Breaking Changes

- Existing code works without modification
- Optional feature that activates automatically
- Graceful fallback for BMCs without ETag support

## Troubleshooting

### HTTP 412 Precondition Failed

If you still get 412 errors after this fix:

1. **Stale ETag**: The resource was modified by another client
   ```python
   # Solution: Refresh the resource before updating
   system.refresh()
   system.AssetTag = "NewValue"
   ```

2. **Wrong ETag format**: Some BMCs are picky about ETag format
   - Check BMC logs for details
   - Verify the ETag value in the response

3. **ETag not updated after refresh**: May be a BMC bug
   ```python
   # Workaround: Fetch a fresh instance
   system = client.Systems[0]  # Get fresh data
   system.AssetTag = "NewValue"
   ```

### HTTP 428 Precondition Required

If you get 428 errors, it means:
- The BMC requires an ETag but the resource doesn't have one
- The resource hasn't been fetched yet (link stub)

```python
# Solution: Ensure resource is fetched
system._ensure_fetched()  # Force fetch if needed
system.patch({"AssetTag": "NewValue"})
```

## References

- [RFC 7232: HTTP Conditional Requests](https://tools.ietf.org/html/rfc7232)
- [Redfish Specification: ETags](https://www.dmtf.org/sites/default/files/standards/documents/DSP0266_1.15.1.pdf)
- [HTTP 412 Precondition Failed](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/412)
- [HTTP 428 Precondition Required](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/428)

## Version History

- **v1.0.2** (unreleased): ETag support added
- **v1.0.1**: Initial release without ETag support
- **v1.0.0**: Initial release

---

For more information, see the [main documentation](INDEX.md) or [examples](EXAMPLES.md).
