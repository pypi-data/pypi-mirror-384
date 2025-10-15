"""Common Pydantic schemas for directory_api.

Shared schemas used across multiple endpoints:
- Enums matching Django model choices
- Pagination response wrapper
- Base response schemas
"""

from enum import Enum
from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

# Type variable for generic pagination
T = TypeVar("T")


class BackfillStatusEnum(str, Enum):
    """Backfill status values matching Django model choices.

    Used to track async content generation and data processing status.
    """

    PENDING = "pending"  # Waiting to be processed
    DONE = "done"  # Successfully completed
    ERROR = "error"  # Processing failed
    NO_BACKFILL = "no_backfill"  # Does not require backfill


class PublishStatusEnum(str, Enum):
    """Publish status values for entities.

    Controls visibility and public access to entity pages.
    """

    DRAFT = "draft"  # Not yet published
    PUBLISHED = "published"  # Live and publicly visible
    INACTIVE = "inactive"  # Previously published, now hidden


class ExperienceLevelEnum(str, Enum):
    """Experience level values for category participants.

    Indicates user's expertise level in a category.
    """

    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"


class PaginatedResponse(BaseModel, Generic[T]):  # noqa: UP046
    """Generic paginated response wrapper for list endpoints.

    Usage:
        Use this to wrap lists of items with pagination metadata.
        The 'items' field will contain the actual data.

    Example response:
        {
            "items": [...],
            "total": 150,
            "page": 1,
            "page_size": 50,
            "pages": 3
        }
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    items: list[T] = Field(description="List of items for the current page", examples=[["Item 1", "Item 2", "Item 3"]])
    total: int = Field(description="Total number of items across all pages", examples=[150], ge=0)
    page: int = Field(description="Current page number (1-indexed)", examples=[1], ge=1)
    page_size: int = Field(description="Number of items per page", examples=[50], ge=1, le=100)
    pages: int = Field(description="Total number of pages", examples=[3], ge=0)


class ErrorResponse(BaseModel):
    """Standard error response format for API errors.

    Provides consistent error structure for clients and LLM agents.
    """

    detail: str = Field(description="Human-readable error message", examples=["Category with slug 'invalid' not found"])
    error_code: str | None = Field(
        default=None, description="Machine-readable error code", examples=["NOT_FOUND", "VALIDATION_ERROR"]
    )


class MessageResponse(BaseModel):
    """Standard success message response."""

    message: str = Field(description="Success message", examples=["Category created successfully"])
