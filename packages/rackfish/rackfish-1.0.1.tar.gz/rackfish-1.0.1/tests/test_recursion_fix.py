#!/usr/bin/env python3
"""
Test that deeply nested JSON structures don't cause recursion errors.
This simulates a Redfish response with deeply nested embedded resources.
"""

import sys

sys.path.insert(0, ".")

from rackfish import RedfishClient, RedfishResource


# Create a deeply nested structure (simulating embedded Redfish resources)
def create_nested_structure(depth=50):
    """Create a deeply nested dict structure with @odata.id to simulate embedded resources."""
    if depth == 0:
        return {"Id": "leaf", "Name": "LeafResource", "@odata.id": "/redfish/v1/leaf"}

    return {
        "@odata.id": f"/redfish/v1/level{depth}",
        "Id": f"level{depth}",
        "Name": f"Level {depth}",
        "Child": create_nested_structure(depth - 1),
        "Siblings": [{"@odata.id": f"/redfish/v1/sibling{i}"} for i in range(3)],
    }


# Mock client (doesn't actually make HTTP requests)
class MockClient:
    def __init__(self):
        self.base_url = "http://mock"

    def get(self, path):
        return {"@odata.id": path, "Id": "mock", "Name": "Mock"}


def test_deep_nesting():
    """Test that deeply nested structures don't cause recursion errors."""
    print("Creating deeply nested structure (depth=50)...")
    nested_data = create_nested_structure(50)

    print("Creating RedfishResource with nested data...")
    mock_client = MockClient()

    try:
        # This should NOT cause a recursion error anymore
        resource = RedfishResource(
            mock_client, path="/redfish/v1/test", data=nested_data, fetched=False
        )
        print("✓ Successfully created resource without recursion error!")

        # Verify lazy loading works - accessing an attribute should trigger hydration
        print(f"✓ Resource ID (lazy): {resource.Id}")
        print(f"✓ Resource Name (lazy): {resource.Name}")

        # Verify nested access works
        print("✓ Accessing nested Child resource...")
        child = resource.Child
        print(f"  Child type: {type(child).__name__}")

        # This should trigger lazy load of the child
        print(f"  Child ID: {child.Id}")

        print("\n✅ All tests passed! Recursion issue is fixed.")
        return True

    except RecursionError as e:
        print(f"❌ RecursionError still occurs: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {type(e).__name__}: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_deep_nesting()
    sys.exit(0 if success else 1)
