# mypy: disable-error-code="index"
from typing import Final

from y import Network
from y.constants import CHAINID


EEE_ADDRESS: Final = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS: Final = "0x0000000000000000000000000000000000000000"


YFI: Final = {
    Network.Mainnet: "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    Network.Fantom: "0x29b0Da86e484E1C0029B56e817912d778aC0EC69",
    Network.Arbitrum: "0x82e3A8F066a6989666b031d916c43672085b1582",
    Network.Polygon: "0xDA537104D6A5edd53c6fBba9A898708E465260b6",
}[CHAINID]
