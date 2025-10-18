"""Resource module."""

from abc import ABC
from collections.abc import Mapping
from typing import Any, Optional

from wriftai.api import API
from wriftai.pagination import PaginationOptions


class Resource(ABC):
    """Abstract base class for API resources."""

    _api: API
    _MODELS_API_PREFIX = "/models"
    _VERSIONS_API_PREFIX = "/versions"
    _SEARCH_API_PREFIX = "/search"

    def __init__(self, api: API) -> None:
        """Initializes the Resource with an API instance.

        Args:
            api (API): An instance of the API class.
        """
        self._api = api

    def _build_search_params(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> Mapping[str, Any]:
        """Build search parameters.

        Args:
            q (str): The search query.
            pagination_options (Optional[PaginationOptions]): Optional settings to
                control pagination behavior.

        Returns:
            Mapping[str, Any]: Parameters for searching.
        """
        params = {**pagination_options} if pagination_options else {}
        params["q"] = q

        return params
