from typing import Callable

import httpx
import pytest
from respx import Router

from tests.integration.conftest import Route
from wriftai.client import Client, ClientOptions
from wriftai.pagination import PaginatedResponse


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_list(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "id": "551c7d27-11e8-40a4-90d3-e8d8c22c5894",
                "name": "NVIDIA A100",
                "gpus": 8,
                "cpus": 64,
                "ram_per_gpu_gb": 40,
                "ram_gb": 320,
                "created_at": "2025-08-13T11:48:44.371093Z",
            }
        ],
        "next_cursor": "abc123",
        "previous_cursor": None,
        "next_url": "/hardware?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/hardware",
            status_code=200,
            json=expected_json,
        )
    )

    client = Client(
        client_options=ClientOptions(
            headers={"Authorization": "test-token"},
            timeout=httpx.Timeout(15),
            transport=httpx.MockTransport(router.handler),
        )
    )

    if async_flag:
        response = await client.hardware.async_list()
    else:
        response = client.hardware.list()

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]
