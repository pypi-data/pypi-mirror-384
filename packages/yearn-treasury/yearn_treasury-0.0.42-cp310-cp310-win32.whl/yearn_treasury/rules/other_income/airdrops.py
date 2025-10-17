from typing import Final

from dao_treasury import TreasuryTx, other_income
from y import Network


airdrop: Final = other_income("Airdrop")

_SAFE_AIRDROP_CONTRACTS: Final = (
    "0xA0b937D5c8E32a80E3a8ed4227CD020221544ee6",
    "0xC0fde70A65C7569Fe919bE57492228DEE8cDb585",
)


@airdrop("SAFE", Network.Mainnet)
def is_safe_airdrop(tx: TreasuryTx) -> bool:
    return tx.symbol == "SAFE" and tx.from_address.address in _SAFE_AIRDROP_CONTRACTS  # type: ignore [union-attr]


@airdrop("Other", Network.Mainnet)
def is_airdrop(tx: TreasuryTx) -> bool:
    return tx.hash in {
        "0x327684dab9e3ce61d125b36fe0b59cbfbc8aa5ac7a5b051125ab7cac3b93b90b",
        "0x44f7d3b2030799ea45932baf6049528a059aabd6387f3128993d646d01c8e877",  # TKX
        "0xf2dbe58dffd3bc1476755e9f74e2ae07531579d0a3ea9e2aaac2ef902e080c2a",  # TKX
        "0x8079e9cae847da196dc5507561bc9d1434f765f05045bc1a82df735ec83bc6ec",  # MTV
        # NOTE: this one was rec'd elsewhere, dumped, and WETH sent to treasury
        "0xc12ded505ea158717890e4ae6e7ab5eb5cb61edbc13dfd125dd0e6f9b1af9477",  # Gnosis SAFE airdrop
        "0x7c086a82b43b2f49db93b76a0698cf86a9c620b3bf924f0003175b04a17455ad",  # PRISMA
    }
