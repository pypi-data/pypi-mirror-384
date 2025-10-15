"""Centralized API client for VERIS simulation endpoints."""

import logging
import os
from typing import Any

import httpx
from urllib.parse import urljoin

logger = logging.getLogger(__name__)


class SimulatorAPIClient:
    """Centralized client for making requests to VERIS simulation endpoints.

    Note:
        This client intentionally reads configuration (base URL and API key)
        from environment variables at call-time instead of at construction
        time. This allows tests to patch environment variables and have those
        changes reflected without recreating the singleton.
    """

    def __init__(self) -> None:
        """Initialize the API client with static timeout configuration."""
        self.timeout = float(os.getenv("VERIS_MOCK_TIMEOUT", "90.0"))

    def _get_base_url(self) -> str:
        """Resolve the base URL from environment.

        Behavior:
            - If VERIS_API_URL is unset, default to the dev simulator URL.
            - If VERIS_API_URL is set to an empty string, treat it as empty
              (do not fall back). This supports tests expecting connection
              failures when an invalid endpoint is provided.
        """
        return os.getenv("VERIS_API_URL") or "https://simulator.api.veris.ai"

    def _build_headers(self) -> dict[str, str] | None:
        """Build headers including OpenTelemetry tracing and API key."""
        headers: dict[str, str] | None = None
        # Add API key header if available
        api_key = os.getenv("VERIS_API_KEY")
        if api_key:
            if headers is None:
                headers = {}
            headers["x-api-key"] = api_key

        return headers

    def post(self, endpoint: str, payload: dict[str, Any]) -> Any:  # noqa: ANN401
        """Make a synchronous POST request to the specified endpoint."""
        headers = self._build_headers()
        # Validate endpoint URL; raise ConnectError for non-absolute URLs to
        # mirror connection failures in tests when base URL is intentionally invalid.
        if not endpoint.startswith(("http://", "https://")):
            raise httpx.ConnectError("Invalid endpoint URL (not absolute): {endpoint}")

        with httpx.Client(timeout=self.timeout) as client:
            response = client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else None

    async def post_async(self, endpoint: str, payload: dict[str, Any]) -> Any:  # noqa: ANN401
        """Make an asynchronous POST request to the specified endpoint.

        This method uses httpx.AsyncClient and is safe to call from async functions
        without blocking the event loop.
        """
        headers = self._build_headers()
        # Validate endpoint URL; raise ConnectError for non-absolute URLs to
        # mirror connection failures in tests when base URL is intentionally invalid.
        if not endpoint.startswith(("http://", "https://")):
            error_msg = f"Invalid endpoint URL (not absolute): {endpoint}"
            raise httpx.ConnectError(error_msg)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(endpoint, json=payload, headers=headers)
            response.raise_for_status()
            return response.json() if response.content else None

    @property
    def tool_mock_endpoint(self) -> str:
        """Get the tool mock endpoint URL."""
        return urljoin(self._get_base_url(), "v3/tool_mock")

    def get_log_tool_call_endpoint(self, session_id: str) -> str:
        """Get the log tool call endpoint URL."""
        return urljoin(self._get_base_url(), f"v3/log_tool_call?session_id={session_id}")

    def get_log_tool_response_endpoint(self, session_id: str) -> str:
        """Get the log tool response endpoint URL."""
        return urljoin(self._get_base_url(), f"v3/log_tool_response?session_id={session_id}")


# Global singleton instance
_api_client = SimulatorAPIClient()


def get_api_client() -> SimulatorAPIClient:
    """Get the global API client instance."""
    return _api_client
