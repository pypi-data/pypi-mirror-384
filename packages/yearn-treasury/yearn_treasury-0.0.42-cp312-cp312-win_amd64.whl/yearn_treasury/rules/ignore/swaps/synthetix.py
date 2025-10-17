from dao_treasury import TreasuryTx
from y import Network

from yearn_treasury.rules.ignore.swaps import swaps


@swaps("Synthetix", Network.Mainnet)
def is_synthetix_swap(tx: TreasuryTx) -> bool:
    # TODO Figure out hueristics for sorting these if they become more frequent
    return tx.hash == "0x5a55121911d9a3992fc1ea9504da9b86331da2148822d88c16f805b2c6b2c753"
