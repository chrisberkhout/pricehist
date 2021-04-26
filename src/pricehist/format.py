from dataclasses import dataclass
from decimal import Decimal, getcontext


@dataclass(frozen=True)
class Format:
    time: str = "00:00:00"
    decimal: str = "."
    thousands: str = ""
    symbol: str = "rightspace"
    datesep: str = "-"
    decimal_places: int = None

    def quantize(self, num):
        if self.decimal_places is None:
            return num
        else:
            prec = getcontext().prec
            digits = len(num.as_tuple().digits)
            exponent = num.as_tuple().exponent

            fractional_digits = -exponent
            whole_digits = digits - fractional_digits
            max_decimal_places = prec - whole_digits
            chosen_decimal_places = min(self.decimal_places, max_decimal_places)

            return num.quantize(Decimal("0." + ("0" * chosen_decimal_places)))
