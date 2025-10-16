from typing import Final
from dao_treasury import TreasuryTx, revenue
from y import Network


seasolver: Final = revenue("Seasolver", Network.Mainnet)


@seasolver("Positive Slippage")
def is_seasolver_slippage_revenue(tx: TreasuryTx) -> bool:
    # TODO: check this earlier, probably in dao-treasury internals
    # After may 1 2023 ymechs wallet separated from yearn treasury
    return (
        tx.block <= 17162286
        and tx.from_nickname == "Contract: TradeHandler"
        and tx.to_nickname == "yMechs Multisig"
    )


@seasolver("CowSwap Incentives")
def is_cowswap_incentive(tx: TreasuryTx) -> bool:
    """Incentives for swapping on CowSwap"""
    return tx.symbol == "COW" and tx.from_address == "0xA03be496e67Ec29bC62F01a428683D7F9c204930"
