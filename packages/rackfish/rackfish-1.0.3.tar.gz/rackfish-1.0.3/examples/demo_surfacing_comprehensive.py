#!/usr/bin/env python3
"""
Comprehensive example showing OEM and Links surfacing with a mock Huawei BMC.
This demonstrates the real-world benefits of automatic property surfacing.
"""

import sys

sys.path.insert(0, ".")

from rackfish import RedfishClient, RedfishResource


# Mock Huawei BMC client
class MockHuaweiBMC:
    def __init__(self):
        self.base_url = "https://huawei-bmc.example.com/redfish/v1"
        self.responses = {
            "/redfish/v1/Systems/1": {
                "@odata.id": "/redfish/v1/Systems/1",
                "Id": "1",
                "Name": "System",
                "PowerState": "On",
                "BootSourceOverrideTarget": "Pxe",
                "Links": {
                    "Chassis": [{"@odata.id": "/redfish/v1/Chassis/1"}],
                    "ManagedBy": [{"@odata.id": "/redfish/v1/Managers/1"}],
                },
                "Oem": {
                    "Huawei": {
                        "BootMode": "UEFI",
                        "ProductName": "TaiShan 2280 V2",
                        "FruControl": {"@odata.id": "/redfish/v1/Systems/1/Oem/Huawei/FruControl"},
                    }
                },
                "Actions": {
                    "#ComputerSystem.Reset": {
                        "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset",
                        "ResetType@Redfish.AllowableValues": ["On", "ForceOff", "GracefulRestart"],
                    },
                    "Oem": {
                        "Huawei": {
                            "#HuaweiComputerSystem.FruControl": {
                                "target": "/redfish/v1/Systems/1/Actions/Oem/Huawei/FruControl"
                            }
                        }
                    },
                },
            },
            "/redfish/v1/Chassis/1": {
                "@odata.id": "/redfish/v1/Chassis/1",
                "Id": "1",
                "Name": "Chassis",
                "ChassisType": "RackMount",
            },
            "/redfish/v1/Managers/1": {
                "@odata.id": "/redfish/v1/Managers/1",
                "Id": "BMC",
                "Name": "Manager",
                "FirmwareVersion": "3.00",
            },
        }

    def get(self, path):
        return self.responses.get(path, {})

    def post(self, path, data=None):
        print(f"POST {path} with data: {data}")
        return {}


def demo_old_way():
    """Show the old way of accessing OEM and Links (before surfacing)."""
    print("\n" + "=" * 70)
    print("OLD WAY: Manual nested access (before surfacing)")
    print("=" * 70)

    mock_client = MockHuaweiBMC()
    system = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=None, fetched=False)

    print("\n1. Accessing standard properties:")
    print(f"   system.PowerState = {system.PowerState}")
    print(f"   system.Id = {system.Id}")

    print("\n2. Accessing OEM properties (verbose):")
    print(f"   system.Oem['Huawei']['BootMode'] = ", end="")
    try:
        boot_mode = system.Oem.get("Huawei", {}).get("BootMode", "N/A")
        print(boot_mode)
    except:
        print("Error accessing nested OEM")

    print("\n3. Accessing Links (verbose):")
    print("   chassis_list = system.Links['Chassis']")
    print("   for chassis_ref in chassis_list:")
    print("       chassis = client.get(chassis_ref['@odata.id'])")
    print("       # More code needed...")


def demo_new_way():
    """Show the new way with automatic surfacing."""
    print("\n" + "=" * 70)
    print("NEW WAY: Direct access with automatic surfacing")
    print("=" * 70)

    mock_client = MockHuaweiBMC()
    system = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=None, fetched=False)

    print("\n1. Standard properties (same as before):")
    print(f"   system.PowerState = {system.PowerState}")
    print(f"   system.Id = {system.Id}")

    print("\n2. OEM properties (surfaced automatically! ✨):")
    print(f"   system.BootMode = {system.BootMode}")
    print(f"   system.ProductName = {system.ProductName}")
    print(f"   system.FruControl = {system.FruControl}")

    print("\n3. Links (surfaced automatically! ✨):")
    print("   for chassis in system.Chassis:")
    for chassis in system.Chassis:
        print(f"       {chassis.Id}: {chassis.Name} ({chassis.ChassisType})")

    print("\n   for manager in system.ManagedBy:")
    for manager in system.ManagedBy:
        print(f"       {manager.Id}: {manager.Name} (FW: {manager.FirmwareVersion})")

    print("\n4. Actions (both standard and OEM):")
    print("   Standard action:")
    print(f"     system.Reset (callable: {callable(system.Reset)})")

    print("   OEM action (surfaced!):")
    print(f"     system.FruControl (callable: {callable(system.FruControl)})")


