"""
Swidge (cross-chain swap) type definitions for agent operations.

These schemas exactly match the execution-layer-sdk for zero friction.
"""

from typing import Annotated, Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Discriminator, Field

# =====================
# Network and Wallet Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeWallet(BaseModel):
    """Swidge wallet specification with network and address."""

    address: str = Field(..., description="Wallet address")
    network: str = Field(
        ..., description="Network identifier (e.g., 'solana' or 'ethereum:1')"
    )

    model_config = ConfigDict(extra="ignore")


# =====================
# Quote Request Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeQuoteRequest(BaseModel):
    """
    Request parameters for getting a cross-chain swap or bridge quote.

    Used to get pricing and routing information for swapping tokens between networks
    or within the same network. Perfect for bridging assets across chains or swapping
    tokens on the same chain.

    Attributes:
        from_: Source wallet specification
        to: Destination wallet specification
        fromToken: Source token contract address (optional, omit for native tokens like ETH/SOL)
        toToken: Destination token contract address (optional, omit for native tokens like ETH/SOL)
        amount: Amount in token's smallest unit (wei for ETH, lamports for SOL)
        slippage: Slippage tolerance % as string (e.g., "2.0" = 2%, default: "0.5")

    Examples:
        ```python
        # Bridge USDC: Polygon → Arbitrum
        quote_request = SwidgeQuoteRequest(
            from_=SwidgeWallet(network="ethereum:137", address=user_address),
            to=SwidgeWallet(network="ethereum:42161", address=user_address),
            amount="50000000",  # $50 USDC (6 decimals)
            fromToken="0x2791Bca1f2de4661ED88A30C99A7a9449Aa84174",  # USDC on Polygon
            toToken="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",   # USDC on Arbitrum
            slippage="2.0",  # 2% slippage for cross-chain
        )

        # Swap USDC → ETH on same chain (using defaults)
        quote_request = SwidgeQuoteRequest(
            from_=SwidgeWallet(network="ethereum:42161", address=user_address),
            to=SwidgeWallet(network="ethereum:42161", address=user_address),
            amount="100000000",  # $100 USDC (6 decimals)
            fromToken="0xaf88d065e77c8cC2239327C5EDb3A432268e5831",  # USDC
            # toToken omitted = native ETH (default behavior)
            # slippage defaults to "0.5"
        )
        ```
    """

    from_: SwidgeWallet = Field(
        ..., alias="from", description="Source wallet specification"
    )
    to: SwidgeWallet = Field(..., description="Destination wallet specification")
    fromToken: str | None = Field(
        None,
        description="Source token contract address (optional, omit for native tokens)",
    )
    toToken: str | None = Field(
        None,
        description="Destination token contract address (optional, omit for native tokens)",
    )
    amount: str = Field(
        ...,
        description="Amount in token's smallest unit (wei for ETH, lamports for SOL)",
    )
    priceImpact: str = Field(
        default="100.0",
        description="Max price impact % as string (hardcoded to '100.0' to not filter quotes)",
    )
    slippage: str | None = Field(
        None, description="Slippage tolerance % as string (default: '0.5')"
    )

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# =====================
# Quote Response Types (exact copy from execution-layer-sdk)
# =====================


class SwidgeQuoteAsset(BaseModel):
    """Asset information in quote response."""

    network: str = Field(..., description="Network identifier")
    address: str = Field(..., description="Wallet address")
    token: str | None = Field(
        None, description="Token contract address (null for native tokens)"
    )
    name: str | None = Field(None, description="Token name")
    symbol: str | None = Field(None, description="Token symbol")
    decimals: int | None = Field(None, description="Token decimals")
    amount: str | None = Field(None, description="Raw amount in smallest unit")
    minimumAmount: str | None = Field(None, description="Minimum amount after slippage")
    amountFormatted: str | None = Field(
        None, description="Human-readable formatted amount"
    )
    amountUsd: str | None = Field(None, description="USD value")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


class SwidgePriceImpact(BaseModel):
    """Price impact information."""

    usd: str | None = Field(None, description="Price impact in USD")
    percentage: str | None = Field(None, description="Price impact percentage")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


class SwidgeFee(BaseModel):
    """Fee information for the swap."""

    name: str = Field(..., description="Fee name (e.g., 'gas', 'bridge', 'protocol')")
    amount: str | None = Field(None, description="Raw fee amount")
    amountFormatted: str | None = Field(
        None, description="Human-readable formatted fee amount"
    )
    amountUsd: str | None = Field(None, description="Fee amount in USD")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


# Solana instruction for transaction details
class SwidgeSolanaInstruction(BaseModel):
    """Solana instruction for transaction details."""

    programId: str = Field(..., description="Program ID")
    keys: list[dict[str, Any]] = Field(..., description="Instruction keys")
    data: str | bytes = Field(..., description="Instruction data")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


