"""
Ignore rules for the Unwrapper contract.

This module defines matching logic for swaps involving the Unwrapper
contract, so those transactions can be ignored from analytics and
reporting.
"""

from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.rules.ignore.swaps import swaps


@swaps("Unwrapper", Network.Mainnet)
def is_unwrapper(tx: TreasuryTx) -> bool:
    return "Contract: Unwrapper" in [tx.from_nickname, tx.to_nickname]