def demo_backward_compatibility():
    """Show that old access methods still work."""
    print("\n" + "=" * 70)
    print("BACKWARD COMPATIBILITY: Old methods still work")
    print("=" * 70)

    mock_client = MockHuaweiBMC()
    system = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=None, fetched=False)

    print("\n✓ Original Oem dict still accessible:")
    print(f"  system.Oem exists: {hasattr(system, 'Oem')}")
    print(f"  system.Oem keys: {list(system.Oem.keys()) if hasattr(system.Oem, 'keys') else 'N/A'}")

    print("\n✓ Original Links dict still accessible:")
    print(f"  system.Links exists: {hasattr(system, 'Links')}")
    print(
        f"  system.Links keys: {list(system.Links.keys()) if hasattr(system.Links, 'keys') else 'N/A'}"
    )

    print("\n✓ Both access methods work:")
    print(f"  system.BootMode (surfaced) = {system.BootMode}")
    print(f"  system.Oem.Huawei.BootMode (original) = ", end="")
    if hasattr(system.Oem, "Huawei"):
        print(system.Oem.Huawei.BootMode)
    else:
        print("Accessible via dict access")


def demo_collision_safety():
    """Show collision safety - standard properties not overwritten."""
    print("\n" + "=" * 70)
    print("COLLISION SAFETY: Standard properties protected")
    print("=" * 70)

    # Create mock data with potential collision
    mock_client = MockHuaweiBMC()
    collision_data = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "System1",
        "PowerState": "On",  # Standard property
        "Oem": {
            "Vendor": {
                "PowerState": "CustomState",  # Would collide if not protected
                "SafeProperty": "ShouldSurface",  # Safe to surface
            }
        },
    }

    system = RedfishResource(
        mock_client, path="/redfish/v1/Systems/1", data=collision_data, fetched=False
    )

    print("\n✓ Standard property NOT overwritten:")
    print(f"  system.PowerState = '{system.PowerState}'")
    print("  (Correctly shows 'On', not 'CustomState')")

    print("\n✓ Non-colliding OEM property surfaced:")
    print(f"  system.SafeProperty = '{system.SafeProperty}'")

    print("\n✓ OEM variant still accessible via Oem dict:")
    print("  system.Oem['Vendor']['PowerState'] would give 'CustomState'")


if __name__ == "__main__":
    print("\n" + "=" * 70)
    print("COMPREHENSIVE OEM AND LINKS SURFACING DEMO")
    print("Simulating Huawei BMC with vendor extensions")
    print("=" * 70)

    demo_old_way()
    demo_new_way()
    demo_backward_compatibility()
    demo_collision_safety()

    print("\n" + "=" * 70)
    print("SUMMARY OF BENEFITS")
    print("=" * 70)
    print(
        """
✅ Cleaner Code
   Before: system.Oem['Huawei']['BootMode']
   After:  system.BootMode

✅ Better IDE Support
   - Autocomplete works on surfaced properties
   - Type hints are preserved

✅ Easier Discovery
   - dir(system) shows all available properties
   - No need to dig into Oem/Links dicts

✅ More Pythonic
   - Dot notation instead of dict access
   - Natural traversal: system.Chassis[0].Thermal.Fans

✅ Safe
   - Standard properties never overwritten
   - Collision detection prevents conflicts

✅ Backward Compatible
   - Oem and Links dicts still accessible
   - Existing code continues to work
    """
    )

    print("=" * 70)
