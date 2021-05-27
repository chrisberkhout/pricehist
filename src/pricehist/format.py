from dataclasses import dataclass
from decimal import Decimal, getcontext


@dataclass(frozen=True)
class Format:
    time: str = "00:00:00"
    decimal: str = "."
    thousands: str = ""
    symbol: str = "rightspace"
    datesep: str = "-"
