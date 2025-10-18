from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.pagination import PaginationOptions
from wriftai.versions import CreateVersionParams, Versions


def test_get() -> None:
    mock_api = Mock()

    model = Versions(api=mock_api)
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"

    result = model.get(version_id=version_id)

    mock_api.request.assert_called_once_with(
        "GET", f"{model._VERSIONS_API_PREFIX}/{version_id}"
    )
    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_get() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    model = Versions(api=mock_api)
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"

    result = await model.async_get(version_id=version_id)

    mock_api.async_request.assert_called_once_with(
        "GET", f"{model._VERSIONS_API_PREFIX}/{version_id}"
    )
    assert result == mock_api.async_request.return_value


@patch("wriftai.versions.PaginatedResponse")
def test_list(mock_paginated_response: Mock) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    versions = Versions(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    model_owner = "abc"
    model_name = "textgenerator"

    result = versions.list(
        model_owner=model_owner,
        model_name=model_name,
        pagination_options=pagination_options,
    )
    path = (
        f"{versions._MODELS_API_PREFIX}/{model_owner}"
        f"/{model_name}{versions._VERSIONS_API_SUFFIX}"
    )
    mock_api.request.assert_called_once_with(
        method="GET", path=path, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.versions.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_list(mock_paginated_response: Mock) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    versions = Versions(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    model_owner = "abc"
    model_name = "textgenerator"

    result = await versions.async_list(
        model_owner=model_owner,
        model_name=model_name,
        pagination_options=pagination_options,
    )

    path = (
        f"{versions._MODELS_API_PREFIX}/{model_owner}"
        f"/{model_name}{versions._VERSIONS_API_SUFFIX}"
    )
    mock_api.async_request.assert_called_once_with(
        method="GET", path=path, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


def test_delete() -> None:
    mock_api = Mock()

    model = Versions(api=mock_api)
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"

    model.delete(version_id=version_id)

    mock_api.request.assert_called_once_with(
        "DELETE", f"{model._VERSIONS_API_PREFIX}/{version_id}"
    )


@pytest.mark.asyncio
async def test_async_delete() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    model = Versions(api=mock_api)
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"

    await model.async_delete(version_id=version_id)

    mock_api.async_request.assert_called_once_with(
        "DELETE", f"{model._VERSIONS_API_PREFIX}/{version_id}"
    )


def test_create() -> None:
    mock_api = Mock()

    model = Versions(api=mock_api)

    model_owner = "abc"
    model_name = "textgenerator"
    options: CreateVersionParams = {
        "release_notes": "Initial release with basic features",
        "container_image_digest": "sha256:" + "a" * 64,
        "schemas": {
            "prediction": {
                "input": {"key1": "value1", "key2": 123},
                "output": {"result": True, "message": "Success"},
            }
        },
    }

    result = model.create(
        model_owner=model_owner,
        model_name=model_name,
        options=options,
    )
    path = (
        f"{model._MODELS_API_PREFIX}/{model_owner}"
        f"/{model_name}{model._VERSIONS_API_SUFFIX}"
    )
    mock_api.request.assert_called_once_with(
        "POST",
        path,
        body=options,
    )

    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_create() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    model = Versions(api=mock_api)

    model_owner = "abc"
    model_name = "textgenerator"
    options: CreateVersionParams = {
        "release_notes": "Initial release with basic features",
        "container_image_digest": "sha256:" + "a" * 64,
        "schemas": {
            "prediction": {
                "input": {"key1": "value1", "key2": 123},
                "output": {"result": True, "message": "Success"},
            }
        },
    }

    result = await model.async_create(
        model_owner=model_owner,
        model_name=model_name,
        options=options,
    )

    path = (
        f"{model._MODELS_API_PREFIX}/{model_owner}"
        f"/{model_name}{model._VERSIONS_API_SUFFIX}"
    )

    mock_api.async_request.assert_called_once_with(
        "POST",
        path,
        body=options,
    )

    assert result == mock_api.async_request.return_value
