from typing import Callable, Optional

import httpx
import pytest
from respx import Router

from tests.integration.conftest import Route
from wriftai.client import Client, ClientOptions
from wriftai.models import CreateModelParams, ModelVisibility, UpdateModelParams
from wriftai.pagination import PaginatedResponse


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
@pytest.mark.parametrize("owner", [None, "test_username"])
async def test_list(
    mock_router: Callable[..., Router], async_flag: bool, owner: Optional[str]
) -> None:
    expected_owner = owner or "test_username"
    path = f"/models/{expected_owner}" if owner else "/models"
    expected_json = {
        "items": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "test_model_name",
                "created_at": "2025-08-01T10:00:00Z",
                "visibility": ModelVisibility.public,
                "description": "A computer vision model.",
                "updated_at": "2025-08-15T14:30:00Z",
                "source_url": "https://example.com/source",
                "license_url": "https://example.com/license",
                "paper_url": "https://example.com/paper",
                "owner": {
                    "id": "user-001",
                    "username": expected_owner,
                    "avatar_url": "https://example.com/avatar.png",
                    "name": "dummy user",
                    "bio": "Soft Dev",
                    "urls": ["https://github.com/dummy"],
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
        "next_url": "/models?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path=path,
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
        response = await client.models.async_list(owner=owner)
    else:
        response = client.models.list(owner=owner)

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_delete(mock_router: Callable[..., Router], async_flag: bool) -> None:
    test_owner = "test_owner"
    test_model_name = "dummy_model"

    router = mock_router(
        route=Route(
            method="DELETE",
            path=f"/models/{test_owner}/{test_model_name}",
            status_code=204,
            json={},
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
        await client.models.async_delete(owner=test_owner, name=test_model_name)
    else:
        client.models.delete(owner=test_owner, name=test_model_name)


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_get(mock_router: Callable[..., Router], async_flag: bool) -> None:
    test_owner = "test_owner"
    test_model_name = "dummy_model"

    expected_json = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": test_model_name,
        "created_at": "2025-08-01T10:00:00Z",
        "visibility": ModelVisibility.public,
        "description": "A computer vision model.",
        "updated_at": "2025-08-15T14:30:00Z",
        "source_url": "https://example.com/source",
        "license_url": "https://example.com/license",
        "paper_url": "https://example.com/paper",
        "owner": {
            "id": "user-001",
            "username": test_owner,
            "avatar_url": "https://example.com/avatar.png",
            "name": "dummy user",
            "bio": "Soft Dev",
            "urls": ["https://github.com/dummy"],
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

    router = mock_router(
        route=Route(
            method="GET",
            path=f"/models/{test_owner}/{test_model_name}",
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
        response = await client.models.async_get(owner=test_owner, name=test_model_name)
    else:
        response = client.models.get(owner=test_owner, name=test_model_name)

    assert response == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_create(mock_router: Callable[..., Router], async_flag: bool) -> None:
    params: CreateModelParams = {
        "name": "test_model",
        "visibility": ModelVisibility.private,
        "hardware_name": "NVIDIA A100",
        "description": "Test model description",
        "source_url": "https://example.com/source",
        "license_url": "https://example.com/license",
        "paper_url": "https://example.com/paper",
    }

    expected_json = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": params["name"],
        "created_at": "2025-08-01T10:00:00Z",
        "visibility": params["visibility"],
        "description": params["description"],
        "updated_at": "2025-08-15T14:30:00Z",
        "source_url": params["source_url"],
        "license_url": params["license_url"],
        "paper_url": params["paper_url"],
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
        "hardware_name": params["hardware_name"],
        "predictions_count": 2048,
    }

    router = mock_router(
        route=Route(
            method="POST",
            path="/models",
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
        response = await client.models.async_create(params)
    else:
        response = client.models.create(params)
    assert response == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_update(mock_router: Callable[..., Router], async_flag: bool) -> None:
    test_owner = "test_owner"
    test_model_name = "dummy_model"
    description = "Updated description"
    source_url = "https://example.com/updated_source"
    license_url = "https://license.com/updated_license"
    paper_url = "https://paper.com/updated_paper"
    hardware_name = "Updated Hardware"

    expected_json = {
        "id": "123e4567-e89b-12d3-a456-426614174000",
        "name": test_model_name,
        "created_at": "2025-08-01T10:00:00Z",
        "visibility": ModelVisibility.public,
        "description": description,
        "updated_at": "2025-08-15T14:30:00Z",
        "source_url": source_url,
        "license_url": license_url,
        "paper_url": paper_url,
        "owner": {
            "id": "user-001",
            "username": test_owner,
            "avatar_url": "https://example.com/avatar.png",
            "name": "dummy user",
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
        "hardware_name": hardware_name,
        "predictions_count": 2048,
    }
    payload: UpdateModelParams = {
        "description": description,
        "source_url": source_url,
        "license_url": license_url,
        "paper_url": paper_url,
        "hardware_name": hardware_name,
    }
    router = mock_router(
        route=Route(
            method="PATCH",
            path=f"/models/{test_owner}/{test_model_name}",
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
        response = await client.models.async_update(
            owner=test_owner,
            name=test_model_name,
            params=payload,
        )
    else:
        response = client.models.update(
            owner=test_owner,
            name=test_model_name,
            params=payload,
        )
    assert response == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_search(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "name": "test_model_name",
                "created_at": "2025-08-01T10:00:00Z",
                "visibility": ModelVisibility.public,
                "description": "A computer vision model.",
                "updated_at": "2025-08-15T14:30:00Z",
                "source_url": "https://example.com/source",
                "license_url": "https://example.com/license",
                "paper_url": "https://example.com/paper",
                "owner": {
                    "id": "user-001",
                    "username": "test_username",
                    "avatar_url": "https://example.com/avatar.png",
                    "name": "dummy user",
                    "bio": "Soft Dev",
                    "urls": ["https://github.com/dummy"],
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
        "next_url": "/search/models?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/search/models",
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
        response = await client.models.async_search(q="dummy_query")
    else:
        response = client.models.search(q="dummy_query")

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]
