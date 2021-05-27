from dataclasses import dataclass, field, replace

from pricehist.price import Price


@dataclass(frozen=True)
class Series:
    base: str
    quote: str
    type: str
    start: str
    end: str
    prices: list[Price] = field(default_factory=list)

    def invert(self):
        return replace(
            self,
            base=self.quote,
            quote=self.base,
            prices=[Price(date=p.date, amount=(1 / p.amount)) for p in self.prices],
        )

    def rename_base(self, new_base):
        return replace(self, base=new_base)

    def rename_quote(self, new_quote):
        return replace(self, quote=new_quote)
