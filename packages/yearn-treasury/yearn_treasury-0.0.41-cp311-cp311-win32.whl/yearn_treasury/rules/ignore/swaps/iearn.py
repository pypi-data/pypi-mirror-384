# mypy: disable-error-code=dict-item
from typing import Dict, Final

from dao_treasury import TreasuryTx
from eth_typing import ChecksumAddress
from y import Contract, Network

from yearn_treasury.constants import ZERO_ADDRESS
from yearn_treasury.rules.ignore.swaps import swaps


IEARN: Final[Dict[str, ChecksumAddress]] = {
    # v1 - deprecated
    # v2
    "yDAIv2": "0x16de59092dAE5CcF4A1E6439D611fd0653f0Bd01",
    "yUSDCv2": "0xd6aD7a6750A7593E092a9B218d66C0A814a3436e",
    "yUSDTv2": "0x83f798e925BcD4017Eb265844FDDAbb448f1707D",
    "ysUSDv2": "0xF61718057901F84C4eEC4339EF8f0D86D2B45600",
    "yTUSDv2": "0x73a052500105205d34daf004eab301916da8190f",
    "yWBTCv2": "0x04Aa51bbcB46541455cCF1B8bef2ebc5d3787EC9",
    # v3
    "yDAIv3": "0xC2cB1040220768554cf699b0d863A3cd4324ce32",
    "yUSDCv3": "0x26EA744E5B887E5205727f55dFBE8685e3b21951",
    "yUSDTv3": "0xE6354ed5bC4b393a5Aad09f21c46E101e692d447",
    "yBUSDv3": "0x04bC0Ab673d88aE9dbC9DA2380cB6B79C4BCa9aE",
}

POOLS: Final = set(IEARN.values())

POOL_TO_UNDERLYING: Final[Dict[ChecksumAddress, ChecksumAddress]] = {
    pool: ChecksumAddress(Contract(pool).token()) for pool in POOLS
}


@swaps("iEarn:Withdrawal", Network.Mainnet)
def is_iearn_withdrawal(tx: TreasuryTx) -> bool:
    # Vault side
    if tx.to_address == ZERO_ADDRESS:
        return tx.token.address.address in POOLS
    # Token side
    from_address: ChecksumAddress = tx.from_address.address  # type: ignore [union-attr, assignment]
    token_address = tx.token.address.address
    return POOL_TO_UNDERLYING.get(from_address) == token_address
