from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    time: str = "00:00:00"
    decimal: str = "."
    thousands: str = ""
    symbol: str = "rightspace"
    datesep: str = "-"

    def format_date(self, date):
        return str(date).replace("-", self.datesep)

    def format_quote_amount(self, quote, amount):
        formatted_amount = self.format_num(amount)

        if self.symbol == "left":
            qa_parts = [quote, formatted_amount]
        elif self.symbol == "leftspace":
            qa_parts = [quote, " ", formatted_amount]
        elif self.symbol == "right":
            qa_parts = [formatted_amount, quote]
        else:
            qa_parts = [formatted_amount, " ", quote]

        quote_amount = "".join(qa_parts)

        return quote_amount

    def format_num(self, num):
        parts = f"{num:,}".split(".")
        parts[0] = parts[0].replace(",", self.thousands)
        result = self.decimal.join(parts)
        return result
