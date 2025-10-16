"""These predate the yteam revshare splitting implementation so were done manually"""

from typing import Final

from dao_treasury import other_expense
from y import Network


revshare: Final = other_expense("Revshare")


revshare("yAudit", Network.Mainnet).match(
    hash="0xdf3e6cf2e50052e4eeb57fb2562b5e1b02701014ce65b60e6c8a850c409b341a",
    log_index=127,
)

revshare("yLockers", Network.Mainnet).match(
    hash="0x038aeb3351b762bc92c5e4274c01520ae08dc314e2282ececc2a19a033d994a8",
    log_index=163,
)
