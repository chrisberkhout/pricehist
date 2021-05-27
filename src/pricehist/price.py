from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Price:
    date: str
    amount: Decimal
