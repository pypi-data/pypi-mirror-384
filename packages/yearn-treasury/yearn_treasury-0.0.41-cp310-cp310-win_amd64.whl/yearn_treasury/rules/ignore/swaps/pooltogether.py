"""
Ignore rules for PoolTogether protocol transactions.

This module defines matching logic for PoolTogether deposits swaps,
as they can be safely ignored in analytics and reporting.
"""

from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.constants import ZERO_ADDRESS
from yearn_treasury.rules.ignore.swaps import swaps


@swaps("PoolTogether:Deposit", Network.Mainnet)
def is_pooltogether_deposit(tx: TreasuryTx) -> bool:
    # TODO: figure out what was done with the withdrawals and put a note here
    symbol = tx.symbol
    return (
        symbol == "POOL" and tx.to_address.address == "0x396b4489da692788e327E2e4b2B0459A5Ef26791"
    ) or (  # type: ignore [union-attr]
        symbol == "PPOOL" and tx.from_address.address == ZERO_ADDRESS
    )  # type: ignore [union-attr]
