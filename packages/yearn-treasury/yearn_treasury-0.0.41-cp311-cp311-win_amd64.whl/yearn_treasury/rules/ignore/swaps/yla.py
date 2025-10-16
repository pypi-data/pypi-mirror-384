from typing import Final

from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.rules.ignore.swaps import swaps


yla: Final = swaps("Yearn Lazy Ape")


@yla("Deposit", Network.Mainnet)
def is_yla_deposit(tx: TreasuryTx) -> bool:
    return tx.hash == "0x1d4e974db2d60ebd994410fcd793c5db771af9a14660015faf94cbdaec285009" and (
        tx.symbol == "YLA" or tx.to_address.address == "0x9ba60bA98413A60dB4C651D4afE5C937bbD8044B"  # type: ignore [union-attr]
    )


@yla("Withdrawal", Network.Mainnet)
def is_yla_withdrawal(tx: TreasuryTx) -> bool:
    return (
        "0x85c6D6b0cd1383Cc85e8e36C09D0815dAf36b9E9"
        in (
            tx.from_address.address,  # type: ignore [union-attr]
            tx.to_address.address,  # type: ignore [union-attr]
        )
        or tx.hash == "0xb1ed399c268dfaf9917e20270cb720ab95986630b6cd4cabd7f02bb55ad5f7c6"
    )
