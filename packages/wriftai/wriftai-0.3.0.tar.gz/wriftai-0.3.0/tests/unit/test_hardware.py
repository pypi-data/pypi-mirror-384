from unittest.mock import AsyncMock, Mock, patch

import pytest

from wriftai.hardware import HardwareResource
from wriftai.pagination import PaginationOptions


@patch("wriftai.hardware.PaginatedResponse")
def test_list(mock_paginated_response: Mock) -> None:
    mock_requestor = Mock()
    test_response = {"key": "value"}
    mock_requestor.request.return_value = test_response

    hardware = HardwareResource(requestor=mock_requestor)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = hardware.list(pagination_options=pagination_options)

    mock_requestor.request.assert_called_once_with(
        method="GET", path=hardware._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value


@patch("wriftai.hardware.PaginatedResponse")
@pytest.mark.asyncio
async def test_async_list(mock_paginated_response: Mock) -> None:
    mock_requestor = AsyncMock()
    test_response = {"key": "value"}
    mock_requestor.async_request.return_value = test_response

    hardware = HardwareResource(requestor=mock_requestor)
    pagination_options = PaginationOptions({"cursor": "abc123", "page_size": 50})
    result = await hardware.async_list(pagination_options=pagination_options)

    mock_requestor.async_request.assert_called_once_with(
        method="GET", path=hardware._API_PREFIX, params=pagination_options
    )
    mock_paginated_response.assert_called_once_with(**test_response)
    assert result == mock_paginated_response.return_value
