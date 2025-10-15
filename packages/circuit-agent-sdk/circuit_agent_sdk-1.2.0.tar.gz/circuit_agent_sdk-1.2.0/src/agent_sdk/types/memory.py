"""
Memory type definitions for agent session storage.

Memory operations provide key-value storage scoped to the current agent session.
All keys are automatically namespaced by agentId and sessionId.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

# =====================
# Request Types
# =====================


class MemorySetRequest(BaseModel):
    """
    Request to set a key-value pair in memory.

    Attributes:
        key: Unique identifier for the value (1-255 characters)
        value: String value to store

    Examples:
        ```python
        # Store user preferences
        request = MemorySetRequest(
            key="lastSwapNetwork",
            value="ethereum:42161"
        )
        ```
    """

    key: str = Field(..., min_length=1, description="Key identifier")
    value: str = Field(..., description="Value to store")

    model_config = ConfigDict(extra="ignore")


class MemoryGetRequest(BaseModel):
    """
    Request to get a value by key from memory.

    Attributes:
        key: The key to retrieve

    Examples:
        ```python
        request = MemoryGetRequest(key="lastSwapNetwork")
        ```
    """

    key: str = Field(..., min_length=1, description="Key to retrieve")

    model_config = ConfigDict(extra="ignore")


class MemoryDeleteRequest(BaseModel):
    """
    Request to delete a key from memory.

    Attributes:
        key: The key to delete

    Examples:
        ```python
        request = MemoryDeleteRequest(key="tempSwapQuote")
        ```
    """

    key: str = Field(..., min_length=1, description="Key to delete")

    model_config = ConfigDict(extra="ignore")


class MemoryListRequest(BaseModel):
    """
    Request to list all keys in memory (no parameters needed).

    Examples:
        ```python
        request = MemoryListRequest()
        ```
    """

    model_config = ConfigDict(extra="ignore")


# =====================
# Response Data Types
# =====================


class MemorySetData(BaseModel):
    """
    Data returned when setting a key.

    Attributes:
        key: The key that was set
    """

    key: str = Field(..., description="The key that was set")

    model_config = ConfigDict(extra="ignore")


class MemoryGetData(BaseModel):
    """
    Data returned when getting a key.

    Attributes:
        key: The requested key
        value: The stored value
    """

    key: str = Field(..., description="The requested key")
    value: str = Field(..., description="The stored value")

    model_config = ConfigDict(extra="ignore")


class MemoryDeleteData(BaseModel):
    """
    Data returned when deleting a key.

    Attributes:
        key: The key that was deleted
    """

    key: str = Field(..., description="The key that was deleted")

    model_config = ConfigDict(extra="ignore")


class MemoryListData(BaseModel):
    """
    Data returned when listing keys.

    Attributes:
        keys: Array of all stored keys
        count: Number of keys
    """

    keys: list[str] = Field(..., description="Array of all stored keys")
    count: int = Field(..., description="Number of keys")

    model_config = ConfigDict(extra="ignore")


# =====================
# SDK Response Wrappers
# =====================


class MemorySDKResponse(BaseModel):
    """Standardized SDK response wrapper for memory operations."""

    success: bool = Field(..., description="Whether the operation was successful")
    data: Any | None = Field(
        None, description="Response data (only present on success)"
    )
    error: str | None = Field(
        None, description="Error message (only present on failure)"
    )
    error_details: dict | None = Field(
        None, description="Detailed error information (only present on failure)"
    )

    @property
    def error_message(self) -> str | None:
        """Alias for error field to provide consistent API."""
        return self.error

    model_config = ConfigDict(extra="ignore")


class MemorySetResponse(MemorySDKResponse):
    """Memory set response wrapper."""

    data: MemorySetData | None = Field(None, description="Set operation data")


class MemoryGetResponse(MemorySDKResponse):
    """Memory get response wrapper."""

    data: MemoryGetData | None = Field(None, description="Get operation data")


class MemoryDeleteResponse(MemorySDKResponse):
    """Memory delete response wrapper."""

    data: MemoryDeleteData | None = Field(None, description="Delete operation data")


class MemoryListResponse(MemorySDKResponse):
    """Memory list response wrapper."""

    data: MemoryListData | None = Field(None, description="List operation data")
