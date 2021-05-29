from dataclasses import dataclass


@dataclass(frozen=True)
class Format:
    base: str = None
    quote: str = None
    time: str = "00:00:00"
    decimal: str = "."
    thousands: str = ""
    symbol: str = "rightspace"
    datesep: str = "-"
    csvdelim: str = ","

    @classmethod
    def fromargs(cls, args):
        def if_not_none(value, default):
            return default if value is None else value

        default = cls()
        return cls(
            base=if_not_none(args.formatbase, default.base),
            quote=if_not_none(args.formatquote, default.quote),
            time=if_not_none(args.formattime, default.time),
            decimal=if_not_none(args.formatdecimal, default.decimal),
            thousands=if_not_none(args.formatthousands, default.thousands),
            symbol=if_not_none(args.formatsymbol, default.symbol),
            datesep=if_not_none(args.formatdatesep, default.datesep),
            csvdelim=if_not_none(args.formatcsvdelim, default.csvdelim),
        )

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
