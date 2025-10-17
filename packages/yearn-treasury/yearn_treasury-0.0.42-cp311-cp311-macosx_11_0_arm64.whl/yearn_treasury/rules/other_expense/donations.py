"""
Other expense rules for donations in Yearn Treasury.

This module defines matching logic for donation transactions,
including Gitcoin matching rounds, 4626 Alliance, Vyper Compiler
Audit Contest, Warroom Games, and more.
"""

from typing import Final

from dao_treasury import TreasuryTx, other_expense
from y import Network


donations: Final = other_expense("Donations")

gitcoin: Final = "0xde21F729137C5Af1b01d73aF1dC21eFfa2B8a0d6"


@donations("Gitcoin Matching Round", Network.Mainnet)
def is_gitcoin_matching_donation(tx: TreasuryTx) -> bool:
    return tx.symbol in ["DAI", "USDC"] and tx.to_address == gitcoin


donations("4626 Alliance", Network.Mainnet).match(
    hash="0xca61496c32806ba34f0deb331c32969eda11c947fdd6235173e6fa13d9a1c288",
    log_index=150,
)


donations("Vyper Compiler Audit Contest", Network.Mainnet).match(
    # Grant for a vyper compiler audit context, vyper-context.eth
    hash="0xb8bb3728fdfb49d7c86c08dba8e3586e3761f13d2c88fa6fab80227b6a3f4519",
    log_index=202,
)


@donations("Warroom Games 2023 Prizes", Network.Mainnet)
def is_warroom_games(tx: TreasuryTx) -> bool:
    return (
        tx.hash == "0x8f17ead9cea87166cf99ed2cdbc46dfdf98c04c261de5b5167caddce5f704cb2"
        and tx.log_index in [429, 430, 431]
    )
