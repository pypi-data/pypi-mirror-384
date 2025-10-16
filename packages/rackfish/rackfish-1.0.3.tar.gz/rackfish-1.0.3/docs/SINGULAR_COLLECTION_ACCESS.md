# Singular Collection Access

## Overview

Rackfish provides a convenient shorthand for accessing single-member collections. When a collection contains exactly one member, you can access it directly using the singular form of the collection name instead of using iteration or indexing.

## Motivation

In many data center scenarios, servers have only one system, one chassis, or one manager. The traditional ways to access these require more verbose code:

```python
# Traditional methods
system = next(iter(client.Systems))         # Iteration
system = client.Systems.Members[0]          # Indexing
system = list(client.Systems)[0]            # List conversion
```

With singular access, this becomes much cleaner:

```python
# Singular access (only works if Systems has exactly 1 member)
system = client.System
```

## How It Works

When you access an attribute that doesn't exist, rackfish automatically:

1. Checks if a plural form exists (adds "s" to the name)
2. Verifies the plural form is a collection (has `__len__` and `__iter__`)
3. Checks if the collection has exactly one member (`len(collection) == 1`)
4. Returns that single member if all conditions are met
5. Raises `AttributeError` otherwise

## Usage Examples

### Basic Client-Level Access

```python
from rackfish import RedfishClient

client = RedfishClient("https://bmc", "admin", "password")
client.connect()

# If only one system exists
system = client.System  # Instead of client.Systems
print(f"System: {system.Name}")

# If only one chassis exists
chassis = client.Chassis  # Instead of client.Chassi
print(f"Chassis: {chassis.Model}")

# If only one manager exists
manager = client.Manager  # Instead of client.Managers
print(f"Manager: {manager.FirmwareVersion}")
```

### Nested Collection Access

Singular access works at any level of the resource hierarchy:

```python
# Access single processor in a system
system = client.System
processor = system.Processor  # If only one processor exists
print(f"Cores: {processor.TotalCores}")

# Access single storage controller
storage_controller = system.Storage  # If only one storage controller
print(f"RAID: {storage_controller.StorageControllers[0].SupportedRAIDTypes}")

# Chain singular access
if len(system.Processors) == 1:
    cpu = system.Processor
    print(f"CPU Model: {cpu.Model}")
```

### Mixed Access Patterns

You can mix singular and plural access as needed:

```python
# Use singular where appropriate
system = client.System

# Use plural for iteration when multiple exist
for nic in system.EthernetInterfaces:
    print(f"NIC {nic.Id}: {nic.MACAddress}")

# Use singular for nested single-member collections
if len(system.Storage) == 1:
    storage = system.Storage
    print(f"Storage: {storage.Name}")
```

## When Singular Access Fails

Singular access only works when the collection has **exactly one member**. In other cases, you'll get an `AttributeError`:

### Multiple Members

```python
# If Systems has 2+ members
try:
    system = client.System  # Fails!
except AttributeError:
    # Use plural form instead
    for system in client.Systems:
        print(system.Name)
```

### Empty Collections

```python
# If Managers collection is empty
try:
    manager = client.Manager  # Fails!
except AttributeError:
    print("No managers found")
```

### Non-Existent Collections

```python
# If neither "Thing" nor "Things" exists
try:
    thing = client.Thing  # Fails!
except AttributeError:
    print("Attribute doesn't exist")
```

## Best Practices

### 1. Check Collection Size First

For robust code, verify the collection size before using singular access:

```python
if len(client.Systems) == 1:
    system = client.System
    # Work with single system
else:
    # Handle multiple systems
    for system in client.Systems:
        print(system.Name)
```

### 2. Use Try-Except for Optional Optimization

If single-member access is an optimization but not required:

```python
try:
    system = client.System  # Fast path for single system
except AttributeError:
    system = next(iter(client.Systems))  # Fallback
```

### 3. Document Your Assumptions

If your code assumes single-member collections, document this:

```python
def configure_system(client):
    """
    Configure the system.
    
    Assumes: BMC has exactly one system (common in 1U servers).
    """
    system = client.System  # Will fail if assumption doesn't hold
    system.Reset(ResetType="GracefulRestart")
```

### 4. Prefer Explicit Code for Multiple Members

Don't try to use singular access when you know there are multiple members:

```python
# BAD - will always fail with multiple systems
for i in range(len(client.Systems)):
    system = client.System  # Wrong!
    
# GOOD - explicit iteration
for system in client.Systems:
    print(system.Name)
```

## Implementation Details

