from dataclasses import dataclass, field, replace
from decimal import Decimal, getcontext

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

    def quantize(self, decimal_places):
        return replace(
            self,
            prices=[
                replace(p, amount=self._quantize(p.amount, decimal_places))
                for p in self.prices
            ],
        )

    def rename_base(self, new_base):
        return replace(self, base=new_base)

    def rename_quote(self, new_quote):
        return replace(self, quote=new_quote)

    def _quantize(self, amount, decimal_places):
        digits = len(amount.as_tuple().digits)
        exponent = amount.as_tuple().exponent

        fractional_digits = -exponent
        whole_digits = digits - fractional_digits
        max_decimal_places = getcontext().prec - whole_digits

        chosen_decimal_places = min(decimal_places, max_decimal_places)
        rounding = Decimal("0." + ("0" * chosen_decimal_places))

        return amount.quantize(rounding)
