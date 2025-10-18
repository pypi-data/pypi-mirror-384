from typing import Callable

import httpx
import pytest
from respx import Router

from tests.integration.conftest import Route
from wriftai.client import Client, ClientOptions
from wriftai.pagination import PaginatedResponse


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_get(mock_router: Callable[..., Router], async_flag: bool) -> None:
    test_username = "user_123"
    expected_json = {
        "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
        "username": test_username,
        "avatar_url": "https://cdn.example.com/avatars/user.png",
        "name": "user",
        "bio": "Software Development Engineer",
        "urls": ["https://user.dev", "https://github.com/user"],
        "location": "Karachi, Sindh",
        "company": "Sych",
        "created_at": "2024-08-13T11:48:44.371093Z",
        "updated_at": "2025-08-13T11:48:44.371103Z",
    }

    router = mock_router(
        route=Route(
            method="GET",
            path=f"/users/{test_username}",
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
        response = await client.users.async_get(username=test_username)
    else:
        response = client.users.get(username=test_username)

    assert response == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_list(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
                "username": "test_username",
                "avatar_url": "https://cdn.example.com/avatars/user.png",
                "name": "user",
                "bio": "Software Development Engineer",
                "urls": ["https://user.dev", "https://github.com/user"],
                "location": "Karachi, Sindh",
                "company": "Sych",
                "created_at": "2024-08-13T11:48:44.371093Z",
                "updated_at": "2025-08-13T11:48:44.371103Z",
            }
        ],
        "next_cursor": "abc123",
        "previous_cursor": None,
        "next_url": "/users?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/users",
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
        response = await client.users.async_list()
    else:
        response = client.users.list()

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_search(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
                "username": "Kunal_Kumar",
                "avatar_url": "https://cdn.example.com/avatars/Kunal.png",
                "name": "Kunal",
                "bio": "Software Development Engineer",
                "urls": ["https://Kunal.dev", "https://github.com/Kunal"],
                "location": "Karachi, Sindh",
                "company": "Sych",
                "created_at": "2024-08-13T11:48:44.371093Z",
                "updated_at": "2025-08-13T11:48:44.371103Z",
            }
        ],
        "next_cursor": "abc123",
        "previous_cursor": None,
        "next_url": "/search/users?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/search/users",
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
        response = await client.users.async_search(q="dummy_query")
    else:
        response = client.users.search(q="dummy_query")

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]
