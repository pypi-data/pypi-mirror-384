# mypy: disable-error-code="list-item"
"""
Error log suppression utilities for the Yearn Treasury exporter.

This module suppresses noisy or irrelevant eth-portfolio error logs for specific
token addresses that are known to be deprecated or otherwise unpricable.

To suppress logs for additional tokens, add their addresses to the
`suppress_logs_for[Network.<chain>]` mapping. The rest will be done
automatically on package import.
"""

from typing import Dict, Final, List

from cchecksum import to_checksum_address
from eth_portfolio._utils import SUPPRESS_ERROR_LOGS
from eth_typing import HexAddress
from y import Network

from yearn_treasury.constants import CHAINID


suppress_logs_for: Final[Dict[Network, List[HexAddress]]] = {
    Network.Mainnet: [
        "0xBF7AA989192b020a8d3e1C65a558e123834325cA",  # unpriceable yvWBTC - This vault had a bug and does not have a pricePerShare
        "0x5aFE3855358E112B5647B952709E6165e1c1eEEe",  # SAFE - This was not tradeable at the time of the first airdrops
        "0x718AbE90777F5B778B52D553a5aBaa148DD0dc5D",  # yvCurve-alETH - The underlying curve pool had an issue and is unpriceable
    ],
}


def setup_eth_portfolio_logging() -> None:
    """
    Suppress eth-portfolio error logs for specific tokens on the current chain.

    Appends token addresses from the suppress_logs_for mapping (for the current
    CHAINID) to the SUPPRESS_ERROR_LOGS list, preventing error logs for these
    tokens from being emitted during analytics and reporting.
    """
    for token in suppress_logs_for.get(CHAINID, []):  # type: ignore [call-overload]
        SUPPRESS_ERROR_LOGS.append(to_checksum_address(token))
