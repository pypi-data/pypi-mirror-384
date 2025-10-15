from unittest.mock import Mock, call, patch

import httpx

from wriftai.client import (
    API_BASE_URL,
    AUTHORIZATION_HEADER,
    USER_AGENT_HEADER,
    Client,
    ClientOptions,
    _configure_client,
)


@patch("wriftai.client._configure_client")
@patch("wriftai.client.Predictions")
@patch("wriftai.client.APIRequestor")
@patch("wriftai.client.AuthenticatedUser")
@patch("wriftai.client.UsersResource")
@patch("wriftai.client.HardwareResource")
@patch("wriftai.client.ModelsResource")
@patch("wriftai.client.Versions")
def test_client_class(
    mock_versions: Mock,
    mock_models_resource: Mock,
    mock_hardware: Mock,
    mock_users_resource: Mock,
    mock_authenticated_user: Mock,
    mock__requestor: Mock,
    mock_predictions: Mock,
    mock__configure_client: Mock,
) -> None:
    test_api_base_url = "https://api.wrift.ai"
    test_access_token = "A9f3D4eH2jK7LmN0Q1rTzX8vY6bC5uW4"  # noqa:S105
    test_client_options = ClientOptions(
        headers={AUTHORIZATION_HEADER: "test-auth"},
        timeout=httpx.Timeout(20),
        transport=Mock(),
    )
    mock__sync_client = Mock()
    mock__async_client = Mock()

    mock__configure_client.side_effect = [mock__sync_client, mock__async_client]

    mock_client = Client(
        api_base_url=test_api_base_url,
        access_token=test_access_token,
        client_options=test_client_options,
    )

    assert mock_client._sync_client == mock__sync_client
    assert mock_client._async_client == mock__async_client
    assert mock_client._requestor == mock__requestor.return_value
    assert mock_client.predictions == mock_predictions.return_value
    assert mock_client.hardware == mock_hardware.return_value
    assert mock_client.versions == mock_versions.return_value
    assert mock_client.authenticated_user == mock_authenticated_user.return_value
    assert mock_client.users == mock_users_resource.return_value
    assert mock_client.models == mock_models_resource.return_value

    mock__configure_client.assert_has_calls([
        call(
            client_type=httpx.Client,
            api_base_url=test_api_base_url,
            access_token=test_access_token,
            client_options=test_client_options,
        ),
        call(
            client_type=httpx.AsyncClient,
            api_base_url=test_api_base_url,
            access_token=test_access_token,
            client_options=test_client_options,
        ),
    ])
    mock__requestor.assert_called_once_with(
        sync_client=mock__sync_client, async_client=mock__async_client
    )
    mock_predictions.assert_called_once_with(requestor=mock__requestor.return_value)
    mock_users_resource.assert_called_once_with(requestor=mock__requestor.return_value)
    mock_hardware.assert_called_once_with(requestor=mock__requestor.return_value)
    mock_versions.assert_called_once_with(requestor=mock__requestor.return_value)
    mock_authenticated_user.assert_called_once_with(
        requestor=mock__requestor.return_value
    )
    mock_models_resource.assert_called_once_with(requestor=mock__requestor.return_value)


@patch("wriftai.client.os")
@patch("wriftai.client.version")
@patch("wriftai.client.httpx.HTTPTransport")
@patch("wriftai.client.httpx.AsyncHTTPTransport")
def test__configure_client_with_None_args(
    mock_async_http_transport: Mock,
    mock_http_transport: Mock,
    mock_version: Mock,
    mock_os: Mock,
) -> None:
    mock_client_type = Mock()
    test_env_var = "test-env-var"

    mock_os.environ.get.return_value = test_env_var

    result = _configure_client(
        client_type=mock_client_type,
        api_base_url=None,
        access_token=None,
        client_options=None,
    )

    mock_os.environ.get.assert_has_calls([
        call("WRIFTAI_API_ACCESS_TOKEN"),
        call("WRIFTAI_API_BASE_URL"),
    ])

    mock_client_type.assert_called_once_with(
        base_url=test_env_var,
        headers={
            USER_AGENT_HEADER: f"wriftai-python/{mock_version.return_value}",
            AUTHORIZATION_HEADER: f"Bearer {test_env_var}",
        },
        timeout=httpx.Timeout(10.0),
        transport=mock_async_http_transport.return_value,
    )
    mock_http_transport.assert_not_called()
    assert result == mock_client_type.return_value


