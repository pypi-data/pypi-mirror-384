from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.pagination import PaginationOptions
from wriftai.users import UsersResource


def test_get() -> None:
    mock_api = Mock()
    mock_api.request = Mock()

    user = UsersResource(api=mock_api)
    username = "test_username"

    result = user.get(username=username)

    mock_api.request.assert_called_once_with("GET", f"{user._API_PREFIX}/{username}")
    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_get() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    user = UsersResource(api=mock_api)
    username = "test_username"

    result = await user.async_get(username=username)

    mock_api.async_request.assert_called_once_with(
        "GET", f"{user._API_PREFIX}/{username}"
    )
    assert result == mock_api.async_request.return_value


@patch("wriftai.users.PaginatedResponse")
def test_list(mock_paginated_response: Mock) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    users = UsersResource(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = users.list(pagination_options=pagination_options)

    mock_api.request.assert_called_once_with(
        method="GET", path=users._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.users.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_list(mock_paginated_response: Mock) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    users = UsersResource(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = await users.async_list(pagination_options=pagination_options)

    mock_api.async_request.assert_called_once_with(
        method="GET", path=users._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.users.PaginatedResponse")
def test_search(mock_paginated_response: Mock) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    users = UsersResource(api=mock_api)
    pagination_options = PaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
    })
    result = users.search(q="dummy_query", pagination_options=pagination_options)

    expected_params = {
        "cursor": pagination_options["cursor"],
        "page_size": pagination_options["page_size"],
        "q": "dummy_query",
    }

    mock_api.request.assert_called_once_with(
        method="GET",
        path=f"{users._SEARCH_API_PREFIX}{users._SEARCH_USERS_SUFFIX}",
        params=expected_params,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.users.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_search(mock_paginated_response: Mock) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    users = UsersResource(api=mock_api)
    pagination_options = PaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
    })
    result = await users.async_search(
        q="dummy_query", pagination_options=pagination_options
    )

    expected_params = {
        "cursor": pagination_options["cursor"],
        "page_size": pagination_options["page_size"],
        "q": "dummy_query",
    }

    mock_api.async_request.assert_called_once_with(
        method="GET",
        path=f"{users._SEARCH_API_PREFIX}{users._SEARCH_USERS_SUFFIX}",
        params=expected_params,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value
