from copy import copy
from unittest.mock import AsyncMock, Mock, call, patch

import pytest

from wriftai.predictions import (
    CreatePredictionParams,
    Predictions,
    PredictionWithIO,
    Status,
    WaitOptions,
)


def test_get() -> None:
    test_prediction_id = "test_id"
    mock_api = Mock()
    mock_api.request = Mock()

    predictions = Predictions(api=mock_api)

    result = predictions.get(test_prediction_id)

    mock_api.request.assert_called_once_with(
        method="GET", path=f"{predictions._API_PREFIX}/{test_prediction_id}"
    )

    assert result == mock_api.request.return_value


@pytest.mark.asyncio
async def test_async_get() -> None:
    test_prediction_id = "test_id"
    mock_api = Mock()
    mock_api.async_request = AsyncMock()

    predictions = Predictions(api=mock_api)

    result = await predictions.async_get(test_prediction_id)

    mock_api.async_request.assert_awaited_once_with(
        method="GET", path=f"{predictions._API_PREFIX}/{test_prediction_id}"
    )

    assert result == mock_api.async_request.return_value


def test__prediction_path_latest_version() -> None:
    predictions = Predictions(api=Mock())
    owner = "test_owner"
    model = "test_model"
    path = predictions._prediction_path(model_owner=owner, model_name=model)
    expected = (
        f"{predictions._MODELS_API_PREFIX}/{owner}/{model}"
        f"{predictions._PREDICTIONS_API_SUFFIX}"
    )
    assert path == expected


def test__prediction_path_specific_version() -> None:
    predictions = Predictions(api=Mock())
    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"
    path = predictions._prediction_path(version_id=version_id)
    expected = (
        f"{predictions._VERSIONS_API_PREFIX}/{version_id}"
        f"{predictions._PREDICTIONS_API_SUFFIX}"
    )
    assert path == expected


def test__prediction_path_invalid_params() -> None:
    predictions = Predictions(api=Mock())
    owner = "test_owner"
    with pytest.raises(TypeError) as exc_info:
        predictions._prediction_path(model_owner=owner)
    assert str(exc_info.value) == predictions._ERROR_MSG_INVALID_PREDICTION_PARAMS


@pytest.mark.parametrize("validate_input", [True, False])
@pytest.mark.parametrize("wait", [True, False])
def test_create(validate_input: bool, wait: bool) -> None:
    mock_api = Mock()
    predictions = Predictions(api=mock_api)

    params: CreatePredictionParams = {
        "input": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }

    if validate_input:
        params["validate_input"] = validate_input

    path = "/models/test_owner/test_model/predictions"
    mock_prediction = {"id": "pred-123", "status": "succeeded"}
    wait_options = WaitOptions(poll_interval=2)

    with (
        patch.object(predictions, "_prediction_path", return_value=path) as mock_path,
        patch.object(predictions, "wait", return_value=mock_prediction) as mock_wait,
    ):
        mock_api.request.return_value = mock_prediction

        result = predictions.create(
            model_owner="test_owner",
            model_name="test_model",
            params=params,
            wait=wait,
            wait_options=wait_options,
        )

        headers = {"Validate-Input": "true"} if validate_input else None

        mock_path.assert_called_once_with("test_owner", "test_model", None)

        mock_api.request.assert_called_once_with(
            method="POST",
            path=path,
            body={"input": params["input"], "webhook_url": params["webhook_url"]},
            headers=headers,
        )

        if wait:
            mock_wait.assert_called_once_with(mock_prediction, options=wait_options)
        else:
            mock_wait.assert_not_called()

        assert result == mock_api.request.return_value


