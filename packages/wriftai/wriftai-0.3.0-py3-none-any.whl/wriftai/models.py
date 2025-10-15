"""Models module."""

from typing import Optional, TypedDict, cast

from wriftai._resource import Resource
from wriftai.common_types import NotRequired, StrEnum, User, Version
from wriftai.pagination import PaginatedResponse, PaginationOptions


class ModelVisibility(StrEnum):
    """Model visibility states."""

    private = "private"
    public = "public"


class Model(TypedDict):
    """Represents a model.

    Attributes:
        id (str): The unique identifier of the model.
        name (str): The name of the model.
        created_at (str): The time when the model was created.
        visibility (ModelVisibility): The visibility of the model.
        description (str | None): Description of the model.
        updated_at (str | None): The time when the model was updated.
        source_url (str | None): Source url from where the model's code can be
            referenced.
        license_url (str | None): License url where the model's usage is specified.
        paper_url (str | None): Paper url from where research info on the model
            can be found.
        owner (User): The details of the owner of the model.
        latest_version (Version | None): The details of the latest version of the model.
        hardware_name (str): The name of the hardware used by the model.
        predictions_count (int): The total number of predictions created across all
            versions of the model.
    """

    id: str
    name: str
    created_at: str
    visibility: ModelVisibility
    description: str | None
    updated_at: str | None
    source_url: str | None
    license_url: str | None
    paper_url: str | None
    owner: User
    latest_version: Version | None
    hardware_name: str
    predictions_count: int


class ModelsSortBy(StrEnum):
    """Enumeration of possible sorting options for querying models."""

    CREATED_AT_ASC = "created_at_asc"
    PREDICTION_COUNT_DESC = "prediction_count_desc"


class ModelPaginationOptions(PaginationOptions):
    """Pagination options for querying models.

    Attribute:
        sort_by (ModelsSortBy): The sorting criteria.
    """

    sort_by: ModelsSortBy


class UpdateModelParams(TypedDict):
    """Parameters for updating a model.

    Attributes:
        name (NotRequired[str]): The name of the model.
        description (NotRequired[str | None]): Description of the model.
        visibility (NotRequired[ModelVisibility]): The visibility of the model.
        hardware_name (NotRequired[str]): The name of the hardware used by the model.
        source_url (NotRequired[str | None]): Source url from where the model's code
            can be referenced.
        license_url (NotRequired[str | None]): License url where the model's usage is
            specified.
        paper_url (NotRequired[str | None]): Paper url from where research info on the
            model can be found.
    """

    name: NotRequired[str]
    description: NotRequired[str | None]
    visibility: NotRequired[ModelVisibility]
    hardware_name: NotRequired[str]
    source_url: NotRequired[str | None]
    license_url: NotRequired[str | None]
    paper_url: NotRequired[str | None]


class CreateModelParams(TypedDict):
    """Parameters for creating a model.

    Attributes:
        name (str): The name of the model.
        hardware_name (str): The name of the hardware used by the model.
        visibility (NotRequired[ModelVisibility]): The visibility of the model.
        description (NotRequired[str | None]): Description of the model.
        source_url (NotRequired[str] | None): Source url from where the model's code
            can be referenced.
        license_url (NotRequired[str] | None): License url where the model's usage is
            specified.
        paper_url (NotRequired[str] | None): Paper url from where research info on the
            model can be found.
    """

    name: str
    hardware_name: str
    visibility: NotRequired[ModelVisibility]
    description: NotRequired[str | None]
    source_url: NotRequired[str | None]
    license_url: NotRequired[str | None]
    paper_url: NotRequired[str | None]


