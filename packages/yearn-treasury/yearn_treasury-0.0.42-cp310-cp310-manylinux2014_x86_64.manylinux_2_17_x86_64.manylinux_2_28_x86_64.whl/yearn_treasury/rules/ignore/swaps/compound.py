from typing import Final

from dao_treasury import TreasuryTx

from yearn_treasury.rules.ignore.swaps import swaps


compound: Final = swaps("Compound")


@compound("Deposit")
async def is_compound_deposit(tx: TreasuryTx) -> bool:
    for event in await tx.get_events("Mint", sync=False):
        if all(arg in event for arg in ("minter", "mintTokens", "mintAmount")):
            minter = event["minter"]
            minted = tx.token.scale_value(event["mintTokens"])
            # cToken side
            if tx.token == tx.from_address == event.address and tx.to_address == minter:
                # TODO: get rid of this rounding when we migrate to postgres
                if round(minted, 14) == round(tx.amount, 14):
                    return True
                print(
                    f"Compound deposit ctoken side does not match: {round(minted, 14)}  {round(tx.amount, 14)}"
                )
            # underlying side
            elif tx.to_address == event.address and tx.from_address == minter:
                # TODO: get rid of this rounding when we migrate to postgres
                if round(minted, 14) == round(tx.amount, 14):
                    return True
                print(
                    f"Compound deposit underlying side does not match: {round(minted, 14)}  {round(tx.amount, 14)}"
                )
    return False


@compound("Withdrawal")
async def is_compound_withdrawal(tx: TreasuryTx) -> bool:
    for event in await tx.get_events("Redeem", sync=False):
        if all(arg in event for arg in ("redeemer", "redeemTokens", "redeemAmount")):
            redeemer = event["redeemer"]
            redeemed = tx.token.scale_value(event["redeemTokens"])
            # cToken side
            if tx.token == event.address and tx.from_address == redeemer:
                # TODO: get rid of this rounding when we migrate to postgres
                if round(redeemed, 14) == round(tx.amount, 14):
                    return True
                print(
                    f"Compound withdrawal ctoken side does not match: {round(redeemed, 14)}  {round(tx.amount, 14)}"
                )
            # underlying side
            elif tx.to_address == redeemer and tx.from_address == event.address:
                # TODO: get rid of this rounding when we migrate to postgres
                if round(redeemed, 14) == round(tx.amount, 14):
                    return True
                print(
                    f"Compound withdrawal underlying side does not match: {round(redeemed, 14)}  {round(tx.amount, 14)}"
                )
    return False
