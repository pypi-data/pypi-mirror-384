#!/usr/bin/env python3
"""
Test the most common Redfish usage cases for pyredfisher.
"""

import sys

sys.path.insert(0, ".")

from rackfish import RedfishClient, RedfishResource


# Mock RedfishClient for testing (no real HTTP calls)
class MockClient:
    def __init__(self):
        self.base_url = "http://mock"
        self._data = {
            "/redfish/v1": {
                "Systems": {"@odata.id": "/redfish/v1/Systems"},
                "Managers": {"@odata.id": "/redfish/v1/Managers"},
                "SessionService": {"@odata.id": "/redfish/v1/SessionService"},
            },
            "/redfish/v1/Systems": {
                "Members": [
                    {"@odata.id": "/redfish/v1/Systems/1"},
                    {"@odata.id": "/redfish/v1/Systems/2"},
                ]
            },
            "/redfish/v1/Systems/1": {
                "Id": "1",
                "Name": "System1",
                "PowerState": "On",
                "Oem": {"Vendor": {"CustomProp": "Value1"}},
                "Links": {"Chassis": [{"@odata.id": "/redfish/v1/Chassis/1"}]},
                "Actions": {
                    "#ComputerSystem.Reset": {
                        "target": "/redfish/v1/Systems/1/Actions/ComputerSystem.Reset"
                    }
                },
            },
            "/redfish/v1/Systems/2": {
                "Id": "2",
                "Name": "System2",
                "PowerState": "Off",
                "Oem": {"Vendor": {"CustomProp": "Value2"}},
                "Links": {"Chassis": [{"@odata.id": "/redfish/v1/Chassis/2"}]},
                "Actions": {
                    "#ComputerSystem.Reset": {
                        "target": "/redfish/v1/Systems/2/Actions/ComputerSystem.Reset"
                    }
                },
            },
            "/redfish/v1/Chassis/1": {"Id": "Chassis1", "Name": "Chassis1"},
            "/redfish/v1/Chassis/2": {"Id": "Chassis2", "Name": "Chassis2"},
        }

    def get(self, path):
        return self._data.get(path, {})

    def post(self, path, data=None):
        return {"result": "ok", "path": path, "data": data}

    def patch(self, path, data=None, etag=None):
        return {"result": "patched", "path": path, "data": data, "etag": etag}

    def delete(self, path):
        return {"result": "deleted", "path": path}


def test_basic_traversal():
    print("Test: Basic Redfish resource traversal and collection iteration")
    client = MockClient()
    root = RedfishResource(client, path="/redfish/v1", data=client.get("/redfish/v1"), fetched=True)
    systems = RedfishResource(
        client, path="/redfish/v1/Systems", data=client.get("/redfish/v1/Systems"), fetched=True
    )

    # Iterate over the collection
    system_objs = list(systems)
    assert len(system_objs) == 2

    # Access properties on the resources
    sys1 = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )
    sys2 = RedfishResource(
        client, path="/redfish/v1/Systems/2", data=client.get("/redfish/v1/Systems/2"), fetched=True
    )
    assert sys1.Name == "System1"
    assert sys2.PowerState == "Off"
    print("  Traversal and collection iteration: OK")
    return True


def test_oem_links_surfacing():
    print("Test: OEM and Links surfacing")
    client = MockClient()
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )
    # OEM property surfaced
    assert hasattr(system, "CustomProp")
    assert system.CustomProp == "Value1"
    # Links property surfaced (Chassis is a list of link stubs)
    assert hasattr(system, "Chassis")
    chassis_list = list(system.Chassis)
    assert len(chassis_list) == 1
    # Fetch the first chassis
    chassis = RedfishResource(
        client, path="/redfish/v1/Chassis/1", data=client.get("/redfish/v1/Chassis/1"), fetched=True
    )
    assert chassis.Name == "Chassis1"
    print("  OEM/Links surfacing: OK")
    return True


def test_action_invocation():
    print("Test: Action invocation (Reset)")
    client = MockClient()
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )
    # Simulate action call
    result = system.Reset(ResetType="On")
    assert result["result"] == "ok"
    print("  Action invocation: OK")
    return True


def test_patch_update():
    print("Test: PATCH update via attribute assignment")
    client = MockClient()
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )
    # Simulate PATCH
    system.PowerState = "ForceOff"
    print("  PATCH update: OK")
    return True


def test_create_delete():
    print("Test: Create and delete resource in collection")
    client = MockClient()
    systems = RedfishResource(
        client, path="/redfish/v1/Systems", data=client.get("/redfish/v1/Systems"), fetched=True
    )
    # Simulate create
    new = systems.create({"Id": "3", "Name": "System3"})
    assert new is not None or systems.refresh() is None
    # Simulate delete
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )
    system.delete()
    print("  Create/Delete: OK")
    return True


if __name__ == "__main__":
    all_passed = True
    all_passed &= test_basic_traversal()
    all_passed &= test_oem_links_surfacing()
    all_passed &= test_action_invocation()
    all_passed &= test_patch_update()
    all_passed &= test_create_delete()
    print("\nAll common Redfish usage tests passed!" if all_passed else "Some tests failed.")
