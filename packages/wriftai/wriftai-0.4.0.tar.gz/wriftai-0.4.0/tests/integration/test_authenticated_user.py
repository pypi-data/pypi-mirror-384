from typing import Callable

import httpx
import pytest
from respx import Router

from tests.integration.conftest import Route
from wriftai.authenticated_user import UpdateUserParams
from wriftai.client import Client, ClientOptions
from wriftai.models import ModelVisibility
from wriftai.pagination import PaginatedResponse


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_get(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
        "username": "test_username",
        "avatar_url": "https://cdn.wriftai.com/avatars/user.png",
        "name": "user",
        "bio": "Software Development Engineer",
        "urls": ["https://user.dev", "https://github.com/username"],
        "location": "Karachi, Sindh",
        "company": "WriftAI",
        "created_at": "2025-08-13T11:48:44.371093Z",
        "updated_at": "2025-08-13T11:48:44.371103Z",
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/user",
            status_code=200,
            json=expected_json,
        )
    )

    client = Client(
        client_options=ClientOptions(
            headers={},
            timeout=httpx.Timeout(15),
            transport=httpx.MockTransport(router.handler),
        )
    )

    if async_flag:
        response = await client.authenticated_user.async_get()
    else:
        response = client.authenticated_user.get()

    assert dict(response) == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_models(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "test_model",
                "created_at": "2025-08-01T10:00:00Z",
                "visibility": ModelVisibility.public,
                "description": "Test model description",
                "updated_at": "2025-08-15T14:30:00Z",
                "source_url": "https://example.com/source",
                "license_url": "https://example.com/license",
                "paper_url": "https://example.com/paper",
                "owner": {
                    "id": "user-001",
                    "username": "Kunal_Kumar",
                    "avatar_url": "https://example.com/avatar.png",
                    "name": "Kunal Kumar",
                    "bio": "Soft Dev",
                    "urls": ["https://github.com/kunal"],
                    "location": "Karachi",
                    "company": "Sych",
                    "created_at": "2024-05-10T09:00:00Z",
                    "updated_at": "2025-07-20T16:45:00Z",
                },
                "latest_version": {
                    "id": "ver-001",
                    "release_notes": "Initial release.",
                    "created_at": "2025-08-10T09:00:00Z",
                    "schemas": {
                        "prediction": {
                            "input": {"key1": "value1", "key2": 123},
                            "output": {"result": True, "message": "Success"},
                        }
                    },
                    "container_image_digest": "sha256:abc123def456ghi",
                },
                "hardware_name": "NVIDIA A100",
                "predictions_count": 2048,
            }
        ],
        "next_cursor": "abc123",
        "previous_cursor": None,
        "next_url": "/user/models?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/user/models",
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
        response = await client.authenticated_user.async_models()
    else:
        response = client.authenticated_user.models()

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_update(mock_router: Callable[..., Router], async_flag: bool) -> None:
    username = "test_username"
    name = "Updated User"
    company = "Updated Company"
    location = "Updated Location"
    bio = "Updated Bio"
    urls = ["https://user.dev", "https://github.com/username"]

    expected_json = {
        "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
        "username": username,
        "avatar_url": "https://cdn.wriftai.com/avatars/user.png",
        "name": name,
        "bio": bio,
        "urls": urls,
        "location": location,
        "company": company,
        "created_at": "2025-08-13T11:48:44.371093Z",
        "updated_at": "2025-09-01T12:00:00.000000Z",
    }
    payload: UpdateUserParams = {
        "username": username,
        "name": name,
        "company": company,
        "location": location,
        "bio": bio,
        "urls": urls,
    }
    router = mock_router(
        route=Route(
            method="PATCH",
            path="/user",
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
        response = await client.authenticated_user.async_update(params=payload)
    else:
        response = client.authenticated_user.update(params=payload)
    assert response == expected_json
