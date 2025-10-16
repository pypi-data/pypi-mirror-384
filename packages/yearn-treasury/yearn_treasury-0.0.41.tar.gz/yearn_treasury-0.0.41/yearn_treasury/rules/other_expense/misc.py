"""
Other expense rules for miscellaneous cases in Yearn Treasury.

This module defines matching logic for miscellaneous other expenses.
If it doesn't really fit anywhere else in :mod:`~other_expenses`,
it will end up in here.
"""

from dao_treasury import TreasuryTx, other_expense
from y import Network


other_expense("veYFI Launch", Network.Mainnet).match(
    hash="0x51202f9e8a9afa84a9a0c37831ca9a18508810175cb95ab7c52691bbe69a56d5",
    symbol="YFI",
)


@other_expense("yBudget Reward", Network.Mainnet)
def is_ybudget_reward(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    return (
        # Epoch 2
        (
            tx.symbol == "YFI"
            and txhash == "0xae7d281b8a093da60d39179452d230de2f1da4355df3aea629d969782708da5d"
        )
        or txhash
        in (
            # Epoch 1
            "0xa1b242b2626def6cdbe49d92a06aad96fa018c27b48719a98530c5e5e0ac61c5",
            # Epoch 3
            "0x6ba3f2bed8b766ed2185df1a492b3ecab0251747c619a5d60e7401908120c9c8",
        )
    )


@other_expense("1 YFI for Signers", Network.Mainnet)
def is_one_yfi_for_signers(tx: TreasuryTx) -> bool:
    txhash = tx.hash
    return txhash in (
        "0x86700207761cdca82a0ad4e04b49b749913de63c8bd933b4f3f9a145d9b2c1fa",
        # https://snapshot.box/#/s:veyfi.eth/proposal/0xc7ded2863a10154b6b520921af4ada48d64d74e5b7989f98cdf073542b2e4411
        "0x5ed4ce821cb09b4c6929cc9a6b5e0a23515f9bb97d9b5916819a6986f6c89f09",
        "0xe80628d90254f8da0a6016629c8811b5dd54f231e94f71697ab37d8c00482586",
    ) or (
        txhash == "0x831ad751e1be1dbb82cb9e1f5bf0e38e31327b8c58f6ad6b90bcfb396129bb11"
        and tx.log_index == 403
    )
