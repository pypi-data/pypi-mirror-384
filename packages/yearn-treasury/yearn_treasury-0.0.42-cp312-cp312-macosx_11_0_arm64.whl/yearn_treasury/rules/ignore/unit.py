"""
Ignore rules for Unit.xyz protocol.

This module defines matching logic for Unit.xyz protocol transactions,
so they can be ignored in analytics and reporting.
"""

from typing import Final

from dao_treasury import TreasuryTx, ignore
from y import Network

from yearn_treasury.constants import ZERO_ADDRESS


UNIT_XYZ_VAULT: Final = "0xb1cFF81b9305166ff1EFc49A129ad2AfCd7BCf19"

unit: Final = ignore("Unit.xyz")
collateral: Final = unit("Collateral")
usdp: Final = unit("USDP")


@collateral("YFI Deposit", Network.Mainnet)
def is_unit_yfi_deposit(tx: TreasuryTx) -> bool:
    return tx.symbol == "YFI" and tx.to_address.address == UNIT_XYZ_VAULT  # type: ignore [union-attr]


@collateral("YFI Withdrawal", Network.Mainnet)
def is_unit_yfi_withdrawal(tx: TreasuryTx) -> bool:
    return tx.symbol == "YFI" and tx.from_address.address == UNIT_XYZ_VAULT  # type: ignore [union-attr]


@usdp("Minting", Network.Mainnet)
def is_minting_usdp(tx: TreasuryTx) -> bool:
    return tx.symbol == "USDP" and tx.from_address.address == ZERO_ADDRESS  # type: ignore [union-attr]


@usdp("Burning", Network.Mainnet)
def is_burning_usdp(tx: TreasuryTx) -> bool:
    return tx.symbol == "USDP" and tx.to_address.address == ZERO_ADDRESS  # type: ignore [union-attr]
