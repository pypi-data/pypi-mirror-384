from typing import Final

from dao_treasury import TreasuryTx, other_expense
from y import Network


events: Final = other_expense("Events")


events("Devcon").match(
    hash="0x57bc99f6007989606bdd9d1adf91c99d198de51f61d29689ee13ccf440b244df",
    log_index=83,
)


@events("EthDenver", Network.Mainnet)
def is_eth_denver(tx: TreasuryTx) -> bool:
    return (
        tx.hash == "0x26956f86b3f4e3ff9de2779fb73533f3e1f8ce058493eec312501d0e8053fe7a"
        and tx.log_index == 179
    )
