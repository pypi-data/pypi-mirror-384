from typing import Callable

import httpx
import pytest
from respx import Router

from tests.integration.conftest import Route
from wriftai.client import Client, ClientOptions
from wriftai.pagination import PaginatedResponse
from wriftai.predictions import CreatePredictionParams, Status


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_get(mock_router: Callable[..., Router], async_flag: bool) -> None:
    test_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"
    expected_json = {
        "url": f"https://api.wriftai.com/v1/predictions/{test_id}",
        "id": test_id,
        "version_id": "abfb16e6-998d-49b9-941c-90dd14fc679f",
        "created_at": "2025-08-13T11:48:44.371093Z",
        "status": Status.pending,
        "webhook_url": None,
        "updated_at": "2025-08-13T11:48:44.371103Z",
        "setup_time": None,
        "execution_time": None,
        "hardware_id": "551c7d27-11e8-40a4-90d3-e8d8c22c5894",
        "error": None,
        "input": None,
        "output": None,
        "logs": None,
        "setup_logs": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path=f"/predictions/{test_id}",
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
        response = await client.predictions.async_get(prediction_id=test_id)
    else:
        response = client.predictions.get(prediction_id=test_id)

    assert dict(response) == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_get_predictions_by_id_raises_404_error(
    mock_router: Callable[..., Router], async_flag: bool
) -> None:
    test_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"

    router = mock_router(
        route=Route(
            method="GET",
            path=f"/predictions/{test_id}",
            status_code=404,
            json={"error": "Prediction not found"},
        )
    )

    client = Client(
        client_options=ClientOptions(
            headers={"Authorization": "test-token"},
            timeout=httpx.Timeout(15),
            transport=httpx.MockTransport(router.handler),
        )
    )

    with pytest.raises(httpx.HTTPStatusError) as e:
        if async_flag:
            await client.predictions.async_get(prediction_id=test_id)
        else:
            client.predictions.get(prediction_id=test_id)

    assert (
        str(e.value)
        == "Client error '404 Not Found' for url "
        + f"'https://api.wrift.ai/v1/predictions/{test_id}'\n"
        + "For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404"
    )


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_list(mock_router: Callable[..., Router], async_flag: bool) -> None:
    expected_json = {
        "items": [
            {
                "url": "https://api.wriftai.com/v1/predictions",
                "id": "test_id",
                "version_id": "abfb16e6-998d-49b9-941c-90dd14fc679f",
                "created_at": "2025-08-13T11:48:44.371093Z",
                "status": Status.pending,
                "webhook_url": None,
                "updated_at": "2025-08-13T11:48:44.371103Z",
                "setup_time": None,
                "execution_time": None,
                "hardware_id": "551c7d27-11e8-40a4-90d3-e8d8c22c5894",
                "error": None,
            }
        ],
        "next_cursor": "abc123",
        "previous_cursor": None,
        "next_url": "/predictions?cursor=abc123",
        "previous_url": None,
    }

    router = mock_router(
        route=Route(
            method="GET",
            path="/predictions",
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
        response = await client.predictions.async_list()
    else:
        response = client.predictions.list()

    # expected_json is a dictionary.
    # Although the structure matches the expected fields, static type checkers like mypy
    # may not be able to verify this due to dynamic typing.
    assert response == PaginatedResponse(**expected_json)  # type:ignore[arg-type]


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_create_prediction_latest_version(
    mock_router: Callable[..., Router], async_flag: bool
) -> None:
    model_owner = "abc"
    model_name = "textgenerator"
    params: CreatePredictionParams = {
        "input": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }

    expected_json = {
        "url": "https://api.wriftai.com",
        "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
        "version_id": "version-abc-123",
        "created_at": "2025-09-03T12:00:00Z",
        "status": Status.pending,
        "webhook_url": None,
        "updated_at": "2025-09-03T12:00:00Z",
        "setup_time": None,
        "execution_time": None,
        "hardware_id": "551c7d27-11e8-40a4-90d3-e8d8c22c5894",
        "error": None,
        "input": "test_input",
        "output": None,
        "logs": None,
        "setup_logs": None,
    }
    router = mock_router(
        route=Route(
            method="POST",
            path=f"/models/{model_owner}/{model_name}/predictions",
            status_code=202,
            json=expected_json,
        )
    )

    client = Client(
        client_options=ClientOptions(
            headers={"Authorization": "Bearer test-token"},
            timeout=httpx.Timeout(15),
            transport=httpx.MockTransport(router.handler),
        )
    )

    if async_flag:
        response = await client.predictions.async_create(
            model_owner=model_owner,
            model_name=model_name,
            params=params,
        )
    else:
        response = client.predictions.create(
            model_owner=model_owner,
            model_name=model_name,
            params=params,
        )

    assert response == expected_json


@pytest.mark.asyncio
@pytest.mark.parametrize("async_flag", [True, False])
async def test_create_prediction_specific_version(
    mock_router: Callable[..., Router], async_flag: bool
) -> None:
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"
    params: CreatePredictionParams = {
        "input": {"key": "value"},
    }

    expected_json = {
        "url": "https://api.wriftai.com",
        "id": "c12258c4-ed83-4d7b-a784-8ed55412325a",
        "version_id": version_id,
        "created_at": "2025-09-03T12:05:00Z",
        "status": Status.pending,
        "webhook_url": None,
        "updated_at": "2025-09-03T12:05:00Z",
        "setup_time": None,
        "execution_time": None,
        "hardware_id": "551c7d27-11e8-40a4-90d3-e8d8c22c5894",
        "error": None,
        "input": "test_input",
        "output": None,
        "logs": None,
        "setup_logs": None,
    }

    router = mock_router(
        route=Route(
            method="POST",
            path=f"/versions/{version_id}/predictions",
            status_code=202,
            json=expected_json,
        )
    )

    client = Client(
        client_options=ClientOptions(
            headers={"Authorization": "Bearer test-token"},
            timeout=httpx.Timeout(15),
            transport=httpx.MockTransport(router.handler),
        )
    )

    if async_flag:
        response = await client.predictions.async_create(
            version_id=version_id,
            params=params,
        )
    else:
        response = client.predictions.create(
            version_id=version_id,
            params=params,
        )

    assert response == expected_json
