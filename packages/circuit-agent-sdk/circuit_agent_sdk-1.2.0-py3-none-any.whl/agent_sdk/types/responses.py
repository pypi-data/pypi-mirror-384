"""
Response type definitions for the Agent SDK.

This module provides all response models returned by SDK operations.
All models use strict Pydantic validation for type safety.
"""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from .swidge import SwidgeData, SwidgeExecuteResponseData


class SignAndSendData(BaseModel):
    """
    Success data from sign_and_send operations.

    This data is returned in the `data` field when a transaction is successfully
    signed and broadcast.

    Attributes:
        internal_transaction_id: Internal transaction ID for tracking
        tx_hash: Transaction hash once broadcast to the network
        transaction_url: Optional transaction URL (explorer link)
    """

    internal_transaction_id: int = Field(
        ..., description="Internal transaction ID for tracking"
    )
    tx_hash: str = Field(..., description="Transaction hash once broadcast")
    transaction_url: str | None = Field(
        None, description="Optional transaction URL (explorer link)"
    )

    model_config = ConfigDict(extra="ignore")


class SignAndSendResponse(BaseModel):
    """
    Standard response from sign_and_send operations.

    This response follows the unified SDK response structure with success, data,
    error, and error_details fields.

    Attributes:
        success: Whether the operation was successful
        data: Transaction data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = sdk.sign_and_send({
            "network": "ethereum:1",
            "request": {"toAddress": "0x...", "data": "0x", "value": "0"}
        })
        if response.success and response.data:
            print(f"Transaction hash: {response.data.tx_hash}")
            if response.data.transaction_url:
                print(f"View on explorer: {response.data.transaction_url}")
        else:
            print(f"Transaction failed: {response.error}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SignAndSendData | None = Field(
        None, description="Transaction data (only present on success)"
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


class EvmMessageSignData(BaseModel):
    """EVM message signature data."""

    status: int
    v: int
    r: str
    s: str
    formattedSignature: str
    type: Literal["evm"]


class EvmMessageSignResponse(BaseModel):
    """
    Response from EVM message signing operations.

    Attributes:
        success: Whether the operation was successful
        data: Signature data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: EvmMessageSignData | None = Field(
        None, description="Signature data (only present on success)"
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


class SwidgeQuoteResponse(BaseModel):
    """
    Swidge quote response wrapper.

    Attributes:
        success: Whether the operation was successful
        data: Swidge data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SwidgeData | None = Field(
        None, description="Swidge data (only present on success)"
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


class SwidgeExecuteResponse(BaseModel):
    """
    Swidge execute response wrapper.

    Attributes:
        success: Whether the operation was successful
        data: Execute response data (only present on success)
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)
    """

    success: bool = Field(..., description="Whether the operation was successful")
    data: SwidgeExecuteResponseData | None = Field(
        None, description="Execute response data (only present on success)"
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


class UpdateJobStatusResponse(BaseModel):
    """Response from job status update."""

    status: int = Field(..., description="HTTP status code")
    message: str = Field(..., description="Response message")

    model_config = ConfigDict(extra="ignore")


class LogResponse(BaseModel):
    """
    Response from agent.log() operations.

    This response is returned after attempting to log a message to the console
    and optionally to the backend.

    Attributes:
        success: Whether the operation was successful
        error: Error message (only present on failure)
        error_details: Detailed error information (only present on failure)

    Example:
        ```python
        response = agent.log("Processing transaction")
        if not response.success:
            print(f"Failed to log: {response.error_message}")
        ```
    """

    success: bool = Field(..., description="Whether the operation was successful")
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