@pytest.mark.asyncio
@pytest.mark.parametrize("validate_input", [True, False])
@pytest.mark.parametrize("wait", [True, False])
async def test_async_create(validate_input: bool, wait: bool) -> None:
    mock_api = Mock()
    mock_api.async_request = AsyncMock()
    predictions = Predictions(api=mock_api)

    params: CreatePredictionParams = {
        "input": {"key": "value"},
        "webhook_url": "https://example.com/webhook",
    }
    if validate_input:
        params["validate_input"] = validate_input

    version_id = "c12258c4-ed83-4d7b-a784-8ed55412325a"
    path = f"versions/{version_id}/predictions"
    mock_prediction = {"id": "pred-123", "status": "succeeded"}
    wait_options = WaitOptions(poll_interval=2)

    with (
        patch.object(predictions, "_prediction_path", return_value=path) as mock_path,
        patch.object(
            predictions, "async_wait", return_value=mock_prediction
        ) as mock_wait,
    ):
        mock_api.async_request.return_value = mock_prediction

        result = await predictions.async_create(
            version_id=version_id, params=params, wait=wait, wait_options=wait_options
        )

        headers = {"Validate-Input": "true"} if validate_input else None

        mock_path.assert_called_once_with(None, None, version_id)

        mock_api.async_request.assert_awaited_once_with(
            method="POST",
            path=path,
            body={"input": params["input"], "webhook_url": params["webhook_url"]},
            headers=headers,
        )

        if wait:
            mock_wait.assert_called_once_with(mock_prediction, options=wait_options)
        else:
            mock_wait.assert_not_called()

        assert result == mock_api.async_request.return_value


@pytest.mark.parametrize(
    "status_sequence, expected_calls",
    [
        ([Status.pending, Status.started, Status.succeeded], 3),
        ([Status.succeeded], 0),
        ([Status.failed], 0),
    ],
)
@patch("time.sleep", return_value=None)
def test_wait(
    mock_sleep: Mock,
    status_sequence: list[Status],
    expected_calls: int,
) -> None:
    options = WaitOptions(poll_interval=2)
    base_prediction = PredictionWithIO(
        url="https://example.com",
        id="test_id",
        version_id="v1",
        created_at="2025-08-15T14:30:00Z",
        status=status_sequence[0],
        webhook_url=None,
        updated_at="2025-08-15T14:30:00Z",
        setup_time=None,
        execution_time=None,
        hardware_id="hw1",
        error=None,
        input={},
        output={},
        logs=None,
        setup_logs=None,
    )

    predictions = Predictions(api=Mock())

    responses = []
    for status in status_sequence:
        p = copy(base_prediction)
        p["status"] = status
        responses.append(p)

    with patch.object(predictions, "get", side_effect=responses) as mock_get:
        result = predictions.wait(base_prediction, options=options)

    assert result["status"] == status_sequence[-1]
    assert mock_get.call_count == expected_calls
    assert mock_sleep.call_count == max(0, expected_calls - 1)
    mock_sleep.assert_has_calls(
        [call(options.poll_interval)] * max(0, expected_calls - 1)
    )


@pytest.mark.parametrize(
    "status_sequence, expected_calls",
    [
        ([Status.pending, Status.started, Status.succeeded], 3),
        ([Status.succeeded], 0),
        ([Status.failed], 0),
    ],
)
@patch("asyncio.sleep", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_async_wait(
    mock_sleep: AsyncMock,
    status_sequence: list[Status],
    expected_calls: int,
) -> None:
    options = WaitOptions(poll_interval=2)
    base_prediction = PredictionWithIO(
        url="https://example.com",
        id="test_id",
        version_id="v1",
        created_at="2025-08-15T14:30:00Z",
        status=status_sequence[0],
        webhook_url=None,
        updated_at="2025-08-15T14:30:00Z",
        setup_time=None,
        execution_time=None,
        hardware_id="hw1",
        error=None,
        input={},
        output={},
        logs=None,
        setup_logs=None,
    )

    predictions = Predictions(api=Mock())

    responses = []
    for status in status_sequence:
        p = copy(base_prediction)
        p["status"] = status
        responses.append(p)

    with patch.object(predictions, "async_get", side_effect=responses) as mock_get:
        result = await predictions.async_wait(base_prediction, options=options)

    assert result["status"] == status_sequence[-1]
    assert mock_get.call_count == expected_calls
    assert mock_sleep.await_count == max(0, expected_calls - 1)
    mock_sleep.assert_has_awaits(
        [call(options.poll_interval)] * max(0, expected_calls - 1)
    )
