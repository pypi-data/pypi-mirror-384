#!/usr/bin/env python3
"""
Example demonstrating OEM and Links surfacing features.
Shows how vendor-specific properties and linked resources are automatically surfaced.
"""

from rackfish import RedfishClient, RedfishResource


# Example 1: Accessing OEM properties directly
def example_oem_access():
    """
    Before surfacing:
        system.Oem["Huawei"]["BootMode"]

    After surfacing:
        system.BootMode  # Much cleaner!
    """
    print("Example 1: OEM Property Surfacing")
    print("=" * 50)

    # Mock example - in real usage, connect to actual BMC
    # client = RedfishClient("https://bmc.example.com", "admin", "password")
    # root = client.connect()
    # system = next(iter(client.Systems))

    print("# Access OEM properties directly:")
    print("system.BootMode              # Instead of system.Oem['Vendor']['BootMode']")
    print("system.FruControl            # Instead of system.Oem['Vendor']['FruControl']")
    print("system.CustomProperty        # Vendor-specific extensions")
    print()


# Example 2: Accessing Links directly
def example_links_access():
    """
    Before surfacing:
        chassis_list = system.Links["Chassis"]
        for chassis_ref in chassis_list:
            chassis = client.get(chassis_ref["@odata.id"])

    After surfacing:
        for chassis in system.Chassis:  # Direct access!
            print(chassis.Id)
    """
    print("Example 2: Links Surfacing")
    print("=" * 50)

    print("# Access linked resources directly:")
    print("for chassis in system.Chassis:")
    print("    print(chassis.Id)        # Instead of system.Links['Chassis']")
    print()
    print("for manager in system.ManagedBy:")
    print("    print(manager.Name)      # Instead of system.Links['ManagedBy']")
    print()


# Example 3: Collision avoidance
def example_collision_handling():
    """
    When OEM or Links properties have the same name as standard properties,
    the standard property takes precedence (no collision).
    """
    print("Example 3: Collision Avoidance")
    print("=" * 50)

    print("# Standard properties are never overwritten:")
    print("system.PowerState            # Always the standard Redfish property")
    print("system.Oem['Vendor']['PowerState']  # OEM variant still accessible")
    print()


# Example 4: Real-world scenario - Huawei BMC
def example_huawei_bmc():
    """
    Huawei BMCs provide many OEM extensions.
    With surfacing, these are much easier to access.
    """
    print("Example 4: Huawei BMC OEM Extensions")
    print("=" * 50)

    print("# Huawei-specific extensions surfaced:")
    print("system.FruControl            # Huawei FRU control resource")
    print("system.BootMode              # Legacy/UEFI boot mode")
    print("system.ProductName           # Huawei product name")
    print()

    print("# Call Huawei OEM actions directly:")
    print("system.FruControl()          # Huawei FRU control action")
    print()


# Example 5: Complex navigation with surfacing
def example_complex_navigation():
    """
    Navigate complex resource relationships using surfaced properties.
    """
    print("Example 5: Complex Navigation Made Simple")
    print("=" * 50)

    print(
        """
# Before surfacing - verbose and error-prone:
system_chassis_links = system.get("Links", {}).get("Chassis", [])
for chassis_ref in system_chassis_links:
    chassis = client.get(chassis_ref["@odata.id"])
    thermal_ref = chassis.get("Thermal", {}).get("@odata.id")
    if thermal_ref:
        thermal = client.get(thermal_ref)
        for fan in thermal.get("Fans", []):
            print(fan.get("Name"))

# After surfacing - clean and intuitive:
for chassis in system.Chassis:
    for fan in chassis.Thermal.Fans:
        print(fan.Name)
    """
    )
    print()


if __name__ == "__main__":
    print("\n" + "=" * 50)
    print("OEM and Links Surfacing Examples")
    print("=" * 50 + "\n")

    example_oem_access()
    example_links_access()
    example_collision_handling()
    example_huawei_bmc()
    example_complex_navigation()

    print("=" * 50)
    print("Benefits of Surfacing:")
    print("=" * 50)
    print("✓ Cleaner code - less nested access")
    print("✓ Better IDE autocomplete")
    print("✓ More Pythonic API")
    print("✓ Easier vendor extension discovery")
    print("✓ Reduced typing errors")
    print("✓ Still backward compatible (Oem/Links remain accessible)")
    print()
