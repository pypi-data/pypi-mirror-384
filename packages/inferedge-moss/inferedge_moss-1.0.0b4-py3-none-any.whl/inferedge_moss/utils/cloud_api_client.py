"""
Cloud API client for making requests to the Moss cloud service.
"""

from typing import Any, Dict, Optional, TypeVar

import httpx
from moss_core import CLOUD_API_BASE_URL

T = TypeVar("T")


class CloudApiClient:
    """
    Cloud API client for making requests to the Moss cloud service.
    """

    def __init__(self, project_id: str, project_key: str) -> None:
        """
        Initialize the cloud API client.

        Args:
            project_id: The project ID for authentication
            project_key: The project key for authentication
        """
        self.project_id = project_id
        self.project_key = project_key

    async def make_request(
        self,
        action: str,
        additional_data: Optional[Dict[str, Any]] = None,
        timeout: float = 30.0,
    ) -> Any:
        """
        Makes a POST request to the cloud API.

        Args:
            action: The action to perform
            additional_data: Additional data to include in the request
            timeout: Request timeout in seconds

        Returns:
            The response data from the API

        Raises:
            Exception: If the request fails or returns an error
        """
        request_body = {
            "action": action,
            "projectId": self.project_id,
            "projectKey": self.project_key,
        }

        if additional_data:
            request_body.update(additional_data)

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    CLOUD_API_BASE_URL,
                    headers={"Content-Type": "application/json"},
                    json=request_body,
                )

                if not response.is_success:
                    raise Exception(f"HTTP error! status: {response.status_code}")

                data = response.json()
                return data

        except httpx.RequestError as error:
            raise Exception(f"Cloud API request failed: {str(error)}")
        except Exception as error:
            raise Exception(f"Cloud API request failed: {str(error)}")
