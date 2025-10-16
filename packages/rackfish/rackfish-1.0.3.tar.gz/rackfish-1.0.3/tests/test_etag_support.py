"""
Test ETag support for PATCH requests.

Verifies that ETags are properly extracted from resources and included
in PATCH requests via the If-Match header.
"""

from rackfish import RedfishResource


class MockClientWithETag:
    """Mock client that tracks ETag headers in PATCH requests."""

    def __init__(self):
        self._data = {
            "/redfish/v1/Systems/1": {
                "@odata.id": "/redfish/v1/Systems/1",
                "@odata.type": "#ComputerSystem.v1_0_0.ComputerSystem",
                "@odata.etag": 'W/"12345678"',
                "Id": "1",
                "Name": "System 1",
                "AssetTag": "MyServer",
                "PowerState": "On",
            }
        }
        self.last_patch_etag = None
        self.last_patch_data = None

    def get(self, path):
        return self._data.get(path, {})

    def post(self, path, data=None):
        return {"result": "ok", "path": path, "data": data}

    def patch(self, path, data=None, etag=None):
        # Store the ETag that was passed
        self.last_patch_etag = etag
        self.last_patch_data = data
        return {"result": "patched", "path": path, "data": data, "etag": etag}

    def delete(self, path):
        return {"result": "deleted", "path": path}


def test_etag_in_patch_via_attribute():
    """Test that ETag is included when using attribute assignment."""
    print("Test: ETag included in PATCH via attribute assignment")
    client = MockClientWithETag()
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )

    # Modify an attribute (triggers PATCH)
    system.AssetTag = "NewAssetTag"

    # Verify the ETag was passed to the PATCH request
    assert (
        client.last_patch_etag == 'W/"12345678"'
    ), f'Expected ETag W/"12345678", got {client.last_patch_etag}'
    assert client.last_patch_data == {"AssetTag": "NewAssetTag"}
    print(f"  ✓ ETag correctly passed: {client.last_patch_etag}")
    return True


def test_etag_in_patch_method():
    """Test that ETag is included when using .patch() method."""
    print("Test: ETag included in PATCH via .patch() method")
    client = MockClientWithETag()
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )

    # Use patch method
    system.patch({"AssetTag": "AnotherTag", "PowerState": "Off"})

    # Verify the ETag was passed to the PATCH request
    assert (
        client.last_patch_etag == 'W/"12345678"'
    ), f'Expected ETag W/"12345678", got {client.last_patch_etag}'
    assert client.last_patch_data == {"AssetTag": "AnotherTag", "PowerState": "Off"}
    print(f"  ✓ ETag correctly passed: {client.last_patch_etag}")
    return True


def test_patch_without_etag():
    """Test that PATCH works when resource has no ETag."""
    print("Test: PATCH works without ETag present")
    client = MockClientWithETag()
    # Modify data to remove ETag
    client._data["/redfish/v1/Systems/1"] = {
        "@odata.id": "/redfish/v1/Systems/1",
        "Id": "1",
        "AssetTag": "NoETagResource",
    }
    system = RedfishResource(
        client, path="/redfish/v1/Systems/1", data=client.get("/redfish/v1/Systems/1"), fetched=True
    )

    # Modify an attribute (triggers PATCH)
    system.AssetTag = "UpdatedTag"

    # Verify that None was passed as ETag (no error should occur)
    assert client.last_patch_etag is None, f"Expected None, got {client.last_patch_etag}"
    assert client.last_patch_data == {"AssetTag": "UpdatedTag"}
    print(f"  ✓ PATCH succeeded without ETag")
    return True


if __name__ == "__main__":
    all_passed = True
    all_passed &= test_etag_in_patch_via_attribute()
    all_passed &= test_etag_in_patch_method()
    all_passed &= test_patch_without_etag()

    if all_passed:
        print("\n✅ All ETag tests passed!")
    else:
        print("\n❌ Some tests failed")
        exit(1)
