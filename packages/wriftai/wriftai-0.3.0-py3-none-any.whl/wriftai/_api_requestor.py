"""API requestor module."""

from collections.abc import Mapping
from typing import Any, Optional, cast

from httpx import AsyncClient, Client

from wriftai.common_types import JsonValue


class APIRequestor:
    """Encapsulates HTTP request handling for sync and async clients."""

    _sync_client: Client
    _async_client: AsyncClient

    def __init__(self, sync_client: Client, async_client: AsyncClient) -> None:
        """Initializes the _APIRequestor with synchronous and asynchronous HTTP clients.

        Args:
            sync_client (Client): An instance of a synchronous HTTP client.
            async_client (AsyncClient): An instance of an asynchronous HTTP client.
        """
        self._sync_client = sync_client
        self._async_client = async_client

    def request(
        self,
        method: str,
        path: str,
        body: Optional[JsonValue] = None,
        headers: Optional[dict[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> JsonValue:
        """Sends a synchronous HTTP request using the configured sync client.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            path (str): The URL path to send the request to.
            body (Optional[JsonValue]): The JSON body to include in
                the request.
            headers (Optional[dict[str, Any]]): Optional HTTP headers to
                include in the request.
            params (Optional[Mapping[str, Any]]): Optional query parameters.


        Returns:
            JsonValue: The json response received from the server.
        """
        response = self._sync_client.request(
            method=method, url=path, json=body, headers=headers, params=params
        )
        response.raise_for_status()
        return cast(JsonValue, response.json())

    async def async_request(
        self,
        method: str,
        path: str,
        body: JsonValue = None,
        headers: Optional[dict[str, Any]] = None,
        params: Optional[Mapping[str, Any]] = None,
    ) -> JsonValue:
        """Sends an asynchronous HTTP request using the configured async client.

        Args:
            method (str): The HTTP method to use (e.g., 'GET', 'POST').
            path (str): The URL path to send the request to.
            body (Optional[JsonValue]): The JSON body to include in
                the request.
            headers (Optional[dict[str, Any]]): Optional HTTP headers to
                include in the request.
            params (Optional[Mapping[str, Any]]): Optional query parameters.


        Returns:
            JsonValue: The json response received from the server.
        """
        response = await self._async_client.request(
            method=method, url=path, json=body, headers=headers, params=params
        )
        response.raise_for_status()
        return cast(JsonValue, response.json())
