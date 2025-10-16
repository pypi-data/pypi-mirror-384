from decimal import Decimal

from dao_treasury import TreasuryTx, expense
from y import Network


@expense("SMS Discretionary Budget", networks=Network.Mainnet)
def is_sms_discretionary_budget(tx: TreasuryTx) -> bool:
    return (
        tx.to_nickname == "Yearn Strategist Multisig"
        and tx.symbol == "DAI"
        and tx.amount == Decimal(200_000)
    )
