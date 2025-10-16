"""
rackfish - Dynamic Redfish Client Library

A lightweight, dynamic Python client for interacting with Redfish BMC APIs.
Provides intuitive access to server hardware management through lazy-loaded
object graphs, automatic OEM property surfacing, and validated action invocation.

Example:
    >>> from rackfish import RedfishClient
    >>> client = RedfishClient("https://bmc.example.com", "admin", "password")
    >>> root = client.connect()
    >>> for system in client.Systems:
    ...     print(system.PowerState)
    >>> client.logout()

For more examples, see the documentation at:
https://github.com/thefrolov/rackfish
"""

from .client import RedfishClient, RedfishError, RedfishResource

__version__ = "1.0.3"
__author__ = "Dmitrii Frolov"
__email__ = "thefrolov@mts.ru"
__license__ = "MIT"

__all__ = ["RedfishClient", "RedfishError", "RedfishResource"]