@patch("wriftai.client.os")
def test__configure_client_with_args_provided(mock_os: Mock) -> None:
    mock_client_type = Mock()
    test_api_base_url = "https://api.wrift.ai"
    test_access_token = "A9f3D4eH2jK7LmN0Q1rTzX8vY6bC5uW4"  # noqa:S105
    mock_transport = Mock()

    test_client_options = ClientOptions(
        headers={
            USER_AGENT_HEADER: "wriftai-python/0.0.1",
            AUTHORIZATION_HEADER: f"Bearer {test_access_token}",
        },
        timeout=httpx.Timeout(20.0),
        transport=mock_transport,
    )

    result = _configure_client(
        client_type=mock_client_type,
        api_base_url=test_api_base_url,
        access_token=test_access_token,
        client_options=test_client_options,
    )

    mock_os.environ.get.assert_not_called()

    mock_client_type.assert_called_once_with(
        base_url=test_api_base_url,
        headers=test_client_options["headers"],
        timeout=test_client_options["timeout"],
        transport=mock_transport,
    )
    assert result == mock_client_type.return_value


@patch("wriftai.client.os")
@patch("wriftai.client.version")
def test__configure_client_with_args_and_env_vars_provided(
    mock_version: Mock, mock_os: Mock
) -> None:
    mock_client_type = Mock()
    test_api_base_url = "https://api.wrift.ai"
    test_access_token = "A9f3D4eH2jK7LmN0Q1rTzX8vY6bC5uW4"  # noqa:S105
    mock_transport = Mock()

    test_client_options = ClientOptions(
        headers={
            USER_AGENT_HEADER: "wriftai-python/0.0.1",
            AUTHORIZATION_HEADER: f"Bearer {test_access_token}",
        },
        timeout=httpx.Timeout(20.0),
        transport=mock_transport,
    )

    mock_os.environ.get.return_value = "test-env-var"

    result = _configure_client(
        client_type=mock_client_type,
        api_base_url=test_api_base_url,
        access_token=test_access_token,
        client_options=test_client_options,
    )

    # assert environment variables not used.
    mock_os.environ.get.assert_not_called()
    # assert version not called.
    mock_version.assert_not_called()

    mock_client_type.assert_called_once_with(
        base_url=test_api_base_url,
        headers=test_client_options["headers"],
        timeout=test_client_options["timeout"],
        transport=mock_transport,
    )
    assert result == mock_client_type.return_value


@patch("wriftai.client.os")
def test__configure_client_with_no_args_and_no_env_var(
    mock_os: Mock,
) -> None:
    mock_client_type = Mock()
    mock_transport = Mock()

    test_client_options = ClientOptions(
        headers={
            USER_AGENT_HEADER: "wriftai-python/0.0.1",
        },
        timeout=httpx.Timeout(20.0),
        transport=mock_transport,
    )

    # no env variable set.
    mock_os.environ.get.return_value = None

    result = _configure_client(
        client_type=mock_client_type,
        api_base_url=None,
        access_token=None,
        client_options=test_client_options,
    )

    mock_os.environ.get.assert_has_calls([
        call("WRIFTAI_API_ACCESS_TOKEN"),
        call("WRIFTAI_API_BASE_URL"),
    ])

    mock_client_type.assert_called_once_with(
        base_url=API_BASE_URL,
        headers=test_client_options["headers"],
        timeout=test_client_options["timeout"],
        transport=mock_transport,
    )
    assert result == mock_client_type.return_value
