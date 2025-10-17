# mypy: disable-error-code="union-attr"
from decimal import Decimal
from typing import Final, Optional

from dao_treasury import TreasuryTx, other_income
from y import Contract, ContractNotVerified, ERC20, Network  # type: ignore [attr-defined]

from yearn_treasury.rules.constants import ZERO_ADDRESS


_POINT_ONE: Final = Decimal("0.1")


@other_income("aToken Yield", Network.Mainnet)
def is_atoken_yield(tx: TreasuryTx) -> bool:
    return (
        tx.symbol in ("aLEND", "aLINK")
        and tx.from_address.address == ZERO_ADDRESS
        and tx.to_nickname in ("Yearn Treasury", "Yearn Treasury V1")
    )


@other_income("RoboVault Thank You", Network.Fantom)
async def is_robovault_share(tx: TreasuryTx) -> bool:
    """
    After Yearn devs helped robovault with a vulnerability, robovault committed to sending Yearn a portion of their fees.
    """
    if not tx.symbol.startswith("rv") and tx.from_address.is_contract:
        return False

    try:
        strat = await Contract.coroutine(tx.from_address.address)
    except ContractNotVerified:
        return False
    else:
        vault: Optional[Contract] = getattr(strat, "vault", None)

    if vault is None:
        return False

    if await vault.coroutine(block_identifier=tx.block) == tx.token:
        return True

    return (
        tx.from_nickname == "Contract: Strategy"
        and tx.symbol == "rv3USDCc"
        and await ERC20(  # type: ignore [call-overload]
            await vault.coroutine(block_identifier=tx.block),
            asynchronous=True,
        ).symbol
        == "rv3USDCb"
    )


@other_income("Cowswap Gas Reimbursement", Network.Mainnet)
def is_cowswap_gas_reimbursement(tx: TreasuryTx) -> bool:
    return (
        tx.symbol == "ETH"
        and tx.from_nickname == "Cowswap Multisig"
        and tx.to_nickname == "yMechs Multisig"
    )


@other_income("USDS Referral Code", Network.Mainnet)
def is_usds_referral_code(tx: TreasuryTx) -> bool:
    """Yearn earns some USDS for referring deposits to Maker"""
    return (
        tx.symbol == "USDS"
        and tx.from_address.address == "0x3C5142F28567E6a0F172fd0BaaF1f2847f49D02F"
    )


@other_income("yETH Application Fee", Network.Mainnet)
def is_yeth_application_fee(tx: TreasuryTx) -> bool:
    return tx.symbol == "yETH" and tx.to_nickname == "Yearn Treasury" and tx.amount == _POINT_ONE


@other_income("yPRISMA Fees", Network.Mainnet)
def is_yprisma_fees(tx: TreasuryTx) -> bool:
    return tx.symbol == "yvmkUSD-A" and tx.from_nickname == "Contract: YPrismaFeeDistributor"
