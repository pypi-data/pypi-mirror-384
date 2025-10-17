from typing import Final

from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.rules.ignore.swaps import swaps


auctions: Final = swaps("Auctions")

YEARNFI_DUTCH_AUCTIONS: Final = "0x861fE45742f70054917B65bE18904662bD0dBd30"


@auctions("Auction Proceeds", Network.Mainnet)
async def is_auction_proceeds(tx: TreasuryTx) -> bool:
    # NOTE: the other side of these swaps is currently recorded under
    # 'Ignore:Internal Transfer' when it goes to the Generic bucket contract
    if tx.from_nickname != "Contract: GPv2Settlement":
        return False

    for trade in await tx.get_events("Trade", sync=False):
        if trade["owner"] != YEARNFI_DUTCH_AUCTIONS or tx.token != trade["buyToken"]:
            continue
        buy_amount = tx.token.scale_value(trade["buyAmount"])
        if round(buy_amount, 14) == round(tx.amount, 14):
            return True
        print(
            f"auction proceeds amount does not match: {round(buy_amount, 14)}  {round(tx.amount, 14)}"
        )

    return False