# EVM transaction details
class SwidgeEvmTransactionDetails(BaseModel):
    """EVM transaction details."""

    type: Literal["evm"] = Field(..., description="Transaction type")
    from_: str = Field(
        ..., alias="from", description="Sender address", pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    to: str = Field(
        ..., description="Recipient address", pattern=r"^0x[a-fA-F0-9]{40}$"
    )
    chainId: int = Field(..., description="Chain ID")
    value: int = Field(..., description="Transaction value in wei")
    data: str = Field(..., description="Transaction data", pattern=r"^0x[a-fA-F0-9]*$")
    gas: int | None = Field(None, description="Gas limit (optional)")
    maxFeePerGas: int | None = Field(None, description="Max fee per gas (optional)")
    maxPriorityFeePerGas: int | None = Field(
        None, description="Max priority fee per gas (optional)"
    )

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# Solana transaction details
class SwidgeSolanaTransactionDetails(BaseModel):
    """Solana transaction details."""

    type: Literal["solana"] = Field(..., description="Transaction type")
    instructions: list[SwidgeSolanaInstruction] = Field(
        ..., description="Transaction instructions"
    )
    addressLookupTableAddresses: list[str] = Field(
        ..., description="Address lookup table addresses"
    )

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


# Transaction step schemas (adapted from execution-layer-sdk)
class SwidgeTransactionStep(BaseModel):
    """Transaction step in unsigned steps."""

    type: Literal["transaction"] = Field(..., description="Step type")
    description: str = Field(..., description="Human-readable description")
    transactionDetails: Annotated[
        SwidgeEvmTransactionDetails | SwidgeSolanaTransactionDetails,
        Discriminator("type"),
    ] = Field(..., description="Transaction details")
    metadata: dict[str, str] = Field(..., description="Additional metadata")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


class SwidgeSignatureStep(BaseModel):
    """Signature step in unsigned steps."""

    type: Literal["signature"] = Field(..., description="Step type")
    description: str = Field(..., description="Human-readable description")
    signatureData: str = Field(..., description="Signature data")
    metadata: dict[str, str] = Field(..., description="Additional metadata")

    # Use extra="allow" to preserve all fields from API
    model_config = ConfigDict(extra="allow")


SwidgeUnsignedStep = Annotated[
    SwidgeTransactionStep | SwidgeSignatureStep, Discriminator("type")
]


# Swidge data schema (includes quote and execution parameters like slippage)
class SwidgeData(BaseModel):
    """Complete Swidge data from quote endpoint (includes routing and slippage settings)."""

    engine: Literal["relay"] = Field(..., description="Swap engine")
    assetSend: SwidgeQuoteAsset = Field(..., description="Asset being sent")
    assetReceive: SwidgeQuoteAsset = Field(
        validation_alias=AliasChoices("assetReceive", "assetReceive"),
        description="Asset being received",
    )
    priceImpact: SwidgePriceImpact = Field(..., description="Price impact information")
    fees: list[SwidgeFee] = Field(..., description="List of fees")
    steps: list[SwidgeUnsignedStep] = Field(
        ..., description="Unsigned transaction steps"
    )

    # Use extra="allow" to preserve all fields from API - critical for passing quote data to execute
    model_config = ConfigDict(extra="allow", populate_by_name=True)


# =====================
# Execute Request Types
# =====================

# Execute request schema - takes the complete quote response from quote() method
SwidgeExecuteRequest = SwidgeData


# =====================
# Execute Response Types
# =====================


class SwidgeStatusInfo(BaseModel):
    """Status information for execute response."""

    network: str = Field(..., description="Network identifier")
    txs: list[str] = Field(..., description="Transaction hashes")

    model_config = ConfigDict(extra="ignore")


class SwidgeExecuteResponseData(BaseModel):
    """
    Execute response data - only final statuses returned by API.

    The API waits for completion and never returns "waiting" or "pending" statuses.
    """

    status: Literal["success", "failure", "refund", "delayed"] = Field(
        ..., description="Final execution status"
    )
    in_: SwidgeStatusInfo = Field(
        ..., alias="in", description="Input transaction status"
    )
    out: SwidgeStatusInfo = Field(
        ..., alias="out", description="Output transaction status"
    )
    lastUpdated: int = Field(..., description="Last update timestamp")

    model_config = ConfigDict(extra="ignore", populate_by_name=True)


# =====================
# Result Types
# =====================

QUOTE_RESULT = {
    "FOUND": "QUOTE_FOUND",  # Not an error - success case
    "NO_QUOTE_PROVIDED": "No quote provided",  # Generic API error
    "WALLET_NOT_FOUND": "Wallet not found",  # Exact API error string
    "WALLET_MISMATCH": "From wallet does not match session wallet",  # Exact API error string
}

SwidgeQuoteResult = Literal[
    "QUOTE_FOUND",
    "No quote provided",
    "Wallet not found",
    "From wallet does not match session wallet",
]


# =====================
# SDK Response Wrappers
# =====================


class SwidgeSDKResponse(BaseModel):
    """Standardized SDK response wrapper for swidge operations."""

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


class SwidgeQuoteResponse(SwidgeSDKResponse):
    """Swidge quote response wrapper."""

    data: SwidgeData | None = Field(None, description="Quote data")


class SwidgeExecuteResponse(SwidgeSDKResponse):
    """Swidge execute response wrapper."""

    data: SwidgeExecuteResponseData | None = Field(
        None, description="Execute response data"
    )
