from typing import Any, Callable, TypedDict

import pytest
import respx
from httpx import Response

from wriftai.client import API_BASE_URL


class Route(TypedDict):
    method: str
    path: str
    status_code: int
    json: dict[str, Any]


@pytest.fixture(scope="function")
def mock_router() -> Callable[..., respx.Router]:
    def _create_mock(*, route: Route, base_url: str = API_BASE_URL) -> respx.Router:
        router = respx.Router(base_url=base_url)

        router.route(
            method=route.get("method", "GET"),
            path=route["path"],
        ).mock(return_value=Response(route.get("status_code", 200), json=route["json"]))

        return router

    return _create_mock
