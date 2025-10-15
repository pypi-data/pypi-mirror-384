"""
Swidge cross-chain swap operations.

This module provides the SwidgeApi class for cross-chain swaps and bridges
using the Swidge protocol.
"""

import json
from typing import TYPE_CHECKING, Any

from .client import APIError
from .types import (
    SwidgeData,
    SwidgeExecuteResponse,
    SwidgeExecuteResponseData,
    SwidgeQuoteRequest,
    SwidgeQuoteResponse,
)

if TYPE_CHECKING:
    from .agent_sdk import AgentSdk


def _ensure_string_error(error: Any) -> str:
    """
    Ensure error is always a string, converting dicts/objects to JSON if needed.

    Args:
        error: Error value that might be a string, dict, or other type

    Returns:
        String representation of the error
    """
    if error is None:
        return "Unknown error"
    elif isinstance(error, dict):
        return json.dumps(error)
    else:
        return str(error)


class SwidgeApi:
    """Cross-chain swap operations using Swidge.

    Workflow: quote() -> execute(quote.data) -> check result.data.status
    """

    def __init__(self, sdk: "AgentSdk"):
        self._sdk = sdk

    def quote(self, request: SwidgeQuoteRequest | dict) -> SwidgeQuoteResponse:
        """Get a cross-chain swap or bridge quote.

        Args:
            request: Quote parameters with wallet info, amount, and optional tokens/slippage.
                from: Source wallet {"network": "ethereum:1", "address": "0x..."}
                to: Destination wallet {"network": "ethereum:42161", "address": "0x..."}
                amount: Amount in smallest unit (e.g., "1000000000000000000" for 1 ETH)
                fromToken: Source token address (optional, omit for native tokens)
                toToken: Destination token address (optional, omit for native tokens)
                slippage: Slippage tolerance % as string (default: "0.5")
                priceImpact: Max price impact % as string (default: "0.5")

        Returns:
            SwidgeQuoteResponse with pricing, fees, and transaction steps.

        Example:
            quote = sdk.swidge.quote({
                "from": {"network": "ethereum:1", "address": user_address},
                "to": {"network": "ethereum:42161", "address": user_address},
                "amount": "1000000000000000000",  # 1 ETH
                "toToken": "0x2f2a2543B76A4166549F7aaB2e75BEF0aefC5b0f"  # WBTC
            })
        """
        return self._handle_swidge_quote(request)

    def execute(self, quote_data: SwidgeData) -> SwidgeExecuteResponse:
        """Execute a cross-chain swap or bridge using a quote.

        Args:
            quote_data: Complete quote object from sdk.swidge.quote().

        Returns:
            SwidgeExecuteResponse with transaction status and details.

        Example:
            quote = sdk.swidge.quote({...})
            if quote.success and quote.data:
                result = sdk.swidge.execute(quote.data)
        """
        return self._handle_swidge_execute(quote_data)

    def _handle_swidge_quote(
        self, request: SwidgeQuoteRequest | dict
    ) -> SwidgeQuoteResponse:
        """Handle swidge quote requests."""
        self._sdk._log("SWIDGE_QUOTE", {"request": request})

        try:
            # Handle both dict and Pydantic model inputs
            if isinstance(request, dict):
                request_obj = SwidgeQuoteRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/swidge/quote",
                request_obj.model_dump(mode="json", by_alias=True, exclude_unset=True),
            )

            # Parse into SwidgeData with extra="allow" to preserve all API fields
            # This is critical - we must not drop any fields the API returns
            return SwidgeQuoteResponse(
                success=True,
                error=None,
                data=SwidgeData(**response),
                error_details=None,
            )
        except APIError as api_error:
            # APIError has both error and message from API response
            self._sdk._log("=== SWIDGE QUOTE ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("=========================")

            return SwidgeQuoteResponse(
                success=False,
                data=None,
                error=_ensure_string_error(
                    api_error.error_message
                ),  # Always ensure it's a string
                error_details=api_error.error_details,  # Contains both 'error' and 'message' from API
            )
        except Exception as error:
            # Handle unexpected non-API errors
            error_message = _ensure_string_error(
                str(error) or "Failed to get swidge quote"
            )
            return SwidgeQuoteResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    def _handle_swidge_execute(self, quote_data: SwidgeData) -> SwidgeExecuteResponse:
        """Handle swidge execute requests."""
        self._sdk._log("SWIDGE_EXECUTE", {"quote": quote_data})

        try:
            # Custom serialization to handle schema inconsistencies:
            # - token field uses .nullable() and must be present even if null
            # - gas/maxFeePerGas/maxPriorityFeePerGas use .optional() and can't be null
            payload = quote_data.model_dump(
                mode="json", by_alias=True, exclude_none=False
            )

            # Strip None values from gas-related fields in transaction details
            if "steps" in payload:
                for step in payload["steps"]:
                    if (
                        step.get("type") == "transaction"
                        and "transactionDetails" in step
                    ):
                        tx_details = step["transactionDetails"]
                        if tx_details.get("type") == "evm":
                            # Remove None values for optional number fields
                            for field in [
                                "gas",
                                "maxFeePerGas",
                                "maxPriorityFeePerGas",
                            ]:
                                if field in tx_details and tx_details[field] is None:
                                    del tx_details[field]

            response = self._sdk.client.post(
                "/v1/swidge/execute",
                payload,
            )

            return SwidgeExecuteResponse(
                success=True,
                error=None,
                data=SwidgeExecuteResponseData(**response),
                error_details=None,
            )
        except APIError as api_error:
            # APIError has both error and message from API response
            self._sdk._log("=== SWIDGE EXECUTE ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("============================")

            return SwidgeExecuteResponse(
                success=False,
                data=None,
                error=_ensure_string_error(
                    api_error.error_message
                ),  # Always ensure it's a string
                error_details=api_error.error_details,  # Contains both 'error' and 'message' from API
            )
        except Exception as error:
            # Handle unexpected non-API errors
            error_message = _ensure_string_error(
                str(error) or "Failed to execute swidge swap"
            )
            return SwidgeExecuteResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )
