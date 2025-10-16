# SSL/TLS Configuration

## Overview

rackfish provides flexible SSL/TLS configuration options for connecting to Redfish BMCs, including support for self-signed certificates and insecure connections.

## SSL Verification

By default, rackfish verifies SSL certificates to ensure secure connections. However, many BMCs use self-signed certificates, which can cause connection failures.

### Secure Connection (Default)

```python
from rackfish import RedfishClient

# Default: SSL verification enabled
client = RedfishClient(
    "https://bmc.example.com",
    "admin",
    "password",
    verify_ssl=True  # Default
)
```

### Insecure Connection (Self-Signed Certificates)

When working with BMCs that use self-signed certificates, you can disable SSL verification:

```python
from rackfish import RedfishClient

# Disable SSL verification for self-signed certificates
client = RedfishClient(
    "https://bmc.example.com",
    "admin",
    "password",
    verify_ssl=False  # Disable SSL verification
)
```

**Important**: When `verify_ssl=False` is set, rackfish automatically suppresses urllib3 `InsecureRequestWarning` messages to keep your logs clean. This prevents warnings like:

```
InsecureRequestWarning: Unverified HTTPS request is being made to host 'bmc.example.com'.
Adding certificate verification is strongly advised.
```

## Security Considerations

### Production Environments

For production environments, it's recommended to:

1. **Use proper CA-signed certificates** on your BMCs when possible
2. **Add BMC certificates to your trust store** instead of disabling verification
3. **Use certificate pinning** for additional security

### Development/Lab Environments

In development or lab environments with self-signed certificates:

- ✅ Using `verify_ssl=False` is acceptable
- ✅ Warnings are automatically suppressed for cleaner logs
- ⚠️ Be aware that man-in-the-middle attacks are possible

## Custom Certificate Verification

If you want to verify against a specific CA certificate or certificate bundle:

```python
from rackfish import RedfishClient

# Verify using custom CA bundle
client = RedfishClient(
    "https://bmc.example.com",
    "admin",
    "password",
    verify_ssl=True  # Enable verification
)

# You can also set a custom CA bundle path after initialization
client._http.verify = "/path/to/ca-bundle.crt"
```

## Common Scenarios

### Scenario 1: Lab Environment with Self-Signed Certs

```python
# Quick setup for testing - no warnings
client = RedfishClient(
    "https://192.168.1.100",
    "admin",
    "password",
    verify_ssl=False
)
root = client.connect()
```

### Scenario 2: Production with Proper Certificates

```python
# Production setup with full SSL verification
client = RedfishClient(
    "https://bmc.datacenter.company.com",
    "admin",
    "password",
    verify_ssl=True
)
root = client.connect()
```

### Scenario 3: Custom CA Bundle

```python
import os

client = RedfishClient(
    "https://bmc.example.com",
    "admin",
    "password",
    verify_ssl=True
)

# Point to custom CA bundle
ca_bundle = os.path.join(os.path.dirname(__file__), "certs", "ca-bundle.crt")
client._http.verify = ca_bundle

root = client.connect()
```

## Troubleshooting

### SSL: CERTIFICATE_VERIFY_FAILED

If you see this error:
```
ssl.SSLError: [SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed
```

**Solutions:**

1. **Disable verification** (development only):
   ```python
   client = RedfishClient(..., verify_ssl=False)
   ```

2. **Install BMC certificate** in your system's trust store

3. **Use custom CA bundle**:
   ```python
   client._http.verify = "/path/to/ca-bundle.crt"
   ```

### Connection Refused / Timeout

If you can't connect at all:

1. Check BMC IP address and network connectivity
2. Verify the BMC web interface is accessible
3. Ensure firewall rules allow HTTPS traffic
4. Try connecting with `curl` or a browser first

### Certificate Hostname Mismatch

If the certificate hostname doesn't match:

```python
# Option 1: Use the correct hostname from the certificate
client = RedfishClient("https://bmc-cert-hostname.example.com", ...)

# Option 2: Disable verification (not recommended for production)
client = RedfishClient(..., verify_ssl=False)
```

## Best Practices

### ✅ Do

- Use proper certificates in production
- Disable verification only in controlled lab environments
- Document why verification is disabled when used
- Consider using environment variables for SSL configuration

### ❌ Don't

- Disable SSL verification in production without understanding the risks
- Ignore certificate errors without investigation
- Store CA bundles in version control (use secure configuration management)

## Environment-Based Configuration

Example of environment-aware SSL configuration:

```python
import os
from rackfish import RedfishClient

# Read from environment
BMC_HOST = os.getenv("BMC_HOST", "https://bmc.example.com")
BMC_USER = os.getenv("BMC_USER", "admin")
BMC_PASS = os.getenv("BMC_PASS", "password")
BMC_VERIFY_SSL = os.getenv("BMC_VERIFY_SSL", "true").lower() == "true"

client = RedfishClient(
    BMC_HOST,
    BMC_USER,
    BMC_PASS,
    verify_ssl=BMC_VERIFY_SSL
)

if not BMC_VERIFY_SSL:
    print("⚠️  Warning: SSL verification is disabled")

root = client.connect()
```

## Related Documentation

- [Main Documentation](INDEX.md)
- [Examples](EXAMPLES.md)
- [ETag Support](ETAG_SUPPORT.md)

## References

- [Python Requests - SSL Cert Verification](https://requests.readthedocs.io/en/latest/user/advanced/#ssl-cert-verification)
- [urllib3 - Certificate Verification](https://urllib3.readthedocs.io/en/stable/advanced-usage.html#ssl-warnings)
- [DMTF Redfish Security](https://www.dmtf.org/sites/default/files/standards/documents/DSP0266_1.15.1.pdf)