class ModelsResource(Resource):
    """Resource for operations related to models."""

    _SEARCH_MODELS_SUFFIX = "/models"

    def delete(self, owner: str, name: str) -> None:
        """Delete a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.
        """
        self._requestor.request("DELETE", f"{self._MODELS_API_PREFIX}/{owner}/{name}")

    async def async_delete(self, owner: str, name: str) -> None:
        """Delete a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.
        """
        await self._requestor.async_request(
            "DELETE", f"{self._MODELS_API_PREFIX}/{owner}/{name}"
        )

    def list(
        self,
        pagination_options: Optional[ModelPaginationOptions] = None,
        owner: Optional[str] = None,
    ) -> PaginatedResponse[Model]:
        """List models.

        Args:
            pagination_options (Optional[ModelPaginationOptions]): Optional settings
                to control pagination behavior.
            owner (Optional[str]): Username of the model's owner to fetch models for.
                If None, all models are fetched.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models and
                navigation metadata.
        """
        path = self._build_list_path(owner)

        response = self._requestor.request(
            method="GET", params=pagination_options, path=path
        )

        # The response will always match the ModelPaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_list(
        self,
        pagination_options: Optional[ModelPaginationOptions] = None,
        owner: Optional[str] = None,
    ) -> PaginatedResponse[Model]:
        """List models.

        Args:
            pagination_options (Optional[ModelPaginationOptions]): Optional settings
                to control pagination behavior.
            owner (Optional[str]): Username of the model's owner to fetch models for.
                If None, all models are fetched.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models and
                navigation metadata.
        """
        path = self._build_list_path(owner)

        response = await self._requestor.async_request(
            method="GET", params=pagination_options, path=path
        )
        # The response will always match the ModelPaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    def _build_list_path(self, owner: Optional[str] = None) -> str:
        """Construct the API path for listing models.

        Args:
            owner (Optional[str]): Username of the model's owner to fetch models for.
                If None, returns a path to fetch all models.

        Returns:
            str: The constructed API path for listing models.
        """
        return (
            f"{self._MODELS_API_PREFIX}/{owner}" if owner else self._MODELS_API_PREFIX
        )

    def get(self, owner: str, name: str) -> Model:
        """Get a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.

        Returns:
            Model: A model object.
        """
        response = self._requestor.request(
            "GET", f"{self._MODELS_API_PREFIX}/{owner}/{name}"
        )

        return cast(Model, response)

    async def async_get(self, owner: str, name: str) -> Model:
        """Get a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.

        Returns:
            Model: A model object.
        """
        response = await self._requestor.async_request(
            "GET", f"{self._MODELS_API_PREFIX}/{owner}/{name}"
        )

        return cast(Model, response)

    def create(self, params: CreateModelParams) -> Model:
        """Create a model.

        Args:
            params (CreateModelParams): Model creation parameters.

        Returns:
            Model: The new model.
        """
        response = self._requestor.request(
            method="POST",
            path=self._MODELS_API_PREFIX,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type:ignore[arg-type]
        )

        return cast(Model, response)

    async def async_create(self, params: CreateModelParams) -> Model:
        """Create a model.

        Args:
            params (CreateModelParams): Model creation parameters.

        Returns:
            Model: The new model.
        """
        response = await self._requestor.async_request(
            method="POST",
            path=self._MODELS_API_PREFIX,
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type:ignore[arg-type]
        )

        return cast(Model, response)

    def update(
        self,
        owner: str,
        name: str,
        params: UpdateModelParams,
    ) -> Model:
        """Update a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.
            params (UpdateModelParams): The fields to update.

        Returns:
            Model: The updated model.
        """
        response = self._requestor.request(
            method="PATCH",
            path=f"{self._MODELS_API_PREFIX}/{owner}/{name}",
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type: ignore[arg-type]
        )
        return cast(Model, response)

    async def async_update(
        self,
        owner: str,
        name: str,
        params: UpdateModelParams,
    ) -> Model:
        """Update a model.

        Args:
            owner (str): Username of the model's owner.
            name (str): Name of the model.
            params (UpdateModelParams): The fields to update.

        Returns:
            Model: The updated model.
        """
        response = await self._requestor.async_request(
            method="PATCH",
            path=f"{self._MODELS_API_PREFIX}/{owner}/{name}",
            # The params matches JsonValue at runtime,
            # but static type checkers may not infer this correctly.
            # Hence, we ignore the argument type warning.
            body=params,  # type: ignore[arg-type]
        )

        return cast(Model, response)

    def search(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Model]:
        """Search models.

        Args:
            q (str): The search query.
            pagination_options (Optional[PaginationOptions]): Optional settings to
                control pagination behavior.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models
                and navigation metadata.
        """
        params = self._build_search_params(q, pagination_options)

        response = self._requestor.request(
            method="GET",
            params=params,
            path=f"{self._SEARCH_API_PREFIX}{self._SEARCH_MODELS_SUFFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_search(
        self, q: str, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Model]:
        """Search models.

        Args:
            q (str): The search query.
            pagination_options (Optional[PaginationOptions]): Optional settings to
                control pagintation behavior.

        Returns:
            PaginatedResponse[Model]: Paginated response containing models
                and navigation metadata.
        """
        params = self._build_search_params(q, pagination_options)

        response = await self._requestor.async_request(
            method="GET",
            params=params,
            path=f"{self._SEARCH_API_PREFIX}{self._SEARCH_MODELS_SUFFIX}",
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]
