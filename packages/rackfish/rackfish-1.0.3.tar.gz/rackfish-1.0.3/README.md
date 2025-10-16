# rackfish - Dynamic Redfish Client

[![PyPI version](https://img.shields.io/pypi/v/rackfish.svg)](https://pypi.org/project/rackfish/)
[![Python Versions](https://img.shields.io/pypi/pyversions/rackfish.svg)](https://pypi.org/project/rackfish/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://github.com/thefrolov/rackfish/workflows/CI/badge.svg)](https://github.com/thefrolov/rackfish/actions)
[![codecov](https://codecov.io/gh/thefrolov/rackfish/branch/main/graph/badge.svg)](https://codecov.io/gh/thefrolov/rackfish)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

A lightweight, dynamic Python client for interacting with Redfish BMC (Baseboard Management Controller) APIs. Provides intuitive access to server hardware management through lazy-loaded object graphs, automatic OEM property surfacing, and validated action invocation.

## 🎯 Why rackfish?

- 🚀 **Zero Dependencies** (except `requests`) - Minimal footprint
- ⚡ **Lazy Loading** - Resources fetched on-demand for performance
- 🎨 **Pythonic Interface** - JSON properties become Python attributes
- 🔧 **OEM Support** - Vendor extensions (Huawei, Dell, HPE) automatically accessible
- 🔗 **Smart Navigation** - Related resources directly navigable via Links
- ✅ **Action Validation** - Parameter validation using ActionInfo schemas
- 📚 **Collection Support** - Iterate Redfish collections naturally
- 🔐 **Flexible Auth** - Session tokens or Basic authentication

## Installation

### From PyPI (recommended)

```bash
pip install rackfish
```

### From source

```bash
git clone https://github.com/thefrolov/rackfish.git
cd rackfish
pip install -e .
```

### Development installation

```bash
pip install -e ".[dev]"
```

## Quick Start

```python
from rackfish import RedfishClient

# Connect to BMC
client = RedfishClient("https://bmc.example.com", "admin", "password", 
                       use_session=True, verify_ssl=False)
root = client.connect()

# Power control - multiple ways to access systems
system = next(iter(client.Systems))  # Traditional iteration
system = client.Systems.Members[0]    # Direct member access
system = client.System                # Singular form (if only one member!)

system.Reset(ResetType="GracefulRestart")

# Access OEM properties (auto-surfaced)
if hasattr(system, "BootMode"):
    print(f"Boot Mode: {system.BootMode}")

# Navigate linked resources
for chassis in system.Chassis:
    print(f"Chassis: {chassis.Name}")

# Logout
client.logout()
```

## Documentation

- **[docs/EXAMPLES.md](docs/EXAMPLES.md)** - Comprehensive usage examples for all common Redfish operations
- **[docs/USE_CASES.md](docs/USE_CASES.md)** - Complete index of 150+ supported use cases
- **[docs/OEM_LINKS_SURFACING.md](docs/OEM_LINKS_SURFACING.md)** - Details on automatic OEM and Links surfacing
- **[docs/TESTS.md](docs/TESTS.md)** - Test suite documentation
- **[docs/INDEX.md](docs/INDEX.md)** - Master navigation document
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - How to contribute

## Common Use Cases

### User Management
```python
accounts = client.AccountService.Accounts
new_user = accounts.create({"UserName": "operator", "Password": "pass", "RoleId": "Operator"})
new_user.RoleId = "Administrator"
new_user.delete()
```

### Storage Management
```python
storage = next(iter(client.Systems)).Storage[0]
volume = storage.Volumes.create({"Name": "DataVol", "CapacityBytes": 500*1024**3})
```

### Network Configuration
```python
port = client.Managers[0].EthernetInterfaces[0]
port.patch({"IPv4Addresses": [{"Address": "192.168.1.100", "SubnetMask": "255.255.255.0"}]})
```

### Event Subscriptions
```python
subs = client.EventService.Subscriptions
sub = subs.create({"Destination": "https://listener/events", "EventTypes": ["Alert"]})
```

### Firmware Updates
```python
client.UpdateService.SimpleUpdate(ImageURI="http://server/fw.bin", TransferProtocol="HTTP")
```

### System Health Monitoring
```python
for temp in chassis.Thermal.Temperatures:
    print(f"{temp.Name}: {temp.ReadingCelsius}°C")
```

See [docs/EXAMPLES.md](docs/EXAMPLES.md) for 100+ more examples covering:

- BIOS configuration
- Certificate management
- Virtual media (KVM)
- LDAP authentication
- Boot order configuration
- SEL/log collection
- And much more...

## Project Structure

```
rackfish/
├── rackfish/          # Main package
│   ├── __init__.py       # Package initialization
│   └── client.py         # Core library implementation
├── tests/                # Test suite
│   ├── __init__.py
│   ├── test_common_usage.py
│   ├── test_oem_links_surfacing.py
│   └── test_recursion_fix.py
├── examples/             # Usage examples
│   ├── examples_comprehensive.py
│   ├── demo_surfacing_comprehensive.py
│   └── example_oem_links.py
├── docs/                 # Documentation
│   ├── INDEX.md
│   ├── EXAMPLES.md
│   ├── USE_CASES.md
│   ├── TESTS.md
│   ├── OEM_LINKS_SURFACING.md
│   └── COMPLETION_SUMMARY.md
├── .github/
│   └── copilot-instructions.md
├── README.md
├── CHANGELOG.md
├── CONTRIBUTING.md
├── LICENSE
├── pyproject.toml
└── requirements.txt
```

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Architecture

### Core Components

- **`RedfishClient`** - HTTP session management, authentication, base URL handling
- **`RedfishResource`** - Dynamic resource representation with lazy loading
- **`_convert`** - Recursive JSON-to-object mapping with link stub creation
- **`_hydrate`** - Property mapping, OEM/Links surfacing, action binding

### Key Design Patterns

1. **Lazy Loading** - Link stubs defer fetching until attribute access
2. **OEM Surfacing** - Vendor properties promoted to main object (collision-safe)
3. **Links Surfacing** - Related resources directly accessible (collision-safe)
4. **Action Methods** - Redfish Actions bound as callable instance methods
5. **ActionInfo Validation** - Parameter schemas fetched and enforced

### Recursion Guard

Deeply nested JSON structures are handled safely by deferring hydration (`fetched=False`) for all embedded resources, preventing stack overflow.

## Supported Use Cases

The library supports **150+ common Redfish operations** including:

### System Management
- Power control (Reset, ForceOff, GracefulRestart)
- Boot order configuration
- System health monitoring

### Storage
- Logical drive creation/deletion
- Storage controller management
- Drive inventory and status

### Network
- IP configuration (IPv4/IPv6)
- VLAN management
- DNS/NTP configuration
- SNMP trap configuration

### User & Security
- User account CRUD
- Role assignment
- Password policies
- LDAP integration

### Certificates
- CSR generation
- SSL/TLS certificate import
- SSH public key management
- Two-factor authentication certs

### Firmware & BIOS
- Firmware updates
- BIOS configuration
- BMC reset/rollback

### Monitoring & Logs
- Temperature sensors
- Fan speeds
- Voltage readings
- System event logs (SEL)

### Virtual Media
- ISO mounting (KVM)
- VNC/KVM configuration
- Virtual media operations

See [EXAMPLES.md](EXAMPLES.md) for complete list and code samples.

## OEM Vendor Support

Works with any Redfish-compliant BMC including:

- **Huawei** - TaiShan servers, FruControl, custom boot modes
- **Dell** - iDRAC, DellAttributes
- **HPE** - iLO, HPE-specific extensions
- **Lenovo** - XClarity
- **Supermicro** - IPMI/Redfish hybrid
- And any other vendor implementing Redfish standard

OEM extensions are automatically surfaced to the main object for easy access.

## Advanced Features

### Generic Request Helpers

For operations not exposed as methods:

```python
response = client.get("/redfish/v1/custom/path")
client.post("/redfish/v1/Actions/Custom", data={"param": "value"})
client.patch("/redfish/v1/Systems/1", data={"AssetTag": "NEW"})
client.delete("/redfish/v1/Collection/Item")
```

### Allowable Values

Get valid parameter values:

```python
reset_types = system.get_allowable_values("ResetType")
print(f"Valid reset types: {reset_types}")
```

### Raw JSON Access

```python
raw_data = resource.to_dict()
```

## Contributing

See `.github/copilot-instructions.md` for development guidelines and architecture details.

## License

See LICENSE file.

## Version

Current version: 1.0.3

## Requirements

- Python 3.8+
- requests library

## Support

For issues, questions, or contributions, please refer to the project repository.
