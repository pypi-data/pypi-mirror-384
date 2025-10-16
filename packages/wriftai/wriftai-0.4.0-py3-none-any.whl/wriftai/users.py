"""User module."""

from typing import Optional, cast

from wriftai._resource import Resource
from wriftai.common_types import User
from wriftai.pagination import PaginatedResponse, PaginationOptions


class UsersResource(Resource):
    """Resource for operations related to users."""

    _API_PREFIX = "/users"
    _SEARCH_USERS_SUFFIX = "/users"

    def get(self, username: str) -> User:
        """Fetch a user by their username.

        Args:
            username(str): The username of the user.

        Returns:
            User: The user object.
        """
        response = self._api.request("GET", f"{self._API_PREFIX}/{username}")
        return cast(User, response)

    async def async_get(self, username: str) -> User:
        """Fetch a user by their username.

        Args:
            username(str): The username of the user.

        Returns:
            User: The user object.
        """
        response = await self._api.async_request(
            "GET", f"{self._API_PREFIX}/{username}"
        )
        return cast(User, response)

    def list(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[User]:
        """List users.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[User]: Paginated response containing users
                and navigation metadata.
        """
        response = self._api.request(
            method="GET", params=pagination_options, path=self._API_PREFIX
        )

        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_list(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[User]:
        """List users.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[User]: Paginated response containing users
                and navigation metadata.
        """
        response = await self._api.async_request(
            method="GET", params=pagination_options, path=self._API_PREFIX
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    def search(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[User]:
        """Search users.

        Args:
            q (str): The search query.
            pagination_options (Optional[PaginationOptions]): Optional settings to
                control pagination behavior.

        Returns:
            PaginatedResponse[User]: Paginated response containing users
                and navigation metadata.
        """
        params = self._build_search_params(q, pagination_options)

        response = self._api.request(
            method="GET",
            params=params,
            path=f"{self._SEARCH_API_PREFIX}{self._SEARCH_USERS_SUFFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_search(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[User]:
        """Search Users.

        Args:
            q (str): The search query.
            pagination_options (Optional[PaginationOptions]): Optional settings to
                control pagintation behavior.

        Returns:
            PaginatedResponse[User]: Paginated response containing users
                and navigation metadata.
        """
        params = self._build_search_params(q, pagination_options)

        response = await self._api.async_request(
            method="GET",
            params=params,
            path=f"{self._SEARCH_API_PREFIX}{self._SEARCH_USERS_SUFFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]
