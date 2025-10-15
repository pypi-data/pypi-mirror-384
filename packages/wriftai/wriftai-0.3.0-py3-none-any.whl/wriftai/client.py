"""Client module."""

import os
from importlib.metadata import version
from typing import Any, Optional, TypedDict, TypeVar

import httpx

from wriftai._api_requestor import APIRequestor
from wriftai.authenticated_user import AuthenticatedUser
from wriftai.hardware import HardwareResource
from wriftai.models import ModelsResource
from wriftai.predictions import Predictions
from wriftai.users import UsersResource
from wriftai.versions import Versions

TClient = TypeVar("TClient", httpx.Client, httpx.AsyncClient)

API_BASE_URL = "https://api.wrift.ai/v1"
AUTHORIZATION_HEADER = "Authorization"
USER_AGENT_HEADER = "User-Agent"


class ClientOptions(TypedDict):
    """Typed dictionary for specifying additional client options.

    Attributes:
        headers (Dict[str, Any]): Optional HTTP headers to include in requests.
        timeout (httpx.Timeout): Timeout configuration for requests.
            This should be an instance of `httpx.Timeout`.
        transport (httpx.BaseTransport | None): Optional custom transport for
            managing HTTP behavior.

    """

    headers: dict[str, Any]
    timeout: httpx.Timeout
    transport: httpx.BaseTransport | None


class Client:
    """WriftAI client class.

    Attributes:
        predictions (Predictions): Interface for accessing prediction related
            resources and operations.
        hardware (HardwareResource): Interface for hardware related resources
            and operations.
        authenticated_user (AuthenticatedUser): Interface for resources and operations
            related to the authenticated user.
        users (UsersResource): Interface for user related resources and
            operations.
        versions (Versions): Interface for resources and operations
            related to model versions.
        models (ModelsResource): Interface for resources and operations related
            to models.

    """

    def __init__(
        self,
        api_base_url: Optional[str] = None,
        access_token: Optional[str] = None,
        client_options: Optional[ClientOptions] = None,
    ) -> None:
        """Initializes a new instance of the Client class.

        Args:
            api_base_url (Optional[str]): The base URL for the API. If not provided,
                it falls back to the environment variable `WRIFTAI_API_BASE_URL` or
                the default api base url.
            access_token (Optional[str]): Bearer token for authorization. If not
                provided it falls back to the environment variable
                `WRIFTAI_API_ACCESS_TOKEN`.
            client_options (Optional[ClientOptions]): Additional options such as custom
                headers and timeout. Timeout defaults to 10s on all operations if not
                specified.
        """
        self._sync_client = _configure_client(
            client_type=httpx.Client,
            api_base_url=api_base_url,
            access_token=access_token,
            client_options=client_options,
        )
        self._async_client = _configure_client(
            client_type=httpx.AsyncClient,
            api_base_url=api_base_url,
            access_token=access_token,
            client_options=client_options,
        )
        self._requestor = APIRequestor(
            sync_client=self._sync_client, async_client=self._async_client
        )
        self.predictions: Predictions = Predictions(requestor=self._requestor)
        self.hardware: HardwareResource = HardwareResource(requestor=self._requestor)
        self.authenticated_user: AuthenticatedUser = AuthenticatedUser(
            requestor=self._requestor
        )
        self.users: UsersResource = UsersResource(requestor=self._requestor)
        self.versions: Versions = Versions(requestor=self._requestor)
        self.models: ModelsResource = ModelsResource(requestor=self._requestor)


def _configure_client(
    client_type: type[TClient],
    api_base_url: str | None,
    access_token: str | None,
    client_options: ClientOptions | None,
) -> TClient:
    """Builds and returns a configured HTTPX client.

    This function sets up the HTTPX client with the specified base URL, headers,
    timeout, and authorization token. If api_base_url or access_token
    are not explicitly provided, it falls back to environment variables. The timeout
    is set to 10 seconds for all operations by default.

    Args:
        client_type (type[TClient]): The HTTPX client class to instantiate.
        api_base_url (str | None): The base URL for the API. If provided it overrides
            the value from the environment variable.
        access_token (str | None): Bearer token for authorization. If provided it
            overrides the value from the environment variable.
        client_options (ClientOptions | None): Additional client options like headers
            and timeout.

    Returns:
        httpx.Client | httpx.AsyncClient : A configured HTTPX client instance.
    """
    headers = (
        client_options["headers"]
        if client_options and "headers" in client_options
        else {}
    )
    timeout = (
        client_options["timeout"]
        if client_options and "timeout" in client_options
        else httpx.Timeout(10.0)
    )

    transport = (
        client_options["transport"]
        if client_options and "transport" in client_options
        else (
            httpx.HTTPTransport()
            if client_type is httpx.Client
            else httpx.AsyncHTTPTransport()
        )
    )

    access_token = access_token or os.environ.get("WRIFTAI_API_ACCESS_TOKEN")
    api_base_url = (
        api_base_url or os.environ.get("WRIFTAI_API_BASE_URL") or API_BASE_URL
    )

    if USER_AGENT_HEADER not in headers:
        headers[USER_AGENT_HEADER] = f"wriftai-python/{version('wriftai')}"

    if access_token and AUTHORIZATION_HEADER not in headers:
        headers[AUTHORIZATION_HEADER] = f"Bearer {access_token}"

    return client_type(
        base_url=api_base_url,
        headers=headers,
        timeout=timeout,
        transport=transport,  # type:ignore[arg-type]
    )
