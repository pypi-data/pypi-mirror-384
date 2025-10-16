"""
Ignore rules for WETH minting and burning.

This module defines matching logic for WETH minting and burning
transactions, so those transactions can be ignored in analytics
and reporting.
"""

from typing import Final

import y
from dao_treasury import TreasuryTx, TreasuryWallet, ignore
from eth_typing import ChecksumAddress

from yearn_treasury.rules.constants import EEE_ADDRESS, ZERO_ADDRESS


weth: Final[ChecksumAddress] = y.weth.address  # type: ignore [assignment]


@ignore("WETH:Minting")
def is_weth_mint(tx: TreasuryTx) -> bool:
    if (
        tx.from_address == ZERO_ADDRESS
        and TreasuryWallet.check_membership(tx.to_address.address, tx.block)  # type: ignore [union-attr, arg-type]
        and tx.token == weth
    ):
        return True
    return bool(
        TreasuryWallet.check_membership(tx.from_address.address, tx.block)  # type: ignore [union-attr, arg-type]
        and tx.to_address == weth
        and tx.token == EEE_ADDRESS
    )


@ignore("WETH:Burning")
def is_weth(tx: TreasuryTx) -> bool:
    if (
        TreasuryWallet.check_membership(tx.from_address.address, tx.block)  # type: ignore [union-attr, arg-type]
        and tx.to_address == ZERO_ADDRESS
        and tx.token == weth
    ):
        return True
    return bool(
        tx.from_address == weth
        and TreasuryWallet.check_membership(tx.to_address.address, tx.block)  # type: ignore [union-attr, arg-type]
        and tx.token == EEE_ADDRESS
    )
