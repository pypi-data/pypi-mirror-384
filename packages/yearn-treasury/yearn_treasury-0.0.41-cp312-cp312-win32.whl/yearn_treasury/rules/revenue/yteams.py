from typing import Final

from dao_treasury import TreasuryTx, revenue
from y import Network


OXSPLIT_CONTRACT: Final = "0x2ed6c4B5dA6378c7897AC67Ba9e43102Feb694EE"
SPLITS_WAREHOUSE_CONTRACT: Final = "0x8fb66F38cF86A3d5e8768f8F1754A24A6c661Fb8"


@revenue("yTeam Rev Share", Network.Mainnet)
def is_yteam_rev_share(tx: TreasuryTx) -> bool:
    return tx.from_address in [OXSPLIT_CONTRACT, SPLITS_WAREHOUSE_CONTRACT] or tx.hash in [
        # These predate the split implementation and must be accounted for separately
        # yAudit
        "0x6e4f4405bd0970d42a48795a5219c14c763705f6ea9879affea652438758c065",
    ]
