"""
Platform integrations namespace.

This module provides the PlatformsApi class which groups platform-specific
integrations like Polymarket under a single namespace.
"""

from typing import TYPE_CHECKING

from .polymarket import PolymarketApi

if TYPE_CHECKING:
    from .agent_sdk import AgentSdk


class PlatformsApi:
    """
    Access to platform-specific integrations.

    Currently supported platforms:
    - polymarket: Prediction market trading operations

    All operations are policy-checked and signed automatically.
    """

    # Type annotation for the polymarket property
    polymarket: "PolymarketApi"

    def __init__(self, sdk: "AgentSdk"):
        """
        Initialize the PlatformsApi.

        Args:
            sdk: The parent AgentSdk instance
        """
        self._sdk = sdk
        # Initialize polymarket property
        self.polymarket = PolymarketApi(sdk)
