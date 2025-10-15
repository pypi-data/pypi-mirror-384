from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.authenticated_user import AuthenticatedUser, UpdateUserParams
from wriftai.pagination import PaginationOptions


def test_get() -> None:
    mock_requestor = Mock()
    mock_requestor.request = Mock()

    user = AuthenticatedUser(requestor=mock_requestor)

    result = user.get()

    mock_requestor.request.assert_called_once_with("GET", f"{user._API_PREFIX}")
    assert result == mock_requestor.request.return_value


@pytest.mark.asyncio
async def test_async_get() -> None:
    mock_requestor = Mock()
    mock_requestor.async_request = AsyncMock()

    user = AuthenticatedUser(requestor=mock_requestor)

    result = await user.async_get()

    mock_requestor.async_request.assert_called_once_with("GET", f"{user._API_PREFIX}")
    assert result == mock_requestor.async_request.return_value


@patch("wriftai.authenticated_user.PaginatedResponse")
def test_models(mock_paginated_response: Mock) -> None:
    mock_requestor = Mock()
    test_response = {"key": "value"}
    mock_requestor.request.return_value = test_response

    user = AuthenticatedUser(requestor=mock_requestor)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = user.models(pagination_options=pagination_options)

    mock_requestor.request.assert_called_once_with(
        method="GET",
        path=f"{user._API_PREFIX}{user._MODELS_API_PREFIX}",
        params=pagination_options,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@pytest.mark.asyncio
@patch("wriftai.authenticated_user.PaginatedResponse")
async def test_async_models(mock_paginated_response: Mock) -> None:
    mock_requestor = AsyncMock()
    test_response = {"key": "value"}
    mock_requestor.async_request.return_value = test_response

    user = AuthenticatedUser(requestor=mock_requestor)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = await user.async_models(pagination_options=pagination_options)

    mock_requestor.async_request.assert_called_once_with(
        method="GET",
        path=f"{user._API_PREFIX}{user._MODELS_API_PREFIX}",
        params=pagination_options,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


def test_update() -> None:
    mock_requestor = Mock()
    user = AuthenticatedUser(requestor=mock_requestor)
    payload: UpdateUserParams = {
        "username": "test_username",
        "name": "dummy_user",
        "company": "Dummy Company",
        "location": "Nowhere",
        "bio": "This is a dummy user.",
        "urls": ["https://example.com", "https://example.org"],
    }

    result = user.update(
        params=payload,
    )
    mock_requestor.request.assert_called_once_with(
        method="PATCH",
        path=f"{user._API_PREFIX}",
        body=payload,
    )
    assert result == mock_requestor.request.return_value


@pytest.mark.asyncio
async def test_async_update() -> None:
    mock_requestor = AsyncMock()
    user = AuthenticatedUser(requestor=mock_requestor)
    payload: UpdateUserParams = {
        "name": "dummy_user",
        "company": "Dummy Company",
        "location": "Nowhere",
    }
    result = await user.async_update(
        params=payload,
    )
    mock_requestor.async_request.assert_called_once_with(
        method="PATCH",
        path=f"{user._API_PREFIX}",
        body=payload,
    )
    assert result == mock_requestor.async_request.return_value
