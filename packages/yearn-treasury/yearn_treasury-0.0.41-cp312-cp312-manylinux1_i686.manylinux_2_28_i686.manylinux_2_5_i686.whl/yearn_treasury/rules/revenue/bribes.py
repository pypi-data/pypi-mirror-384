from typing import Final

from dao_treasury import TreasuryTx, revenue


bribes: Final = revenue("Bribes")


@bribes("yCRV Bribes")
def is_ycrv_bribe(tx: TreasuryTx) -> bool:
    return (
        tx.from_nickname
        in [
            # OLD
            "Contract: BribeSplitter",
            # NEW
            "Contract: YCRVSplitter",
            # done manually during migration
        ]
        or tx.hash == "0x3c635388812bed82845c0df3531583399fdf736ccfb95837b362379766955f2d"
    )


@bribes("yBribe Fees")
def is_ybribe_fees(tx: TreasuryTx) -> bool:
    return False
