from decimal import Decimal
from typing import Final

from brownie import ZERO_ADDRESS
from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.constants import YFI
from yearn_treasury.rules.ignore.swaps import swaps


WOOFY: Final = "0xD0660cD418a64a1d44E9214ad8e459324D8157f1"

YFI_SCALE: Final = Decimal(10**18)
WOOFY_SCALE: Final = Decimal(10**12)


@swaps("WOOFY", Network.Mainnet)
def is_woofy(tx: TreasuryTx) -> bool:
    """
    Returns True if the tx involved wrapping or unwrapping WOOFY.

    https://docs.yearn.fi/resources/deprecated/woofy
    """

    # Wrapping, YFI side
    if tx.to_address == WOOFY and tx.symbol == "YFI":
        # Check for WOOFY transfer
        for transfer in tx.get_events("Transfer"):
            if transfer.address != WOOFY:
                continue
            sender, receiver, amount = transfer.values()
            if sender == ZERO_ADDRESS and tx.from_address == receiver:
                scaled = Decimal(amount) / YFI_SCALE
                if scaled == tx.amount:
                    return True
                print(f"woofy wrapping woofy side amount no match: [{scaled}, {tx.amount}]")

    # Wrapping, WOOFY side
    elif tx.from_address == ZERO_ADDRESS and tx.symbol == "WOOFY":
        # Check for YFI transfer
        for transfer in tx.get_events("Transfer"):
            if transfer.address != YFI:
                continue
            sender, receiver, amount = transfer.values()
            if receiver == WOOFY and tx.to_address == sender:
                scaled = Decimal(amount) / WOOFY_SCALE
                if scaled == tx.amount:
                    return True
                print(f"woofy wrapping yfi side amount no match: [{scaled}, {tx.amount}]")

    # Unwrapping, YFI side
    elif tx.from_address == WOOFY and tx.symbol == "YFI":
        # Check for WOOFY transfer
        for transfer in tx.get_events("Transfer"):
            if transfer.address != WOOFY:
                continue
            sender, receiver, amount = transfer.values()
            if tx.to_address == sender and receiver == ZERO_ADDRESS:
                scaled = round(Decimal(amount) / YFI_SCALE, 12)
                rounded = round(tx.amount, 12)
                if scaled == rounded:
                    return True
                print(f"woofy unwrapping yfi side amount no match: [{scaled}, {rounded}]")

    # Unwrapping, WOOFY side
    elif tx.to_address == ZERO_ADDRESS and tx.symbol == "WOOFY":
        # Check for YFI transfer
        for transfer in tx.get_events("Transfer"):
            if transfer.address != YFI:
                continue
            sender, receiver, amount = transfer.values()
            if sender == WOOFY and tx.from_address == receiver:
                # TODO remove this rounding once sqlite is replaced with postgres
                scaled = round(Decimal(amount) / WOOFY_SCALE, 7)
                rounded = round(tx.amount, 7)
                if scaled == rounded:
                    return True
                print(f"woofy unwrapping woofy side amount no match: [{scaled}, {rounded}]")
    return False
