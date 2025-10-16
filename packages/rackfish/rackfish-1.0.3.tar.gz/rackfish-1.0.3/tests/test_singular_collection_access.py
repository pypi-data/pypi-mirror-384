"""
Test singular access to single-member collections.

When a collection has only one member, it should be accessible via singular name.
E.g., client.System instead of client.Systems when only one system exists.
"""

import pytest

from rackfish import RedfishClient, RedfishResource


class MockClient:
    """Mock client that returns mock data for testing."""

    def __init__(self):
        self.base_url = "https://mock"
        self._session_token = None
        self._data = {
            "/redfish/v1": {
                "Systems": {"@odata.id": "/redfish/v1/Systems"},
                "Chassis": {"@odata.id": "/redfish/v1/Chassis"},
                "Managers": {"@odata.id": "/redfish/v1/Managers"},
            },
            "/redfish/v1/Systems": {
                "@odata.id": "/redfish/v1/Systems",
                "Members": [
                    {"@odata.id": "/redfish/v1/Systems/1"},
                ],
                "Members@odata.count": 1,
            },
            "/redfish/v1/Systems/1": {
                "@odata.id": "/redfish/v1/Systems/1",
                "Id": "1",
                "Name": "System 1",
                "PowerState": "On",
                "Processors": {"@odata.id": "/redfish/v1/Systems/1/Processors"},
            },
            "/redfish/v1/Chassis": {
                "@odata.id": "/redfish/v1/Chassis",
                "Members": [
                    {"@odata.id": "/redfish/v1/Chassis/1"},
                    {"@odata.id": "/redfish/v1/Chassis/2"},
                ],
                "Members@odata.count": 2,
            },
            "/redfish/v1/Chassis/1": {
                "@odata.id": "/redfish/v1/Chassis/1",
                "Id": "1",
                "Name": "Chassis 1",
            },
            "/redfish/v1/Chassis/2": {
                "@odata.id": "/redfish/v1/Chassis/2",
                "Id": "2",
                "Name": "Chassis 2",
            },
            "/redfish/v1/Managers": {
                "@odata.id": "/redfish/v1/Managers",
                "Members": [],
                "Members@odata.count": 0,
            },
            "/redfish/v1/Systems/1/Processors": {
                "@odata.id": "/redfish/v1/Systems/1/Processors",
                "Members": [
                    {"@odata.id": "/redfish/v1/Systems/1/Processors/CPU1"},
                ],
                "Members@odata.count": 1,
            },
            "/redfish/v1/Systems/1/Processors/CPU1": {
                "@odata.id": "/redfish/v1/Systems/1/Processors/CPU1",
                "Id": "CPU1",
                "Name": "Processor 1",
                "TotalCores": 8,
            },
        }

    def get(self, path: str, **_kwargs):
        """Return mock responses for different paths."""
        return self._data.get(path, {})

    def post(self, _path, _data, **_kwargs):
        return {}

    def patch(self, _path, _data, **_kwargs):
        return {}

    def delete(self, _path, **_kwargs):
        return {}


def test_singular_access_to_single_member_collection():
    """Test accessing single member via singular name."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Access Systems collection (has 1 member)
    system = root.System  # singular access
    assert system.Id == "1"
    assert system.Name == "System 1"
    assert system.PowerState == "On"


def test_singular_access_fails_for_multiple_members():
    """Test that singular access raises AttributeError when collection has multiple members."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Access Chassis collection (has 2 members)
    with pytest.raises(AttributeError, match="no attribute 'Chassi'"):
        _ = root.Chassi  # should fail


def test_singular_access_fails_for_empty_collection():
    """Test that singular access raises AttributeError when collection is empty."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Access Managers collection (empty)
    with pytest.raises(AttributeError, match="no attribute 'Manager'"):
        _ = root.Manager  # should fail


def test_singular_access_via_client():
    """Test singular access through RedfishClient."""
    mock_client = MockClient()
    client = RedfishClient.__new__(RedfishClient)
    client._client = mock_client
    client._root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Access via client
    system = client.System  # singular access through client
    assert system.Id == "1"
    assert system.Name == "System 1"


def test_singular_access_nested_collections():
    """Test singular access works for nested collections."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Access nested single-member collection
    system = root.System
    processor = system.Processor  # singular access to nested collection
    assert processor.Id == "CPU1"
    assert processor.Name == "Processor 1"
    assert processor.TotalCores == 8


def test_plural_access_still_works():
    """Test that traditional plural access still works."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    # Traditional plural access
    systems = root.Systems
    assert len(systems) == 1
    system = next(iter(systems))
    assert system.Id == "1"


def test_singular_access_nonexistent_attribute():
    """Test that accessing non-existent singular attribute fails properly."""
    mock_client = MockClient()
    root = RedfishResource(mock_client, path="/redfish/v1", data=None, fetched=False)

    with pytest.raises(AttributeError, match="no attribute 'NonExistent'"):
        _ = root.NonExistent
