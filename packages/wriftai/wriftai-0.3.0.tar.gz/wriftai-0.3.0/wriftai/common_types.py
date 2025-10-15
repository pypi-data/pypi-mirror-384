"""Common types used across the WriftAI package."""

import sys
from collections.abc import Mapping
from typing import Any, TypeAlias, TypedDict, Union

__all__ = ["NotRequired", "StrEnum", "Unpack"]


JsonValue: TypeAlias = Union[
    list["JsonValue"],
    Mapping[str, "JsonValue"],
    str,
    bool,
    int,
    float,
    None,
]

if sys.version_info >= (3, 11):
    from enum import StrEnum
    from typing import NotRequired, Unpack
else:
    from enum import Enum

    from typing_extensions import NotRequired, Unpack

    class StrEnum(str, Enum):
        """String-based enum class for compatibility with older Python versions."""

        pass


class User(TypedDict):
    """Represents a user.

    Attributes:
            id (str): Unique identifier of the user.
            username (str): The username of the user.
            avatar_url (str): URL of the user's avatar.
            name (str | None): The name of the user.
            bio (str | None): The biography of the user.
            urls (list[str] | None): Personal or professional website URLs.
            location (str | None): Location of the user.
            company (str | None): Company the user is associated with.
            created_at (str): Timestamp when the user joined WriftAI.
            updated_at (str | None): Timestamp when the user was last updated.
    """

    id: str
    username: str
    avatar_url: str
    name: str | None
    bio: str | None
    urls: list[str] | None
    location: str | None
    company: str | None
    created_at: str
    updated_at: str | None


class SchemaIO(TypedDict):
    """Represents input and output schemas.

    Attributes:
        input (dict[str, Any]): Schema for input, following JSON Schema
            Draft 2020-12 standards.
        output (dict[str, Any]): Schema for output, following JSON Schema
            Draft 2020-12 standards.
    """

    input: dict[str, Any]
    output: dict[str, Any]


class Schemas(TypedDict):
    """Represents schemas of a version.

    Attributes:
        prediction (SchemaIO):The input and output schemas for a prediction.
    """

    prediction: SchemaIO


class Version(TypedDict):
    """Represents a version.

    Attributes:
        id (str):The unique identifier of the version.
        release_notes (str): Information about changes such as
            new features,bug fixes, or optimizations in this version.
        created_at (str): The time when the version was created.
        schemas (Schemas): The schemas of the model version.
        container_image_digest (str): A sha256 hash digest of
            the version's container image.
    """

    id: str
    release_notes: str
    created_at: str
    schemas: Schemas
    container_image_digest: str