### Pluralization Logic

Currently, rackfish uses simple "add s" pluralization:

- `System` → `Systems` ✓
- `Chassis` → `Chassi` → `Chassis` (special handling needed)
- `Manager` → `Managers` ✓
- `Processor` → `Processors` ✓

### Performance Considerations

Singular access has minimal overhead:

1. One failed attribute lookup
2. One successful attribute lookup for plural form
3. One `len()` call on the collection
4. One iteration to get first member

This is comparable to `next(iter(collection))` and faster than `list(collection)[0]`.

### Thread Safety

Singular access is as thread-safe as the underlying collection access. The collection length check and member retrieval are not atomic, so concurrent modifications could cause issues (same as with any collection access).

## Comparison with Traditional Methods

| Method | Code | Works When |
|--------|------|------------|
| Singular access | `client.System` | Exactly 1 member |
| Iteration | `next(iter(client.Systems))` | 1+ members |
| Indexing | `client.Systems.Members[0]` | 1+ members |
| List conversion | `list(client.Systems)[0]` | 1+ members |

**Recommendation**: Use singular access when you **know** or **expect** exactly one member and want cleaner code. Use traditional methods when handling variable-sized collections.

## Real-World Use Cases

### Single-Server BMCs (1U, Blades)

Most 1U rack servers and blade servers have exactly one system:

```python
# Common pattern for 1U servers
system = client.System
system.Reset(ResetType="On")
print(f"Power: {system.PowerState}")
```

### Single-Chassis Servers

Many servers have one chassis:

```python
chassis = client.Chassis
for sensor in chassis.Thermal.Temperatures:
    if sensor.ReadingCelsius > 80:
        alert(f"High temp: {sensor.Name}")
```

### Single-Manager Systems

Typical servers have one management controller:

```python
manager = client.Manager
print(f"Firmware: {manager.FirmwareVersion}")
manager.Actions["#Manager.Reset"](ResetType="GracefulRestart")
```

### Embedded Controllers

Servers with embedded NICs, storage controllers, etc.:

```python
system = client.System

# Single integrated NIC
if len(system.EthernetInterfaces) == 1:
    nic = system.EthernetInterface
    print(f"MAC: {nic.MACAddress}")

# Single storage controller
if len(system.Storage) == 1:
    storage = system.Storage
    print(f"Controller: {storage.StorageControllers[0].Model}")
```

## Error Handling

### Graceful Degradation

```python
def get_system(client):
    """Get the system, preferring singular access if possible."""
    try:
        return client.System
    except AttributeError:
        systems = list(client.Systems)
        if not systems:
            raise ValueError("No systems found")
        if len(systems) > 1:
            raise ValueError(f"Multiple systems found: {len(systems)}")
        return systems[0]
```

### Validation Helper

```python
def require_single_system(client):
    """Ensure exactly one system exists."""
    count = len(client.Systems)
    if count == 0:
        raise ValueError("No systems found")
    if count > 1:
        raise ValueError(f"Expected 1 system, found {count}")
    return client.System
```

## Testing

Singular access is fully tested in `tests/test_singular_collection_access.py`:

- Single member access (success case)
- Multiple members (failure case)
- Empty collection (failure case)
- Non-existent attribute (failure case)
- Nested collections
- Client-level and resource-level access

Run tests with:

```bash
pytest tests/test_singular_collection_access.py -v
```

## Limitations

1. **Simple Pluralization**: Only adds "s" to form plurals. Irregular plurals like "Chassis" (plural of "Chassis") won't work with `Chassi` singular form.

2. **Exact Count Required**: Collection must have exactly 1 member. Won't default to first member if multiple exist (by design, for safety).

3. **No Configuration**: Cannot configure pluralization rules or enable/disable the feature.

4. **Python Naming Convention**: Assumes collection names follow Python conventions (ending in "s" for plurals).

## Future Enhancements

Possible improvements in future versions:

1. **Configurable Pluralization**: Custom rules for irregular plurals
2. **Opt-in Behavior**: Configuration flag to enable/disable singular access
3. **Better Error Messages**: Indicate whether plural form exists and its member count
4. **Caching**: Cache singular-to-plural mappings for performance

## See Also

- [EXAMPLES.md](EXAMPLES.md) - Usage examples including singular access patterns
- [docs/TESTS.md](TESTS.md) - Test documentation
- [Client API Reference](../rackfish/client.py) - Implementation details

---

**Feature Added:** Version 1.0.2  
**Status:** Stable  
**Test Coverage:** 7 comprehensive tests
