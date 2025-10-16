import decimal
from typing import Final

from brownie.exceptions import EventLookupError
from dao_treasury import TreasuryTx
from y import WRAPPED_GAS_COIN, Network

from yearn_treasury.constants import YCHAD_MULTISIG
from yearn_treasury.rules.ignore.swaps import swaps


buying_yfi: Final = swaps("Buying YFI")

VYPER_BUYERS: Final = (
    "0xdf5e4E54d212F7a01cf94B3986f40933fcfF589F",  # buys YFI for DAI at the current chainlink price
    "0x6903223578806940bd3ff0C51f87aa43968424c8",  # buys YFI for DAI at the current chainlink price. Can be funded via llamapay stream.
)
"""These contracts, now retired, previously were used to purchase YFI for DAI at the current chainlink market price."""


YFI_BUYBACK_AUCTIONS: Final = "0x4349ed200029e6Cf38F1455B9dA88981F1806df3"


Decimal: Final = decimal.Decimal


@buying_yfi("Top-up Buyer Contract", Network.Mainnet)
def is_buyer_top_up(tx: TreasuryTx) -> bool:
    """
    The sell side of these transactions is in :func:`is_buying_with_buyer`.
    The buyer is topped up with DAI regularly and buys YFI at the current chainlink market price.

    # TODO: amortize this into a daily expense
    """
    return tx.symbol == "DAI" and tx.to_address.address in VYPER_BUYERS  # type: ignore [union-attr]


@buying_yfi("Buyer Contract", Network.Mainnet)
def is_buying_with_buyer(tx: TreasuryTx) -> bool:
    """
    The buy side of these transactions is in :func:`is_buyer_top_up`.
    The buyer is topped up with DAI regularly and buys YFI at the current chainlink market price
    """
    if tx.symbol == "YFI" and tx.to_address.address == YCHAD_MULTISIG:  # type: ignore [union-attr]
        try:
            events = tx.events
        except KeyError as e:
            if "components" in str(e):
                print(f"cannot parse events of possible YFI buyback {tx}")
                return False
            raise

        if "Buyback" in events:
            buyback_events = events["Buyback"]
            if len(buyback_events) > 1:
                print(f"Must code handler for multiple Buyback events in one tx: {tx}")
                return False
            buyback_event = buyback_events[0]
            if buyback_event.address in VYPER_BUYERS and all(  # type: ignore [attr-defined]
                arg in buyback_event for arg in ("buyer", "yfi", "dai")
            ):
                # TODO get rid of this rounding once we've swapped out sqlite for postgres
                buyback_amount = Decimal(buyback_event["yfi"]) / 10**18  # type: ignore [call-overload]
                if round(tx.amount, 14) == round(buyback_amount, 14):
                    return True
                print(
                    f"from node: {buyback_amount} "
                    f"from db: {tx.amount} "
                    f"diff: {buyback_amount - tx.amount}"
                )
            else:
                print("unhandled Buyback event: buyback_event")
    return False


@buying_yfi("Buyback Auction", Network.Mainnet)
def is_buying_with_auction(tx: TreasuryTx) -> bool:
    try:
        if tx.symbol != "YFI" or tx.to_address != YCHAD_MULTISIG or "AuctionTaken" not in tx.events:
            return False
    except EventLookupError:
        return False
    except KeyError as e:
        # TODO: diagnose and fix this, pretty sure it's in eth-event
        if "components" not in str(e):
            raise
        return False

    auctions_taken = tx.get_events("AuctionTaken")
    if len(auctions_taken) == 0:
        return False
    if len(auctions_taken) > 1:
        raise NotImplementedError("we need new code to handle this case")
    event = auctions_taken[0]
    if event.address != YFI_BUYBACK_AUCTIONS:  # type: ignore [attr-defined]
        raise ValueError(event.address, event)  # type: ignore [attr-defined]
    # did the auction contract send weth to tx.sender?
    for transfer in tx.get_events("Transfer"):
        if transfer.address == WRAPPED_GAS_COIN:
            sender, receiver, amount = transfer.values()
            if sender != YFI_BUYBACK_AUCTIONS:
                print(f"Transfer sender is not YFI_BUYBACK_AUCTIONS:  sender={sender}  YFI_BUYBACK_AUCTIONS={YFI_BUYBACK_AUCTIONS}")  # type: ignore [union-attr]
                continue
            if tx.from_address != receiver:
                print(f"Transfer does not match auction taker:  taker={tx.from_address.address}  transfer={receiver}")  # type: ignore [union-attr]
                continue
            # TODO get rid of this rounding once we've swapped out sqlite for postgres
            if round(amount, 14) == round(event["taken"], 14):  # type: ignore [call-overload]
                return True
            print(f"AuctionTaken: {event} amount does not match Transfer: {transfer}")
    return False
