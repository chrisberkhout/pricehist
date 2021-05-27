from dataclasses import dataclass, field

from pricehist.price import Price


@dataclass(frozen=True)
class Series:
    base: str
    quote: str
    type: str
    start: str
    end: str
    prices: list[Price] = field(default_factory=list)
