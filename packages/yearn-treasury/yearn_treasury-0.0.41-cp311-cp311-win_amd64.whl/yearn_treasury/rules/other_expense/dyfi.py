from typing import Final

from dao_treasury import TreasuryTx, other_expense
from pony.orm import commit
from y import Network


dyfi: Final = other_expense("dYFI")


@dyfi("Launch", Network.Mainnet)
def is_dyfi_launch(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    if txhash == "0x2ec726e5ee52cdc063e61795d1b96a75d16fd91824136c990b7c3ddd52b28e31":
        # unused returned
        if tx.amount > 0:
            tx.amount *= -1
            commit()
        if tx.value_usd > 0:  # type: ignore [operator]
            tx.value_usd *= -1  # type: ignore [operator]
            commit()
        return True
    return txhash == "0x066c32f02fc0908d55b6651afcfb20473ec3d99363de222f2e8f4a7e0c66462e"


@dyfi("Redemptions", Network.Mainnet)
def is_dyfi_redemptions(tx: TreasuryTx) -> bool:
    """YFI going to the dyfi redemptions contract"""
    return tx.symbol == "YFI" and tx.to_nickname == "dYFI Redemption Contract"
