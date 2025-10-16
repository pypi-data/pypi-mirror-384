from typing import Final

from dao_treasury import TreasuryTx, ignore
from y import Network


YGOV: Final = "0xBa37B002AbaFDd8E89a1995dA52740bbC013D992"


@ignore("Transfer to yGov (Deprecated)", Network.Mainnet)
def is_sent_to_ygov(tx: TreasuryTx) -> bool:
    return (
        tx.from_nickname == "Yearn Treasury"
        and tx.symbol == "yDAI+yUSDC+yUSDT+yTUSD"
        and tx.to_address == YGOV
    )
