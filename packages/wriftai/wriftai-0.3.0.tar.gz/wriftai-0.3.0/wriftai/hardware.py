"""Hardware module."""

from typing import Optional, TypedDict

from wriftai._resource import Resource
from wriftai.pagination import PaginatedResponse, PaginationOptions


class Hardware(TypedDict):
    """Represents a hardware item.

    Attributes:
        id (str): Unique identifier for the hardware.
        name (str): Name of the hardware.
        gpus (int): Number of GPUs available on the hardware.
        cpus (int): Number of CPUs available on the hardware.
        ram_per_gpu_gb (int): Amount of Ram (in GB) allocated per GPU.
        ram_gb (int): Total RAM (in GB) available on the hardware.
        created_at (str): Timestamp when the hardware was created.
    """

    id: str
    name: str
    gpus: int
    cpus: int
    ram_per_gpu_gb: int
    ram_gb: int
    created_at: str


class HardwareResource(Resource):
    """Resource for operations related to hardware."""

    _API_PREFIX = "/hardware"

    def list(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Hardware]:
        """List hardware.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Hardware]: Paginated response containing
                hardware items and navigation metadata.
        """
        response = self._requestor.request(
            method="GET", params=pagination_options, path=self._API_PREFIX
        )

        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]

    async def async_list(
        self, pagination_options: Optional[PaginationOptions] = None
    ) -> PaginatedResponse[Hardware]:
        """List hardware.

        Args:
            pagination_options (Optional[PaginationOptions]): Optional settings
                to control pagination behavior.

        Returns:
            PaginatedResponse[Hardware]: Paginated response containing
                hardware items and navigation metadata.
        """
        response = await self._requestor.async_request(
            method="GET", params=pagination_options, path=self._API_PREFIX
        )
        # The response will always match the PaginatedResponse structure,
        # but static type checkers may not infer this correctly.
        # Hence, we ignore the argument type warning.
        return PaginatedResponse(**response)  # type:ignore[arg-type]
