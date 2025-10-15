"""Authenticated user module."""

from typing import Optional, TypedDict, cast

from wriftai._resource import Resource
from wriftai.common_types import NotRequired, User
from wriftai.models import Model
from wriftai.pagination import PaginatedResponse, PaginationOptions


class UpdateUserParams(TypedDict):
    """Parameters for updating a user.

    Attributes:
        username (NotRequired[str]): The new username of the user.
        name (NotRequired[str | None]): The new name of the user.
        bio (NotRequired[str | None]): The new biography of the user.
        urls (NotRequired[list[str] | None]): The new URLs associated with the user.
        company (NotRequired[str | None]): The new company of the user.
        location (NotRequired[str | None]): The new location of the user.
    """

    username: NotRequired[str]
    name: NotRequired[str | None]
    bio: NotRequired[str | None]
    urls: NotRequired[list[str] | None]
    company: NotRequired[str | None]
    location: NotRequired[str | None]


class AuthenticatedUser(Resource):
    """Resource for operations related to the authenticated user."""

    _API_PREFIX = "/user"

    def get(self) -> User:
        """Get the authenticated user.

        Returns:
            User: The user object.
        """
        response = self._requestor.request("GET", f"{self._API_PREFIX}")
        return cast(User, response)

    async def async_get(self) -> User:
        """Get authenticated user.

        Returns:
            User: The user object.
        """
        response = await self._requestor.async_request("GET", f"{self._API_PREFIX}")
        return cast(User, response)

    def models(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Model]:
        """List models of the authenticated user.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models
                and navigation metadata.
        """
        response = self._requestor.request(
            method="GET",
            params=pagination_options,
            path=f"{self._API_PREFIX}{self._MODELS_API_PREFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_models(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Model]:
        """List models of the authenticated user.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models
                and navigation metadata.
        """
        response = await self._requestor.async_request(
            method="GET",
            params=pagination_options,
            path=f"{self._API_PREFIX}{self._MODELS_API_PREFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    def update(
        self,
        params: UpdateUserParams,
    ) -> User:
        """Update the authenticated user.

        Args:
            params (UpdateUserParams): The fields to update.

        Returns:
            User: The updated user object.
        """
        response = self._requestor.request(
            method="PATCH",
            path=f"{self._API_PREFIX}",
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type:ignore[arg-type]
        )
        return cast(User, response)

    async def async_update(
        self,
        params: UpdateUserParams,
    ) -> User:
        """Update the authenticated user.

        Args:
            params (UpdateUserParams): The fields to update.

        Returns:
            User: The updated user object.
        """
        response = await self._requestor.async_request(
            method="PATCH",
            path=f"{self._API_PREFIX}",
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type:ignore[arg-type]
        )
        return cast(User, response)
