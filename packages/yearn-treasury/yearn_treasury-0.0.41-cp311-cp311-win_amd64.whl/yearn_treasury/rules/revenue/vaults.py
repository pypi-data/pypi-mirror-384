from logging import getLogger
from typing import Final, Optional

from dao_treasury import TreasuryTx, revenue
from eth_typing import ChecksumAddress
from faster_async_lru import alru_cache
from y import Contract, Network

from yearn_treasury.vaults import v1, v2


logger: Final = getLogger(__name__)

fees: Final = revenue("Fees")


# v1 helpers
def _is_single_sided(tx: TreasuryTx) -> bool:
    """Fees from single-sided strategies are not denominated in `vault.token`."""
    symbol = tx.symbol
    from_nickname = tx.from_nickname
    return _is_y3crv(symbol, from_nickname) or _is_ypool(symbol, from_nickname)


def _is_y3crv(symbol: str, from_nickname: str) -> bool:
    return (
        symbol == "y3Crv"
        and from_nickname.startswith("Contract: Strategy")
        and from_nickname.endswith("3pool")
    )


def _is_ypool(symbol: str, from_nickname: str) -> bool:
    return (
        symbol == "yyDAI+yUSDC+yUSDT+yTUSD"
        and from_nickname.startswith("Contract: Strategy")
        and from_nickname.endswith("ypool")
    )


@alru_cache(maxsize=1000)
async def _get_rewards(controller: Contract, block: int) -> Optional[ChecksumAddress]:
    try:
        return await controller.rewards.coroutine(block_identifier=block)  # type: ignore [no-any-return]
    except ValueError as e:
        if str(e) == "No data was returned - the call likely reverted":
            return None
        raise


@alru_cache(maxsize=None)
async def _get_controller(vault: Contract) -> Contract:
    return await Contract.coroutine(await vault.controller)  # type: ignore [return-value]


@fees("Vaults V1", Network.Mainnet)
async def is_v1_vault_fees(tx: TreasuryTx) -> bool:
    token = tx.token.address.address

    # Fees from single-sided strategies are not denominated in `vault.token` but everything else is
    is_single_sided = _is_single_sided(tx)

    for vault, underlying in v1.items():
        if token != underlying and not is_single_sided:
            continue

        controller = await _get_controller(vault)
        rewards = await _get_rewards(controller, tx.block)
        if tx.to_address != rewards:
            logger.debug(
                "to address %s doesnt match rewards address %s", tx.to_address.address, rewards
            )
            continue
        strategy: ChecksumAddress = await controller.strategies.coroutine(
            underlying, block_identifier=tx.block
        )
        if tx.from_address == strategy:
            return True
        logger.debug(
            "from address %s doesnt match strategy %s set on controller %s",
            tx.from_address.address,
            strategy,
            controller,
        )
    return False


def is_inverse_fees_from_stash_contract(from_address: str, to_nickname: str) -> bool:
    return (
        from_address == "0xE376e8e8E3B0793CD61C6F1283bA18548b726C2e"
        and to_nickname == "Token: Curve stETH Pool yVault"
    )


@fees("Vaults V2")
async def is_v2_vault_fees(tx: TreasuryTx) -> bool:
    token = tx.token.address.address
    from_address = tx.from_address.address
    if (
        from_address == token
        and (vault := v2.get(from_address))  # type: ignore [arg-type]
        and tx.to_address == await vault.rewards.coroutine(block_identifier=tx.block)
    ):
        return True

    if is_inverse_fees_from_stash_contract(from_address, tx.to_nickname):  # type: ignore [arg-type]
        if tx.value_usd > 0:  # type: ignore [operator]
            tx.value_usd *= -1  # type: ignore [operator]
        return True

    return False


@fees("Vaults V3")
def is_v3_vault_fees(tx: TreasuryTx) -> bool:
    # TODO: fill me in too
    return False


@fees("YearnFed", Network.Mainnet)
def is_yearn_fed_fees(tx: TreasuryTx) -> bool:
    symbol = tx.symbol
    from_address = tx.from_address
    # New version
    if (
        symbol in ["yvCurve-DOLA-U", "CRV"]
        and from_address == "0x64e4fC597C70B26102464B7F70B1F00C77352910"
    ):
        return True
    # Old versions
    if symbol in ["yvCurve-DOLA-U", "yveCRV-DAO"] and from_address in [
        "0x09F61718474e2FFB884f438275C0405E3D3559d3",
        "0x7928becDda70755B9ABD5eE7c7D5E267F1412042",
    ]:
        return True
    if (
        symbol == "INV"
        and tx.from_nickname == "Inverse Treasury"
        and tx.to_nickname == "ySwap Multisig"
    ):
        return True
    if (
        from_address == "0x9D5Df30F475CEA915b1ed4C0CCa59255C897b61B"
        and tx.to_nickname == "ySwap Multisig"
    ):
        return True
    return False


@fees("DOLAFRAXBP", Network.Mainnet)
def is_dolafraxbp_fees(tx: TreasuryTx) -> bool:
    return (
        tx.from_nickname == "Contract: StrategyConvexFraxBpRewardsClonable"
        and tx.to_nickname == "Yearn yChad Multisig"
        and tx.symbol == "yvCurve-DOLA-FRAXBP-U"
    )


@fees("TempleDAO Private Vault", Network.Mainnet)
def is_temple(tx: TreasuryTx) -> bool:
    if tx.to_nickname in ["Yearn Treasury", "Yearn yChad Multisig"]:  # fees have been sent to both
        from_nickname = tx.from_nickname
        symbol = tx.symbol
        if from_nickname == "Contract: StrategyConvexCrvCvxPairsClonable" and symbol == "CRV":
            return True
        elif from_nickname == "Contract: Splitter" and symbol in ["yveCRV-DAO", "CRV"]:
            return True
    return False
