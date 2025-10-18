"""
Polymarket prediction market operations.

This module provides the PolymarketApi class for interacting with Polymarket
prediction markets, including position management, market orders, and redemptions.
"""

import json
from typing import TYPE_CHECKING, Any

from .client import APIError
from .types import (
    PolymarketMarketOrderData,
    PolymarketMarketOrderRequest,
    PolymarketMarketOrderResponse,
    PolymarketRedeemPositionsRequest,
    PolymarketRedeemPositionsResponse,
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


class PolymarketApi:
    """
    Polymarket prediction market operations.

    Provides access to market orders and position redemptions
    on the Polymarket platform using your session wallet.

    Note: Position data is available via agent.currentPositions in the request.
    """

    def __init__(self, sdk: "AgentSdk"):
        self._sdk = sdk

    def market_order(
        self, request: PolymarketMarketOrderRequest | dict
    ) -> PolymarketMarketOrderResponse:
        """
               Execute a market order on Polymarket.

               Places a buy or sell market order for the specified token and size. Handles approvals,
               signing, and submission automatically.

               **Important**: The `size` parameter meaning differs by order side:
               - **BUY**: `size` is the USD amount to spend (e.g., 10 = $10 worth of shares)
               - **SELL**: `size` is the number of shares/tokens to sell (e.g., 10 = 10 shares)

               **Input**: `PolymarketMarketOrderRequest`
                   - `tokenId` (str): Market token ID for the position
                   - `size` (float): For BUY: USD amount to spend. For SELL: Number of shares to sell
                   - `side` (Literal["BUY", "SELL"]): Order side

               **Output**: `PolymarketMarketOrderResponse`
                   - `success` (bool): Whether the operation was successful
                   - `data` (PolymarketMarketOrderData | None): Market order data (only present on success)
                       - `success` (bool): Whether the order was successfully submitted
                       - `orderInfo` (PolymarketOrderInfo): Order information with transaction details
                           - `orderId` (str): Unique order identifier
                           - `side` (str): Order side ("BUY" or "SELL")
                           - `size` (str): Order size
                           - `priceUsd` (str): Price per share in USD
                           - `totalPriceUsd` (str): Total order value in USD
                           - `txHashes` (list[str]): List of transaction hashes
                   - `error` (str | None): Error message (only present on failure)

               **Key Functionality**:
                   - Automatic approval handling for token spending
                   - EIP-712 signature generation for order placement
                   - Real-time order submission and confirmation
                   - Support for both buy and sell orders

               **Example**:
                   ```python
                   # BUY order - size is USD amount
                   buy_result = sdk.platforms.polymarket.market_order({
                       "tokenId": "123456",
                       "size": 10,  # Spend $10 to buy shares
                       "side": "BUY"
                   })

                   # SELL order - size is number of shares
                   sell_result = sdk.platforms.polymarket.market_order({
                       "tokenId": "123456",
                       "size": 5,  # Sell 5 shares
                       "side": "SELL"
                   })

                   if buy_result.success and buy_result.data:
                       print(f"Order Success: {buy_result.data.success}")
                       print(f"Order ID: {buy_result.data.orderInfo.orderId}")
                       print(f"Total Price: ${buy_result.data.orderInfo.totalPriceUsd}")
                   else:
                       print(f"Error: {buy_result.error}")
                   ```

               **Success Case**:
                   ```python
                   {
                       "success": True,
                       "data": {
                           "success": True,
                           "orderInfo": {
                               "orderId": "abc123",
                               "side": "BUY",
                               "size": "10.0",
                               "priceUsd": "0.52",
                               "totalPriceUsd": "5.20",
                               "txHashes": ["0xabc..."]
                           }
                       },
                       "error": None,
        None
                   }
                   ```

               **Error Case**:
                   ```python
                   {
                       "success": False,
                       "data": None,
                       "error": "Could not get order",
        {"message": "Invalid request", "status": 400}
                   }
                   ```

               Args:
                   request: Order parameters (tokenId, size, side)

               Returns:
                   PolymarketMarketOrderResponse: Wrapped response with order details and submission result
        """
        return self._handle_polymarket_market_order(request)

    def redeem_positions(
        self, request: PolymarketRedeemPositionsRequest | dict | None = None
    ) -> PolymarketRedeemPositionsResponse:
        """
               Redeem settled positions on Polymarket.

               Redeems one or all redeemable positions, claiming winnings. Handles multiple transactions if needed.

               **Input**: `PolymarketRedeemPositionsRequest` (optional, defaults to redeem all)
                   - `tokenIds` (list[str], optional): List of token IDs to redeem specific positions. Empty or omitted redeems all redeemable positions.

               **Output**: `PolymarketRedeemPositionsResponse`
                   - `success` (bool): Whether the operation was successful
                   - `data` (list[PolymarketRedeemPositionResult] | None): Redeem positions data (only present on success)
                       Each result contains:
                           - `success` (bool): Whether redemption was successful
                           - `position` (PolymarketPosition): Position that was redeemed (full position details)
                           - `transactionHash` (str | None): Transaction hash (null if redemption failed)
                   - `error` (str | None): Error message (only present on failure)

               **Key Functionality**:
                   - Automatic detection of redeemable positions
                   - Batch redemption support for multiple positions
                   - Single position redemption by token ID
                   - Transaction tracking for each redemption

               **Example**:
                   ```python
                   # Redeem all positions (no arguments - default behavior)
                   all_result = sdk.platforms.polymarket.redeem_positions()

                   # Redeem specific positions
                   specific_result = sdk.platforms.polymarket.redeem_positions({"tokenIds": ["123456", "789012"]})

                   if all_result.success and all_result.data:
                       for tx in all_result.data:
                           if tx.success and tx.position:
                               print(f"Redeemed {tx.position.question}: Tx {tx.transactionHash}")
                           elif tx.success:
                               print(f"Unwrapped collateral: Tx {tx.transactionHash}")
                           elif tx.position:
                               print(f"Failed to redeem {tx.position.question}")
                   else:
                       print(f"Error: {all_result.error}")
                   ```

               **Success Case (Multiple Redemptions)**:
                   ```python
                   {
                       "success": True,
                       "data": [
                           {
                               "success": True,
                               "position": {
                                   "contractAddress": "0x...",
                                   "tokenId": "123456",
                                   "question": "Will event X happen?",
                                   "outcome": "Yes",
                                   # ... full position details
                               },
                               "transactionHash": "0xabc123..."
                           },
                           {
                               "success": True,
                               "position": {
                                   "contractAddress": "0x...",
                                   "tokenId": "789012",
                                   "question": "Will event Y happen?",
                                   "outcome": "No",
                                   # ... full position details
                               },
                               "transactionHash": "0xdef456..."
                           },
                           {
                               "success": True,
                               "position": None,  # None for unwrap collateral transactions
                               "transactionHash": "0xghi789..."
                           }
                       ],
                       "error": None,
        None
                   }
                   ```

               **Error Case**:
                   ```python
                   {
                       "success": False,
                       "data": None,
                       "error": "Could not get positions",
        {"message": "No redeemable positions", "status": 404}
                   }
                   ```

               Args:
                   request: Redemption parameters (tokenIds list for specific positions, empty for all)

               Returns:
                   PolymarketRedeemPositionsResponse: Wrapped response with per-position redemption results
        """
        return self._handle_polymarket_redeem_positions(request)

    def _handle_polymarket_market_order(
        self, request: PolymarketMarketOrderRequest | dict
    ) -> PolymarketMarketOrderResponse:
        """Handle polymarket market order requests."""
        self._sdk._log("POLYMARKET_MARKET_ORDER", {"request": request})

        try:
            # Handle both dict and Pydantic model inputs
            if isinstance(request, dict):
                request_obj = PolymarketMarketOrderRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/platforms/polymarket/market-order",
                request_obj.model_dump(mode="json", exclude_unset=True),
            )

            return PolymarketMarketOrderResponse(
                success=True,
                data=PolymarketMarketOrderData(**response),
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== POLYMARKET MARKET ORDER ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("====================================")

            return PolymarketMarketOrderResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to execute polymarket market order"
            return PolymarketMarketOrderResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )

    def _handle_polymarket_redeem_positions(
        self, request: PolymarketRedeemPositionsRequest | dict | None
    ) -> PolymarketRedeemPositionsResponse:
        """Handle polymarket redeem positions requests."""
        self._sdk._log("POLYMARKET_REDEEM_POSITIONS", {"request": request})

        try:
            # Handle None, dict, and Pydantic model inputs
            if request is None:
                request_obj = PolymarketRedeemPositionsRequest()
            elif isinstance(request, dict):
                request_obj = PolymarketRedeemPositionsRequest(**request)
            else:
                request_obj = request

            response = self._sdk.client.post(
                "/v1/platforms/polymarket/redeem-positions",
                request_obj.model_dump(mode="json", exclude_unset=True),
            )

            # Parse response data into list of PolymarketRedeemPositionResult
            # Note: API returns a list, not a dict, for this endpoint
            from typing import cast

            from .types.polymarket import PolymarketRedeemPositionResult

            parsed_data: list[PolymarketRedeemPositionResult] | None = None
            if response:
                # Cast because client.post is typed as returning dict, but this endpoint returns list
                response_list = cast(list[dict[str, Any]], response)
                parsed_data = [
                    PolymarketRedeemPositionResult(**item) for item in response_list
                ]

            return PolymarketRedeemPositionsResponse(
                success=True,
                data=parsed_data,
                error=None,
                error_details=None,
            )
        except APIError as api_error:
            self._sdk._log("=== POLYMARKET REDEEM POSITIONS ERROR ===")
            self._sdk._log("Error:", api_error.error_message)
            self._sdk._log("========================================")

            return PolymarketRedeemPositionsResponse(
                success=False,
                data=None,
                error=_ensure_string_error(api_error.error_message),
                error_details=api_error.error_details,
            )
        except Exception as error:
            error_message = str(error) or "Failed to redeem polymarket positions"
            return PolymarketRedeemPositionsResponse(
                success=False,
                data=None,
                error=error_message,
                error_details={"type": type(error).__name__},
            )
