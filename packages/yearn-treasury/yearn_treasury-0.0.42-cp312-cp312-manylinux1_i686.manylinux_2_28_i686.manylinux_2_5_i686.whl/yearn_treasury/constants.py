from pathlib import Path
from typing import Final, Set

import y.constants
from eth_typing import BlockNumber, ChecksumAddress
from y import Network, convert


CHAINID: Final = y.constants.CHAINID

EEE_ADDRESS: Final = "0xEeeeeEeeeEeEeeEeEeEeeEEEeeeeEeeeeeeeEEeE"
ZERO_ADDRESS: Final = "0x0000000000000000000000000000000000000000"

_YEARN_TREASURY_ROOT_DIR: Final = Path(__file__).parent

TREASURY_MULTISIGS: Final = {
    Network.Mainnet: "0x93A62dA5a14C80f265DAbC077fCEE437B1a0Efde",
    Network.Fantom: "0x89716Ad7EDC3be3B35695789C475F3e7A3Deb12a",
    Network.Arbitrum: "0x1deb47dcc9a35ad454bf7f0fcdb03c09792c08c1",
    Network.Optimism: "0x84654e35E504452769757AAe5a8C7C6599cBf954",
    Network.Base: "0x02ff746D8cb62709aEEc611CeC9B17d7dD1D3480",
}

YCHAD_MULTISIGS: Final = {
    Network.Mainnet: "0xFEB4acf3df3cDEA7399794D0869ef76A6EfAff52",
    Network.Fantom: "0xC0E2830724C946a6748dDFE09753613cd38f6767",
    Network.Gnosis: "0x22eAe41c7Da367b9a15e942EB6227DF849Bb498C",
    Network.Arbitrum: "0xb6bc033d34733329971b938fef32fad7e98e56ad",
    Network.Optimism: "0xF5d9D6133b698cE29567a90Ab35CfB874204B3A7",
    Network.Base: "0xbfAABa9F56A39B814281D68d2Ad949e88D06b02E",
}

YSWAP_MULTISIGS: Final = {
    Network.Mainnet: "0x7d2aB9CA511EBD6F03971Fb417d3492aA82513f0",
}


if CHAINID not in TREASURY_MULTISIGS or CHAINID not in YCHAD_MULTISIGS:
    raise RuntimeError(f"{Network(CHAINID)} is not supported")


TREASURY_MULTISIG: Final = convert.to_address(TREASURY_MULTISIGS[CHAINID])  # type: ignore [index]

YCHAD_MULTISIG: Final = convert.to_address(YCHAD_MULTISIGS[CHAINID])  # type: ignore [index]

__yswap_multisig = YSWAP_MULTISIGS.get(CHAINID)  # type: ignore [call-overload]
YSWAP_MULTISIG: Final = convert.to_address(__yswap_multisig) if __yswap_multisig else None

_TREASURY_WALLETS: Final = {
    Network.Mainnet: {
        TREASURY_MULTISIG,
        YCHAD_MULTISIG,
        "0xb99a40fcE04cb740EB79fC04976CA15aF69AaaaE",  # Yearn Treasury V1
        "0x5f0845101857d2A91627478e302357860b1598a1",  # Yearn KP3R Wallet
        YSWAP_MULTISIG,
        "0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6",  # yMechs Multisig
        "0xE376e8e8E3B0793CD61C6F1283bA18548b726C2e",  # Fee Reimbursement Stash
        "0xC001d00d425Fa92C4F840baA8f1e0c27c4297a0B",  # New token dumping wallet
        "0x4fc1b14cD213e7B6212145Ba4f180C3d53d1A11e",  # veFarming wallet
    },
}

TREASURY_WALLETS: Final = {
    convert.to_address(address) for address in _TREASURY_WALLETS.get(CHAINID, set())  # type: ignore [call-overload]
}


YFI: Final = {
    Network.Mainnet: "0x0bc529c00C6401aEF6D220BE8C6Ea1667F6Ad93e",
    Network.Fantom: "0x29b0Da86e484E1C0029B56e817912d778aC0EC69",
    Network.Arbitrum: "0x82e3A8F066a6989666b031d916c43672085b1582",
    Network.Polygon: "0xDA537104D6A5edd53c6fBba9A898708E465260b6",
}.get(
    CHAINID, None
)  # type: ignore [call-overload]


class Args:
    wallets: Final[Path] = _YEARN_TREASURY_ROOT_DIR / "wallets.yaml"
    # TODO: update dashboard def to use this label (we will need to migrate the provisioning files to yearn-treasury but we need to do this anyway for yearn-specific additions)
    label: Final[str] = "Treasury"  # "Yearn"
    first_tx_block: Final = BlockNumber({Network.Mainnet: 10_502_337}.get(CHAINID, 0))  # type: ignore [call-overload]
    export_start_block: Final = first_tx_block

    sort_rules: Final[Path] = _YEARN_TREASURY_ROOT_DIR / "rules"
    """The path where the sort rules for dao-treasury are defined."""

    nicknames: Final[Path] = _YEARN_TREASURY_ROOT_DIR / "address_labels.yaml"
    """The path where yearn-treasury's address nicknames are defined."""
