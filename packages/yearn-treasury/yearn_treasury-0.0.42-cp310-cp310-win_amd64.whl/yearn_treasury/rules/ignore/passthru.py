from decimal import Decimal
from typing import Final, Tuple

from dao_treasury import TreasuryTx, TreasuryWallet, ignore
from eth_typing import BlockNumber, ChecksumAddress
from y import Network

from yearn_treasury.constants import CHAINID, YSWAP_MULTISIG, ZERO_ADDRESS


passthru: Final = ignore("Pass-Thru")

cowswap_router: Final = "0x9008D19f58AAbD9eD0D60971565AA8510560ab41"
ycrv: Final = "0xFCc5c47bE19d06BF83eB04298b026F81069ff65b"


@passthru("Sent to dinobots to dump", Network.Mainnet)
def is_sent_to_dinoswap(tx: TreasuryTx) -> bool:
    """These tokens are dumpped and the proceeds sent back to the origin strategy."""
    return tx.from_nickname == "Contract: Strategy" and tx.to_nickname == "yMechs Multisig"


@passthru("Bribes for yCRV", Network.Mainnet)
def is_ycrv(tx: TreasuryTx) -> bool:
    """These are routed thru cowswap with dai as the purchase token."""
    ymechs = "0x2C01B4AD51a67E2d8F02208F54dF9aC4c0B778B6"

    from_address = tx.from_address
    symbol = tx.symbol
    if (from_address == YSWAP_MULTISIG and symbol == "DAI") or (
        from_address == ymechs and symbol == "3Crv"
    ):
        if tx.to_address == cowswap_router:
            for trade in tx.get_events("Trade"):
                (
                    owner,
                    sell_token,
                    buy_token,
                    sell_amount,
                    buy_amount,
                    fee_amount,
                    order_uid,
                ) = trade.values()
                if tx.from_address == owner and tx.token == sell_token and buy_token == ycrv:
                    scaled = Decimal(sell_amount) / 10**18
                    # TODO: remove this rounding when we implement postgres
                    if round(scaled, 11) == round(tx.amount, 11):
                        return True
                    print(f"bribes for ycrv amount no match: [{scaled}, {tx.amount}]")

    elif tx.hash in {
        # one off exception case to correct accounting mix-up
        "0x1578f3b0d3158d305167c39dc29ada08914e1ddb67ef9698e1b0421432f9aed6",
        # A few donations from ySwap
        "0xb2e335500b33b42edd8a97f57db35e0561df9a3a811d0cd73dce9767c23da0c4",
        "0xc02aab3a84b3bbfbc18f0ee6aa742f233d97511f653b4a40e7cd8f822851e10a",
        "0x8a2dba62eac44fdfc7ff189016ac601c9da664f5dea42d647f2e552319db2f7d",
        "0xd2c0a137d03811c5e4c27be19c7893f7fdd5851bdd6f825ee7301f3634033035",
    }:
        return True
    return is_dola_bribe(tx)


def is_dola_bribe(tx: TreasuryTx) -> bool:
    return (
        tx.from_nickname == "ySwap Multisig"
        and tx.to_nickname == "Contract: GPv2Settlement"
        and tx.symbol == "DOLA"
    )


passthru("BAL Rewards", Network.Mainnet).match(
    hash="0xf4677cce1a08ecd54272cdc1b23bc64693450f8bb5d6de59b8e58e288ec3b2a7",
    symbol="BAL",
)


