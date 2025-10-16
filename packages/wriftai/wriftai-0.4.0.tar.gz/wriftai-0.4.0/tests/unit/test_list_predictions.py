from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.pagination import PaginationOptions
from wriftai.predictions import Predictions


@patch("wriftai.predictions.PaginatedResponse")
def test_list(mock_paginated_response: Mock) -> None:
    mock_api = Mock()
    test_response = {"key": "value"}
    mock_api.request.return_value = test_response

    prediction = Predictions(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = prediction.list(pagination_options=pagination_options)

    mock_api.request.assert_called_once_with(
        method="GET", path=prediction._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.predictions.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_list(mock_paginated_response: Mock) -> None:
    mock_api = AsyncMock()
    test_response = {"key": "value"}
    mock_api.async_request.return_value = test_response

    prediction = Predictions(api=mock_api)
    pagination_options = PaginationOptions({"cursor": "abc123"})
    result = await prediction.async_list(pagination_options=pagination_options)

    mock_api.async_request.assert_called_once_with(
        method="GET", path=prediction._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value
