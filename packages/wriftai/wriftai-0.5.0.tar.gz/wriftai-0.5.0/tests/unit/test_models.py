from typing import Optional
from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.models import (
    CreateModelParams,
    ModelPaginationOptions,
    ModelsResource,
    ModelsSortBy,
    ModelVisibility,
    UpdateModelParams,
)
from wriftai.pagination import PaginationOptions


def test_delete() -> None:
    mock_api = Mock()
    mock_api.request = Mock()

    model = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"

    model.delete(owner=test_owner, name=test_model_name)

    mock_api.request.assert_called_once_with(
        "DELETE", f"{model._MODELS_API_PREFIX}/{test_owner}/{test_model_name}"
    )


@pytest.mark.asyncio
async def test_async_delete() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    model = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"

    await model.async_delete(owner=test_owner, name=test_model_name)

    mock_api.async_request.assert_called_once_with(
        "DELETE", f"{model._MODELS_API_PREFIX}/{test_owner}/{test_model_name}"
    )


@patch("wriftai.models.PaginatedResponse")
@pytest.mark.parametrize("owner", [None, "test_user"])
def test_list(mock_paginated_response: Mock, owner: Optional[str]) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    models = ModelsResource(api=mock_api)
    pagination_options = ModelPaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
        "sort_by": ModelsSortBy.CREATED_AT_ASC,
    })

    path = (
        models._MODELS_API_PREFIX
        if owner is None
        else f"{models._MODELS_API_PREFIX}/{owner}"
    )

    result = models.list(pagination_options=pagination_options, owner=owner)

    mock_api.request.assert_called_once_with(
        method="GET", path=path, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.models.PaginatedResponse")
@pytest.mark.parametrize("owner", [None, "test_user"])
@pytest.mark.asyncio
async def test_async_list(mock_paginated_response: Mock, owner: Optional[str]) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    models = ModelsResource(api=mock_api)
    pagination_options = ModelPaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
        "sort_by": ModelsSortBy.CREATED_AT_ASC,
    })
    path = (
        models._MODELS_API_PREFIX
        if owner is None
        else f"{models._MODELS_API_PREFIX}/{owner}"
    )

    result = await models.async_list(pagination_options=pagination_options, owner=owner)

    mock_api.async_request.assert_called_once_with(
        method="GET", path=path, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


def test_get() -> None:
    mock_api = Mock()
    mock_api.request = Mock()

    models = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"

    result = models.get(owner=test_owner, name=test_model_name)

    mock_api.request.assert_called_once_with(
        "GET", f"{models._MODELS_API_PREFIX}/{test_owner}/{test_model_name}"
    )

    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_get() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    models = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"

    result = await models.async_get(owner=test_owner, name=test_model_name)

    mock_api.async_request.assert_called_once_with(
        "GET", f"{models._MODELS_API_PREFIX}/{test_owner}/{test_model_name}"
    )

    assert result == mock_api.async_request.return_value


def test_create() -> None:
    mock_api = Mock()
    mock_api.request = Mock()

    models = ModelsResource(api=mock_api)

    model_data: CreateModelParams = {
        "name": "test_model",
        "visibility": ModelVisibility.public,
        "hardware_name": "NVIDIA A100",
        "description": "Test model description",
        "source_url": "https://example.com/source",
        "license_url": "https://example.com/license",
        "paper_url": "https://example.com/paper",
    }

    result = models.create(model_data)

    mock_api.request.assert_called_once_with(
        method="POST",
        path=models._MODELS_API_PREFIX,
        body=model_data,
    )

    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_create() -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    models = ModelsResource(api=mock_api)

    model_data: CreateModelParams = {
        "name": "test_model",
        "visibility": ModelVisibility.public,
        "hardware_name": "NVIDIA A100",
        "description": "Test model description",
        "source_url": "https://example.com/source",
        "license_url": "https://example.com/license",
        "paper_url": "https://example.com/paper",
    }

    result = await models.async_create(model_data)

    mock_api.async_request.assert_called_once_with(
        method="POST",
        path=models._MODELS_API_PREFIX,
        body=model_data,
    )

    assert result == mock_api.async_request.return_value


def test_update() -> None:
    mock_api = Mock()
    models = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"
    payload: UpdateModelParams = {
        "name": "updated_model_name",
        "description": "Updated description",
        "source_url": "https://example.com/updated_source",
        "license_url": "https://example.com/updated_license",
        "paper_url": "https://example.com/updated_paper",
        "hardware_name": "Updated Hardware",
        "visibility": ModelVisibility.public,
    }

    result = models.update(
        owner=test_owner,
        name=test_model_name,
        params=payload,
    )

    mock_api.request.assert_called_once_with(
        method="PATCH",
        path=f"{models._MODELS_API_PREFIX}/{test_owner}/{test_model_name}",
        body=payload,
    )

    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_update() -> None:
    mock_api = AsyncMock()
    models = ModelsResource(api=mock_api)
    test_owner = "test_user"
    test_model_name = "dummy_model"
    payload: UpdateModelParams = {
        "name": "updated_model_name",
        "description": "Updated description",
        "visibility": ModelVisibility.public,
    }

    result = await models.async_update(
        owner=test_owner,
        name=test_model_name,
        params=payload,
    )

    mock_api.async_request.assert_called_once_with(
        method="PATCH",
        path=f"{models._MODELS_API_PREFIX}/{test_owner}/{test_model_name}",
        body=payload,
    )

    assert result == mock_api.async_request.return_value


@patch("wriftai.models.PaginatedResponse")
def test_search(mock_paginated_response: Mock) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    models = ModelsResource(api=mock_api)
    pagination_options = PaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
    })
    result = models.search(q="dummy_query", pagination_options=pagination_options)

    expected_params = {
        "cursor": pagination_options["cursor"],
        "page_size": pagination_options["page_size"],
        "q": "dummy_query",
    }

    mock_api.request.assert_called_once_with(
        method="GET",
        path=f"{models._SEARCH_API_PREFIX}{models._SEARCH_MODELS_SUFFIX}",
        params=expected_params,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.models.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_search(mock_paginated_response: Mock) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    models = ModelsResource(api=mock_api)
    pagination_options = PaginationOptions({
        "cursor": "abc123",
        "page_size": 50,
    })
    result = await models.async_search(
        q="dummy_query", pagination_options=pagination_options
    )

    expected_params = {
        "cursor": pagination_options["cursor"],
        "page_size": pagination_options["page_size"],
        "q": "dummy_query",
    }

    mock_api.async_request.assert_called_once_with(
        method="GET",
        path=f"{models._SEARCH_API_PREFIX}{models._SEARCH_MODELS_SUFFIX}",
        params=expected_params,
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value