@passthru("StrategyAuraUSDClonable", Network.Mainnet)
def is_aura(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    if (
        txhash == "0x1621ba5c9b57930c97cc43d5d6d401ee9c69fed435b0b458ee031544a10bfa75"
        and tx.symbol in ["BAL", "AURA"]
    ):
        return True
    return (
        txhash == "0x996b5911a48319133f50f72904e70ed905c08c81e2c03770e0ccc896be873bd4"
        and tx.symbol == "AURA"
    )


@passthru("yPrisma Strategy Migration", Network.Mainnet)
def is_yprisma_migration(tx: TreasuryTx) -> bool:
    # strategies were changed a few times
    txhash = tx.hash
    if txhash in (
        "0x4c19259ff9e23c2f23653b7560526c2dbd5adef2d53c297b63d8c1fa6f4906f1",
        "0xed39b66c01e25b053117778c80e544c985d962522233b49ce6f7fe136b1a4474",
    ):
        return True
    return (
        txhash == "0x45bb5d7c25393c5bb8ad9647ae60ff39ddc39d695f0e427eb45f91b04f42c636"
        and tx.symbol == "yPRISMA"
    )


@passthru("rKP3R", Network.Mainnet)
def is_rkp3r(tx: TreasuryTx) -> bool:
    if tx.symbol == "rKP3R":
        from_nickname = tx.from_nickname
        to_nickname = tx.to_nickname
        if (
            from_nickname == "Contract: StrategyConvexFixedForexClonable"
            and to_nickname == "Yearn yChad Multisig"
        ):
            return True
        elif (
            from_nickname == "Yearn yChad Multisig"
            and to_nickname == "Contract: StrategyConvexFixedForexClonable"
        ):
            return True
    return False


@passthru("Inverse-earned YearnFed Fees", Network.Mainnet)
def is_inverse_fees_from_yearn_fed(tx: TreasuryTx) -> bool:
    return tx.symbol == "yvDOLA-U" and tx.to_nickname == "Contract: YearnFed"


@passthru("stkAAVE", Network.Mainnet)
def is_stkaave(tx: TreasuryTx) -> bool:
    """stkAAVE is sent from a strategy to ychad, then to sms for unwrapping."""
    if tx.symbol == "stkAAVE":
        from_nickname = tx.from_nickname
        to_nickname = tx.to_nickname
        if "Strategy" in from_nickname and to_nickname == "Yearn yChad Multisig":
            return True
        elif from_nickname == "Yearn yChad Multisig" and to_nickname == "Yearn Strategist Multisig":
            return True
    return False


@passthru("StrategyIdle", Network.Mainnet)
def is_idle(tx: TreasuryTx) -> bool:
    return tx.hash in {
        "0x59595773ee4304ba4e7e06d2c02541781d93867f74c6c83056e7295b684036c7",
        "0x4c7685aa3dfa9f375c612a2773951b9edbe059102b505423ed28a97d2692e75a",
        "0xb17317686b57229aeb7f06103097b47dc2eafa34489c40af70d2ac57bcf8f455",
        "0xfd9e6fd303fdbb358207bf3ba069b7f6a21f82f6b082605056d54948127e81e8",
        "0x41c8428fd361c54bb80cdac752e31622915ac626dd1e9270f02af1dc2c84d1f9",
        "0x9c0d169c7362a7fe436ae852c1aee58a5905d10569abbd50261f65cb0574dc3a",
        "0x55d89a5890cfe80da06f6831fdfa3a366c0ed9cf9b7f1b4d53f5007bb9698fa0",
        "0x6c6fc43dca1841af82b517bc5fc53ea8607e3f95512e4dd3009c0dbb425669f7",
    }


_factory_strat_to_yield_tokens = {
    "Contract: StrategyCurveBoostedFactoryClonable": ("CRV", "LDO"),
    "Contract: StrategyConvexFactoryClonable": ("CRV", "CVX"),
    "Contract: StrategyConvexFraxFactoryClonable": ("CRV", "CVX", "FXS"),
}


@passthru("Factory Vault Yield", Network.Mainnet)
def is_factory_vault_yield(tx: TreasuryTx) -> bool:
    return tx.to_nickname == "yMechs Multisig" and tx.symbol in _factory_strat_to_yield_tokens.get(
        tx.from_nickname, ()
    )


@passthru("CowSwap Migration", Network.Mainnet)
def is_cowswap_migration(tx: TreasuryTx) -> bool:
    """A one-time tx that transferred tokens from an old contract to its replacement."""
    return tx.hash == "0xb50341d3db2ff4a39b9bfa21753893035554ae44abb7d104ab650753db1c4855"


def is_curve_bribe(tx: TreasuryTx) -> bool:
    """All present and future curve bribes are committed to yveCRV holders."""
    from_nickname = tx.from_nickname
    if from_nickname == "Contract: CurveYCRVVoter" and tx.hash not in [
        # took place before bribes were committed to yveCRV
        "0x6824345c8a0c1f0b801d8050bb6f587032c4a9fa153faa113d723a2068d844f4",
        # was a whitehat hack of the v1 bribe contract, necessary to safeguard user funds
        "0xfcef3911809770fe351b2b526e4ee0274589a3f7d6ef9408a8f5643fa006b771",
    ]:
        return True

    # Bribe V3
    elif from_nickname == "Contract: yBribe" and tx.to_nickname in [
        "Yearn Treasury",
        "ySwap Multisig",
    ]:
        return True

    # NOTE: I added this one-off to capture tokens sent to BribeSplitter 0x527e80008D212E2891C737Ba8a2768a7337D7Fd2
    return tx.hash == "0xce45da7e3a7616ed0c0d356d6dfa8a784606c9a8034bae9faa40abf7b52be114"


_pass_thru_hashes: Tuple[str, ...] = {
    Network.Mainnet: ("0xf662c68817c56a64b801181a3175c8a7e7a5add45f8242990c695d418651e50d",),
    Network.Fantom: (
        "0x411d0aff42c3862d06a0b04b5ffd91f4593a9a8b2685d554fe1fbe5dc7e4fc04",
        "0xa347da365286cc912e4590fc71e97a5bcba9e258c98a301f85918826538aa021",
    ),
}.get(
    CHAINID, ()
)  # type: ignore [call-overload]


@passthru("Misc.", Network.Mainnet)
def is_misc_passthru_mainnet(tx: TreasuryTx) -> bool:
    # not sure if we still need this, TODO figure it out
    # NOTE skipped the hashmatcher to do strange things ... there is probably a better way to do this
    if tx.hash in _pass_thru_hashes and str(tx.log_index).lower() != "nan":
        return True

    txhash = tx.hash
    if txhash in {
        "0xae6797ad466de75731117df46ccea5c263265dd6258d596b9d6d8cf3a7b1e3c2",
        "0x2a6191ba8426d3ae77e2a6c91de10a6e76d1abdb2d0f831c6c5aad52be3d6246",
        # https://github.com/yearn/chief-multisig-officer/pull/924
        "0x25b54e113e58a3a4bbffc011cdfcb8c07a0424f33b0dbda921803d82b88f1429",
        "0xcb000dd2b623f9924fe0234831800950a3269b2d412ce9eeabb0ec65cd737059",
    }:
        return True
    # do these need hueristics? build real sort logic if these keep reoccurring
    elif txhash == "0x14faeac8ee0734875611e68ce0614eaf39db94a5ffb5bc6f9739da6daf58282a" and (
        tx.symbol in ("CRV", "CVX", "yPRISMA") or tx.log_index == 254
    ):
        return True
    return False


@passthru("Misc.", Network.Fantom)
def is_misc_passthru_fantom(tx: TreasuryTx) -> bool:
    # not sure if we still need this, TODO figure it out
    # NOTE skipped the hashmatcher to do strange things ... there is probably a better way to do this
    if tx.hash in _pass_thru_hashes and str(tx.log_index).lower() != "nan":
        return True

    if tx.hash == "0x14faeac8ee0734875611e68ce0614eaf39db94a5ffb5bc6f9739da6daf58282a":
        return True
    # Passing thru to yvWFTM
    if (
        tx.symbol == "WFTM"
        and TreasuryWallet.check_membership(tx.from_address.address, tx.block)  # type: ignore [arg-type, union-attr]
        and tx.to_address == "0x0DEC85e74A92c52b7F708c4B10207D9560CEFaf0"
    ):
        # dont want to accidenally sort a vault deposit here
        is_deposit = False
        for event in tx.get_events("Transfer"):
            sender, receiver, _ = event.values()
            if (
                tx.to_address == event.address
                and sender == ZERO_ADDRESS
                and tx.from_address == receiver
            ):
                is_deposit = True
        if not is_deposit:
            return True
    return False


@passthru("yvBoost INCOMPLETE", Network.Mainnet)
def is_buying_yvboost(tx: TreasuryTx) -> bool:
    """Bought back yvBoost is unwrapped and sent back to vault holders."""
    symbol = tx.symbol
    block: BlockNumber = tx.block  # type: ignore [assignment]
    from_address: ChecksumAddress = tx.from_address.address  # type: ignore [union-attr, assignment]
    to_address: ChecksumAddress = tx.to_address.address  # type: ignore [union-attr, assignment]
    if (
        symbol == "SPELL"
        and TreasuryWallet.check_membership(from_address, block)
        and to_address == cowswap_router
    ):
        return True

    elif (
        symbol == "yveCRV-DAO"
        and TreasuryWallet.check_membership(from_address, block)
        and to_address
        in (
            "0xd7240B32d24B814fE52946cD44d94a2e3532E63d",
            "0x7fe508eE30316e3261079e2C81f4451E0445103b",
        )
    ):
        return True

    elif (
        symbol == "3Crv"
        and from_address == "0xd7240B32d24B814fE52946cD44d94a2e3532E63d"
        and TreasuryWallet.check_membership(to_address, block)
    ):
        return True

    # SPELL bribe handling
    elif symbol == "SPELL":
        if tx.to_nickname in ("Abracadabra Treasury", "Contract: BribeSplitter"):
            return True

    return tx in (
        "0x9eabdf110efbfb44aab7a50eb4fe187f68deae7c8f28d78753c355029f2658d3",
        "0x5a80f5ff90fc6f4f4597290b2432adbb62ab4154ead68b515accdf19b01c1086",
        "0x848b4d629e137ad8d8eefe5db40eab895c9959b9c210d0ae0fef16a04bfaaee1",
        "0x896663aa9e2633b5d152028bdf84d7f4b1137dd27a8e61daca3863db16bebc4f",
        "0xd8aa1e5d093a89515530b7267a9fd216b97fddb6478b3027b2f5c1d53070cd5f",
        "0x169aab84b408fce76e0b776ebf412c796240300c5610f0263d5c09d0d3f1b062",
        "0xe6fefbf061f4489cd967cdff6aa8aca616f0c709e08c3696f12b0027e9e166c9",
        "0x10be8a3345660f3c51b695e8716f758b1a91628bd612093784f0516a604f79c1",
    )
