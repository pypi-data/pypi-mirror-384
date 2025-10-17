"""
Simple HTTP client for Orb Cloud API.
"""

import httpx
from typing import Dict, Any, Optional, List

try:
    from .models import Device, TempDatasetsRequest, Organization
except ImportError:
    # Handle direct execution
    from models import Device, TempDatasetsRequest, Organization

class OrbCloudClientBase(object):
    def __init__(self, base_url: str = "https://panel.orb.net", token: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.headers = {"Content-Type": "application/json"}
        if token:
            self.headers["Authorization"] = f"Bearer {token}"

    def _get_organization_devices(self, response: httpx.Response) -> List[Device]:
        """Get list of devices for the organization from a response."""
        response.raise_for_status()
        return [Device(**device) for device in response.json()]

    def _configure_temporary_datasets(self, response: httpx.Response) -> Dict[str, Any]:
        """Process the response for configuring temporary datasets."""
        response.raise_for_status()
        return response.json()

    def _get_organizations(self, response: httpx.Response) -> List[Organization]:
        """Get list of organizations accessible with the provided token."""
        response.raise_for_status()
        return [Organization(**org) for org in response.json()]

class OrbCloudClient(OrbCloudClientBase):
    """Simple HTTP client for Orb Cloud API."""

    def __init__(self, base_url: str = "https://panel.orb.net", token: Optional[str] = None):
        super().__init__(base_url, token)
        self.client = httpx.Client(base_url=self.base_url, headers=self.headers)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def get_organization_devices(self, organization_id: str) -> List[Device]:
        """Get list of devices for the organization."""
        response = self.client.get(f"/api/v2/organization/{organization_id}/devices")
        return self._get_organization_devices(response)

    def configure_temporary_datasets(self, device_id: str, temp_datasets_request: TempDatasetsRequest) -> Dict[str, Any]:
        """Enable temporary data reporting to a custom endpoint with a given config for a specified duration."""
        response = self.client.post(f"/api/v1/device/{device_id}/temp-datasets", json=temp_datasets_request.model_dump())
        return self._configure_temporary_datasets(response)

    def get_organizations(self) -> List[Organization]:
        """Get list of organizations accessible with the provided token."""
        response = self.client.get("/api/v2/organizations")
        return self._get_organizations(response)

    def request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make a raw HTTP request for any other endpoints."""
        return self.client.request(method, endpoint, **kwargs)


class OrbCloudClientAsync(OrbCloudClientBase):
    """Simple async HTTP client for Orb Cloud API."""

    def __init__(self, base_url: str = "https://panel.orb.net", token: Optional[str] = None):
        super().__init__(base_url, token)
        self.client = httpx.AsyncClient(base_url=self.base_url, headers=self.headers)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def close(self):
        """Close the HTTP client."""
        await self.client.aclose()

    async def get_organization_devices(self, organization_id: str) -> List[Device]:
        """Get list of devices for the organization."""
        response = await self.client.get(f"/api/v2/organization/{organization_id}/devices")
        return self._get_organization_devices(response)

    async def configure_temporary_datasets(self, device_id: str, temp_datasets_request: TempDatasetsRequest) -> Dict[str, Any]:
        """Enable temporary data reporting to a custom endpoint with a given config for a specified duration."""
        response = await self.client.post(f"/api/v1/device/{device_id}/temp-datasets", json=temp_datasets_request.model_dump())
        return self._configure_temporary_datasets(response)

    async def get_organizations(self) -> List[Organization]:
        """Get list of organizations accessible with the provided token."""
        response = await self.client.get("/api/v2/organizations")
        return self._get_organizations(response)

    async def request(self, method: str, endpoint: str, **kwargs) -> httpx.Response:
        """Make a raw async HTTP request for any other endpoints."""
        return await self.client.request(method, endpoint, **kwargs)