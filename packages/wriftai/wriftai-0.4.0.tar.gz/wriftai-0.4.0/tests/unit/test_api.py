from unittest.mock import AsyncMock, Mock

import pytest
from httpx import HTTPStatusError

from wriftai.api import API
from wriftai.common_types import JsonValue


def test_request() -> None:
    test_path = "/test-path"
    test_method = "GET"
    test_body: JsonValue = {"key": "value"}
    test_headers = {"test": "test"}
    test_params = {"cursor": "abc123", "page_size": 50}

    mock_sync_client = Mock()
    mock_response = Mock()
    mock_sync_client.request.return_value = mock_response

    api = API(sync_client=mock_sync_client, async_client=Mock())
    result = api.request(
        method=test_method,
        path=test_path,
        body=test_body,
        headers=test_headers,
        params=test_params,
    )

    mock_sync_client.request.assert_called_once_with(
        method=test_method,
        url=test_path,
        json=test_body,
        headers=test_headers,
        params=test_params,
    )
    mock_response.json.assert_called_once_with()

    assert result == mock_response.json.return_value


def test_request_raises_error() -> None:
    test_error_message = "HTTP error"
    mock_sync_client = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        message=test_error_message, request=Mock(), response=mock_response
    )
    mock_sync_client.request.return_value = mock_response

    api = API(sync_client=mock_sync_client, async_client=Mock())

    with pytest.raises(HTTPStatusError) as e:
        api.request(
            method="GET",
            path="/test-path",
            body={"key": "value"},
            headers={"test": "test"},
            params={"cursor": "abc123", "page_size": 50},
        )

    assert str(e.value) == test_error_message
    mock_response.raise_for_status.assert_called_once_with()


@pytest.mark.asyncio
async def test_async_request() -> None:
    test_path = "/test-path"
    test_method = "GET"
    test_params = {"cursor": "abc123", "page_size": 50}

    mock_async_client = Mock()
    mock_response = Mock()
    mock_async_client.request = AsyncMock(return_value=mock_response)

    api = API(sync_client=Mock(), async_client=mock_async_client)
    result = await api.async_request(
        method=test_method, path=test_path, params=test_params
    )

    mock_async_client.request.assert_awaited_once_with(
        method=test_method, url=test_path, json=None, headers=None, params=test_params
    )
    mock_response.json.assert_called_once_with()

    assert result == mock_response.json.return_value


@pytest.mark.asyncio
async def test_async_request_raises_error() -> None:
    test_error_message = "HTTP error"

    mock_async_client = Mock()
    mock_response = Mock()
    mock_response.raise_for_status.side_effect = HTTPStatusError(
        message=test_error_message, request=Mock(), response=mock_response
    )
    mock_async_client.request = AsyncMock(return_value=mock_response)

    api = API(sync_client=Mock(), async_client=mock_async_client)

    with pytest.raises(HTTPStatusError) as e:
        await api.async_request(
            method="GET",
            path="/test-path",
            body={"key": "value"},
            headers={"test": "test"},
            params={"cursor": "abc123", "page_size": 50},
        )

    assert str(e.value) == test_error_message
    mock_response.raise_for_status.assert_called_once_with()
