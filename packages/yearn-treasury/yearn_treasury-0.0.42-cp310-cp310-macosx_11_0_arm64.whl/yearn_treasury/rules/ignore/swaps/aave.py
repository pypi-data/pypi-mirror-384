"""
Ignore rules for Aave-related transactions.

This module defines rules for identifying and ignoring Aave-related
transactions in the Yearn Treasury system. It provides matching logic
for deposit and withdrawal events, so these transactions can be
ignored in analytics and reporting.
"""

from typing import Final

from dao_treasury import TreasuryTx, TreasuryWallet
from eth_typing import ChecksumAddress

from yearn_treasury.rules.constants import ZERO_ADDRESS
from yearn_treasury.rules.ignore.swaps import swaps


aave: Final = swaps("Aave")


@aave("Deposit")
def is_aave_deposit(tx: TreasuryTx) -> bool:
    # Atoken side

    # Underlying side
    # TODO we didnt need this historically??
    return False


@aave("Withdrawal")
async def is_aave_withdrawal(tx: TreasuryTx) -> bool:
    from_address: ChecksumAddress = tx.from_address.address  # type: ignore [union-attr, assignment]
    to_address: ChecksumAddress = tx.to_address.address  # type: ignore [union-attr, assignment]
    # Atoken side
    if (
        TreasuryWallet.check_membership(from_address, tx.block)  # type: ignore [union-attr, arg-type]
        and to_address == ZERO_ADDRESS
    ):
        token = tx.token
        if hasattr(token.contract, "underlyingAssetAddress"):
            for event in await tx.get_events("RedeemUnderlying", sync=False):
                if (
                    from_address == event["_user"]
                    and await token.contract.underlyingAssetAddress == event["_reserve"]
                ):
                    # TODO get rid of this rounding when we migrate the db to postgres
                    event_amount = round(token.scale_value(event["_amount"]), 11)
                    if event_amount == round(tx.amount, 11):
                        return True
                    print(
                        f"Aave Withdrawal atoken side does not match: {round(tx.amount, 14)}  {event_amount}"
                    )

    # Underlying side
    if TreasuryWallet.check_membership(tx.to_address.address, tx.block):  # type: ignore [union-attr, arg-type]
        token = tx.token
        for event in await tx.get_events("RedeemUnderlying", sync=False):
            if token == event["_reserve"] and to_address == event["_user"]:
                # TODO get rid of this rounding when we migrate the db to postgres
                event_amount = round(token.scale_value(event["_amount"]), 11)
                if event_amount == round(tx.amount, 11):
                    return True
                print(
                    f"Aave Withdrawal underlying side does not match: {round(tx.amount, 14)}  {event_amount}"
                )

    # TODO: If these end up becoming more frequent, figure out sorting hueristics.
    return tx.hash == "0x36ee5631859a15f57b44e41b8590023cf6f0c7b12d28ea760e9d8f8003f4fc50"
