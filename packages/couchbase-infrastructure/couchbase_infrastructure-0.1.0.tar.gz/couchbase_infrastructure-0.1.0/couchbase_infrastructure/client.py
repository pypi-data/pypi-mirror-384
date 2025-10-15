"""API client for Couchbase Capella Management API."""

import time
from typing import Any, Dict, Optional

import httpx
from rich.console import Console

from couchbase_infrastructure.config import CapellaConfig

console = Console()


class CapellaClient:
    """Client for interacting with Couchbase Capella Management API."""

    def __init__(self, config: CapellaConfig):
        """Initialize the Capella API client.

        Args:
            config: Configuration object with API credentials and settings
        """
        self.config = config
        self.base_url = f"https://{config.api_base_url}"
        self.headers = {
            "Authorization": f"Bearer {config.management_api_key}",
            "Content-Type": "application/json",
        }

    def get_current_ip(self) -> str:
        """Get the current public IP address.

        Returns:
            Current public IP address or error message
        """
        try:
            with httpx.Client(timeout=10) as client:
                response = client.get("https://api.ipify.org")
            if response.status_code == 200:
                return response.text.strip()
        except Exception:
            pass
        return "Unable to determine IP"

    def get_organization_id(self) -> str:
        """Get organization ID from config or auto-detect.

        Returns:
            Organization ID

        Raises:
            Exception: If unable to determine organization ID
        """
        if self.config.organization_id:
            return self.config.organization_id

        try:
            with httpx.Client(headers=self.headers, timeout=10) as client:
                response = client.get(f"{self.base_url}/v4/organizations")

            if response.status_code == 200:
                orgs = response.json().get("data", [])
                if orgs:
                    auto_org_id = orgs[0]["id"]
                    console.print(f"   Auto-detected Organization ID: [cyan]{auto_org_id}[/cyan]")
                    return auto_org_id

            raise Exception(f"Failed to get organizations. Status: {response.status_code}")
        except Exception as e:
            raise Exception(f"Failed to auto-detect organization ID: {e}")

    def test_connection(self, org_id: str) -> bool:
        """Test API connection and provide debugging info.

        Args:
            org_id: Organization ID to test connection with

        Returns:
            True if connection successful, False otherwise
        """
        console.print("[bold blue]🔍 Testing API connection...[/bold blue]")
        console.print(f"   Current IP: [yellow]{self.get_current_ip()}[/yellow]")
        console.print(f"   API Base URL: [yellow]{self.base_url}[/yellow]")
        console.print(f"   Organization ID: [yellow]{org_id}[/yellow]")

        try:
            with httpx.Client(headers=self.headers, timeout=10) as client:
                response = client.get(f"{self.base_url}/v4/organizations/{org_id}")

            console.print(f"   API Response Status: [yellow]{response.status_code}[/yellow]")

            if response.status_code == 401:
                console.print("   [red]❌ Authentication failed[/red] - check API key and IP allowlist")
                return False
            elif response.status_code == 200:
                console.print("   [green]✅ Authentication successful[/green]")
                return True
            else:
                console.print(f"   [yellow]⚠️  Unexpected response: {response.status_code}[/yellow]")
                return False
        except Exception as e:
            console.print(f"   [red]❌ Connection failed: {e}[/red]")
            return False

    def wait_for_resource(
        self,
        check_url: str,
        resource_type: str,
        timeout_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Poll a Capella endpoint until the resource is ready.

        Args:
            check_url: API endpoint to check (relative path starting with /)
            resource_type: Human-readable resource type name
            timeout_seconds: Optional timeout in seconds

        Returns:
            Resource data when ready

        Raises:
            Exception: If timeout is reached or polling fails
        """
        start_time = time.time()
        if timeout_seconds is None:
            console.print(
                f"   Waiting for {resource_type} to become ready... "
                "(no timeout, will wait indefinitely)"
            )
        else:
            console.print(
                f"   Waiting for {resource_type} to become ready... "
                f"(timeout: {timeout_seconds}s)"
            )

        while True:
            # Check timeout if specified
            if timeout_seconds is not None and (time.time() - start_time) > timeout_seconds:
                raise Exception(
                    f"Timeout: {resource_type} was not ready within {timeout_seconds} seconds."
                )

            try:
                with httpx.Client(headers=self.headers, timeout=30) as client:
                    response = client.get(f"{self.base_url}{check_url}")

                if response.status_code == 200:
                    data = response.json()

                    # For AI models, check status field
                    if "aiServices/models" in check_url:
                        model_data = data.get("model", {})
                        status = model_data.get("status", "unknown").lower()
                    else:
                        # Clusters use nested status.state
                        status = data.get("status", {}).get(
                            "state", data.get("currentState", "unknown")
                        ).lower()

                    elapsed = int(time.time() - start_time)
                    console.print(f"   Current status: [yellow]{status}[/yellow] (elapsed: {elapsed}s)")

                    if status in ["healthy", "ready", "deployed", "running"]:
                        console.print(f"[green]✅ {resource_type} is ready![/green]")
                        return data

                time.sleep(20)
            except Exception as e:
                console.print(f"   ... still waiting (error polling: {e})")
                time.sleep(20)

    def get(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make a GET request to the API.

        Args:
            endpoint: API endpoint (relative path starting with /)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object
        """
        with httpx.Client(headers=self.headers, timeout=30) as client:
            return client.get(f"{self.base_url}{endpoint}", **kwargs)

    def post(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make a POST request to the API.

        Args:
            endpoint: API endpoint (relative path starting with /)
            json: JSON payload
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object
        """
        with httpx.Client(headers=self.headers, timeout=60) as client:
            return client.post(f"{self.base_url}{endpoint}", json=json, **kwargs)

    def put(self, endpoint: str, json: Optional[Dict[str, Any]] = None, **kwargs) -> httpx.Response:
        """Make a PUT request to the API.

        Args:
            endpoint: API endpoint (relative path starting with /)
            json: JSON payload
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object
        """
        with httpx.Client(headers=self.headers, timeout=60) as client:
            return client.put(f"{self.base_url}{endpoint}", json=json, **kwargs)

    def delete(self, endpoint: str, **kwargs) -> httpx.Response:
        """Make a DELETE request to the API.

        Args:
            endpoint: API endpoint (relative path starting with /)
            **kwargs: Additional arguments to pass to httpx

        Returns:
            Response object
        """
        with httpx.Client(headers=self.headers, timeout=30) as client:
            return client.delete(f"{self.base_url}{endpoint}", **kwargs)
