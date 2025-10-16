from dao_treasury import TreasuryTx, other_expense
from y import Network


bugs = other_expense("Bug Reimbursements")


@bugs("yDAI Fee Calculation Bug", Network.Mainnet)
def is_double_fee_reimbursement(tx: TreasuryTx) -> bool:
    """
    Due to new single-sided strats that deposit into other vaults,
    some users were accidentally charged 2x the expected withdrawal fee.
    """
    return tx.from_nickname == "Disperse.app" and tx.hash in [
        "0x4ce0c829fb46fc1ea03e434599a68af4c6f65f80aff7e934a008c0fe63e9da3f",
        "0x90b54bf0d35621160b5094c263a2684f8e7b37fc6467c8c1ce6a53e2e7acbfa1",
        "0x2f667223aaefc4b153c28440d151fdb19333aff5d052c0524f2804fbd5a7964c",
    ]


@bugs("yYFI Fee Calculation Bug", Network.Mainnet)
def is_yyfi_fee_reimbursement(tx: TreasuryTx) -> bool:
    return (
        tx.from_nickname == "Disperse.app"
        and tx.hash == "0x867b547b67910a08c939978d8071acca28ecc444d7155c0626e87730f67c058c"
    )


@bugs("yvCurve-IB Fee Calculation Bug", Network.Mainnet)
def is_lossy_fee_reimbursement(tx: TreasuryTx) -> bool:
    """old vault code doesn't prevent fees from making harvest lossy. so here we airdrop the fee-take back to vault and do some housekeeper to prevent this from happening on other strats."""
    return (
        tx.hash == "0x61eea3d40b2dc8586a5d20109ed962998c43cc55a37c300f283820150490eaa0"
        and tx.log_index == 179
    )


@bugs("Reimburse st-yCRV User", Network.Mainnet)
def is_stycrv(tx: TreasuryTx) -> bool:
    """Some user lost some funds in a minor issue, then was reimbursed."""
    return (
        tx.hash == "0x491f07d134f3253ef06a2b46d83b82cdf2927b13cce4d38225d92ce01799da96"
        and tx.log_index == 197
    )


@bugs("Slippage Bug", Network.Mainnet)
def is_slippage_bug_reimbursement(tx: TreasuryTx) -> bool:
    """a swap tx was messed up so Yearn sent treasury funds to the relevant strategy to compensate"""
    txhash = tx.hash
    if txhash in [
        "0xffe3883e34ae0b6ae3a7f304f00c625a7b315a021cf38f47a932e81d3f1c371c",
        "0x42cfcaa06beebe61547724f22fa790c763b2937ca2af8e3d5dbc680b903aad69",
    ]:
        return True

    other = {
        # separate slippage event
        "0xc179e27f0e38bca52744d71dc6ff2463ed10fa918908ce28adcf4f4c0d6d6a1e": 103,
        "0x51c611597574aaa3b829004363476b1c2a4dc2941dff695c26c100498b695b4f": 214,
    }

    return txhash in other and tx.log_index == other[txhash]


@bugs("Reimburse GUSD Vault Bug", Network.Mainnet)
def is_gusd_vault_bug_reimbursement(tx: TreasuryTx) -> bool:
    return (
        tx.symbol == "GUSD"
        and tx.hash == "0x22f62d0922c430232aa402296055d79a6cf5c36a8b6253a7f1f46f1e1f66e277"
        and tx.log_index != 65
    )


@bugs("Reimburse DAI Vault Bug", Network.Mainnet)
def is_dai_vault_reimbursement(tx: TreasuryTx) -> bool:
    # this is from very early days, I'm not sure if it's documented anywhere
    return (
        tx.hash == "0x61ad3697ab56316ffdc7b8eaaeee57d0b3f8d4fed3e283eee35c6c38eed594e0"
        and tx.log_index == 202
    )
