"""
Budget request data model for Yearn Treasury.

This module defines the BudgetRequest dataclass, which models a single
budget request and its state. It provides methods for checking approval,
rejection, streaming, vesting, and payment status.
"""

from dataclasses import dataclass
from logging import getLogger
from typing import Final, Optional, Set, final


logger: Final = getLogger(__name__)


@final
@dataclass(frozen=True)
class BudgetRequest:
    id: int
    number: int
    title: str
    state: str
    url: str
    created_at: str
    updated_at: str
    closed_at: Optional[str]
    body: Optional[str]
    labels: Set[str]

    def is_approved(self) -> bool:
        return "approved" in self.labels

    def is_rejected(self) -> bool:
        return "rejected" in self.labels

    def is_stream(self) -> bool:
        return "stream" in self.labels

    def is_vesting(self) -> bool:
        return "vesting" in self.labels

    def is_paid(self) -> bool:
        return "paid" in self.labels
