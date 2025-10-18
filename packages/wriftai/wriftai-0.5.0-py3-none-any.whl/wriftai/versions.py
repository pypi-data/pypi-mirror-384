"""Versions module."""

from typing import Optional, TypedDict, cast

from wriftai._resource import Resource
from wriftai.common_types import Schemas, Version
from wriftai.pagination import PaginatedResponse, PaginationOptions


class CreateVersionParams(TypedDict):
    """Parameters for creating a version of a model.

    Attributes:
        release_notes (str): Information about changes such as new features,
            bug fixes, or optimizations in this version.
        schemas (Schemas): Schemas for the model version.
        container_image_digest (str): SHA256 hash digest of the version's
            container image.
    """

    release_notes: str
    schemas: Schemas
    container_image_digest: str


class Versions(Resource):
    """Resource for operations related to versions."""

    _VERSIONS_API_SUFFIX = "/versions"

    def get(self, version_id: str) -> Version:
        """Fetch a model version by its id.

        Args:
            version_id(str): The unique identifier of the version.

        Returns:
            Version: The model version.
        """
        response = self._api.request("GET", f"{self._VERSIONS_API_PREFIX}/{version_id}")
        return cast(Version, response)

    async def async_get(self, version_id: str) -> Version:
        """Fetch a model version by its id.

        Args:
            version_id(str): The unique identifier of the version.

        Returns:
            Version: The model version.
        """
        response = await self._api.async_request(
            "GET", f"{self._VERSIONS_API_PREFIX}/{version_id}"
        )
        return cast(Version, response)

    def list(
        self,
        model_owner: str,
        model_name: str,
        pagination_options: Optional[PaginationOptions] = None,
    ) -> PaginatedResponse[Version]:
        """List versions.

        Args:
            model_owner (str): Username of the model's owner.
            model_name (str): Name of the model.
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Version]: Paginated response containing versions
                and navigation metadata.
        """
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._VERSIONS_API_SUFFIX}"
        )
        response = self._api.request(method="GET", params=pagination_options, path=path)

        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_list(
        self,
        model_owner: str,
        model_name: str,
        pagination_options: Optional[PaginationOptions] = None,
    ) -> PaginatedResponse[Version]:
        """List versions.

        Args:
            model_owner (str): Username of the model's owner.
            model_name (str): Name of the model.
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Version]: Paginated response containing versions
                and navigation metadata.
        """
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._VERSIONS_API_SUFFIX}"
        )
        response = await self._api.async_request(
            method="GET", params=pagination_options, path=path
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    def delete(self, version_id: str) -> None:
        """Delete a model version by its id.

        Args:
            version_id(str): The unique identifier of the version.
        """
        self._api.request("DELETE", f"{self._VERSIONS_API_PREFIX}/{version_id}")

    async def async_delete(self, version_id: str) -> None:
        """Delete a model version by its id.

        Args:
            version_id(str): The unique identifier of the version.
        """
        await self._api.async_request(
            "DELETE", f"{self._VERSIONS_API_PREFIX}/{version_id}"
        )

    def create(
        self,
        model_owner: str,
        model_name: str,
        options: CreateVersionParams,
    ) -> Version:
        """Create a version of a model.

        Args:
            model_owner (str): Username of the model's owner.
            model_name (str): Name of the model.
            options (VersionCreateParams): Model's version creation parameters.

        Returns:
            Version: The new version.
        """
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._VERSIONS_API_SUFFIX}"
        )
        response = self._api.request(
            "POST",
            path,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=options,  # type:ignore[arg-type]
        )
        return cast(Version, response)

    async def async_create(
        self,
        model_owner: str,
        model_name: str,
        options: CreateVersionParams,
    ) -> Version:
        """Create a version of a model.

        Args:
            model_owner (str): Username of the model's owner.
            model_name (str): Name of the model.
            options (VersionCreateParams): Model's version creation parameters.

        Returns:
            Version: The new version.
        """
        path = (
            f"{self._MODELS_API_PREFIX}/{model_owner}"
            f"/{model_name}{self._VERSIONS_API_SUFFIX}"
        )
        response = await self._api.async_request(
            "POST",
            path,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=options,  # type:ignore[arg-type]
        )
        return cast(Version, response)
