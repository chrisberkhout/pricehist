from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Price:
    base: str
    quote: str
    date: str
    amount: Decimal
