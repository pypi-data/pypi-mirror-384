#!/usr/bin/env python3
"""
Test that OEM and Links child objects are surfaced to the main object.
"""

import sys

sys.path.insert(0, ".")

from rackfish import RedfishClient, RedfishResource


# Mock client
class MockClient:
    def __init__(self):
        self.base_url = "http://mock"

    def get(self, path):
        return {"@odata.id": path, "Id": "mock", "Name": "Mock"}


def test_oem_surfacing():
    """Test that OEM properties are surfaced to main object."""
    print("Testing OEM content surfacing...")

    # Sample data with OEM vendor extensions
    data = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "System1",
        "Name": "Test System",
        "PowerState": "On",
        "Oem": {
            "Huawei": {
                "FruControl": {"@odata.id": "/redfish/v1/Systems/1/Oem/Huawei/FruControl"},
                "BootMode": "Legacy",
                "CustomProperty": "CustomValue",
            },
            "Dell": {"DellAttributes": {"@odata.id": "/redfish/v1/Systems/1/Oem/Dell/Attributes"}},
        },
    }

    mock_client = MockClient()
    resource = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=data, fetched=False)

    # Access standard property
    print(f"  Standard property - Id: {resource.Id}")
    assert resource.Id == "System1", "Standard property access failed"

    # Check that OEM properties are surfaced
    print(f"  OEM surfaced - FruControl: {resource.FruControl}")
    assert hasattr(resource, "FruControl"), "FruControl not surfaced from Huawei OEM"
    assert isinstance(
        resource.FruControl, RedfishResource
    ), "FruControl should be a RedfishResource"

    print(f"  OEM surfaced - BootMode: {resource.BootMode}")
    assert resource.BootMode == "Legacy", "BootMode not surfaced from Huawei OEM"

    print(f"  OEM surfaced - CustomProperty: {resource.CustomProperty}")
    assert resource.CustomProperty == "CustomValue", "CustomProperty not surfaced from Huawei OEM"

    print(f"  OEM surfaced - DellAttributes: {resource.DellAttributes}")
    assert hasattr(resource, "DellAttributes"), "DellAttributes not surfaced from Dell OEM"

    # Original Oem property should still be accessible
    assert hasattr(resource, "Oem"), "Original Oem property should still exist"

    print("✓ OEM surfacing test passed!\n")
    return True


def test_links_surfacing():
    """Test that Links properties are surfaced to main object."""
    print("Testing Links content surfacing...")

    # Sample data with Links
    data = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "System1",
        "Name": "Test System",
        "Links": {
            "Chassis": [{"@odata.id": "/redfish/v1/Chassis/1"}],
            "ManagedBy": [{"@odata.id": "/redfish/v1/Managers/BMC"}],
            "RelatedItem": {"@odata.id": "/redfish/v1/Systems/1/Storage/1"},
            "Oem": {},  # OEM in Links should be skipped
        },
    }

    mock_client = MockClient()
    resource = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=data, fetched=False)

    # Access standard property
    print(f"  Standard property - Id: {resource.Id}")
    assert resource.Id == "System1", "Standard property access failed"

    # Check that Links properties are surfaced
    print(f"  Links surfaced - Chassis: {resource.Chassis}")
    assert hasattr(resource, "Chassis"), "Chassis not surfaced from Links"
    assert isinstance(resource.Chassis, list), "Chassis should be a list"
    assert len(resource.Chassis) == 1, "Chassis should have 1 item"

    print(f"  Links surfaced - ManagedBy: {resource.ManagedBy}")
    assert hasattr(resource, "ManagedBy"), "ManagedBy not surfaced from Links"

    print(f"  Links surfaced - RelatedItem: {resource.RelatedItem}")
    assert hasattr(resource, "RelatedItem"), "RelatedItem not surfaced from Links"
    assert isinstance(
        resource.RelatedItem, RedfishResource
    ), "RelatedItem should be a RedfishResource"

    # Original Links property should still be accessible
    assert hasattr(resource, "Links"), "Original Links property should still exist"

    print("✓ Links surfacing test passed!\n")
    return True


def test_no_collision():
    """Test that existing properties are not overwritten."""
    print("Testing collision avoidance...")

    # Sample data where OEM tries to override existing property
    data = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "System1",
        "Name": "Test System",
        "PowerState": "On",  # Standard property
        "Oem": {
            "Vendor": {
                "PowerState": "CustomValue",  # Should NOT override
                "CustomProp": "ShouldBeSurfaced",
            }
        },
    }

    mock_client = MockClient()
    resource = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=data, fetched=False)

    # Standard property should not be overwritten
    print(f"  PowerState (should be 'On'): {resource.PowerState}")
    assert resource.PowerState == "On", "Standard property was incorrectly overwritten by OEM"

    # Non-colliding OEM property should be surfaced
    print(f"  CustomProp (should be surfaced): {resource.CustomProp}")
    assert resource.CustomProp == "ShouldBeSurfaced", "Non-colliding OEM property not surfaced"

    print("✓ Collision avoidance test passed!\n")
    return True


def test_oem_actions():
    """Test that OEM actions are still properly bound as methods."""
    print("Testing OEM actions binding...")

    # Sample data with OEM actions
    data = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "System1",
        "Name": "Test System",
        "Actions": {
            "#ComputerSystem.Reset": {
                "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
            },
            "Oem": {
                "Huawei": {
                    "#HuaweiComputerSystem.FruControl": {
                        "target": "/redfish/v1/Systems/1/Actions/Oem/Huawei/FruControl"
                    }
                }
            },
        },
    }

    mock_client = MockClient()
    resource = RedfishResource(mock_client, path="/redfish/v1/Systems/1", data=data, fetched=False)

    # Standard action should be bound
    print(f"  Standard action - Reset: {hasattr(resource, 'Reset')}")
    assert hasattr(resource, "Reset"), "Standard Reset action not bound"
    assert callable(resource.Reset), "Reset should be callable"

    # OEM action should be bound
    print(f"  OEM action - FruControl: {hasattr(resource, 'FruControl')}")
    assert hasattr(resource, "FruControl"), "OEM FruControl action not bound"
    assert callable(resource.FruControl), "FruControl should be callable"

    print("✓ OEM actions binding test passed!\n")
    return True


if __name__ == "__main__":
    try:
        success = True
        success &= test_oem_surfacing()
        success &= test_links_surfacing()
        success &= test_no_collision()
        success &= test_oem_actions()

        if success:
            print("✅ All OEM and Links surfacing tests passed!")
            sys.exit(0)
        else:
            print("❌ Some tests failed")
            sys.exit(1)
    except Exception as e:
        print(f"❌ Test error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
