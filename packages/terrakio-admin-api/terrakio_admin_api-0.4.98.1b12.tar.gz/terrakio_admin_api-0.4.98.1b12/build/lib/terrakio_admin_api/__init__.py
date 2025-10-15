# terrakio_admin/__init__.py
"""
Terrakio Admin API Client

An admin API client for Terrakio.
"""

__version__ = "0.4.5"

from terrakio_core import AsyncClient as CoreAsyncClient
from terrakio_core import Client as CoreClient
from terrakio_core.endpoints.group_management import AdminGroupManagement

class AsyncClient(CoreAsyncClient):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = AdminGroupManagement(self)

class Client(CoreClient):
    """Synchronous version of the Terrakio Admin API client with full admin permissions."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.groups = AdminGroupManagement(self)

__all__ = ['AsyncClient', 'Client']