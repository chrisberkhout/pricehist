from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    time: str = "00:00:00"
    decimal: str = "."
    thousands: str = ""
    symbol: str = "rightspace"
    datesep: str = "-"

    def format_num(self, num):
        parts = f"{num:,}".split(".")
        parts[0] = parts[0].replace(",", self.thousands)
        result = self.decimal.join(parts)
        return result
