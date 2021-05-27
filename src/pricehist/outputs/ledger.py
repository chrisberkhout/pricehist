from pricehist.format import Format

from .baseoutput import BaseOutput


class Ledger(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        lines = []
        for price in series.prices:
            date = fmt.format_date(price.date)
            quote_amount = fmt.format_quote_amount(series.quote, price.amount)
            lines.append(f"P {date} {fmt.time} {series.base} {quote_amount}")
        return "\n".join(lines) + "\n"

    # TODO support additional details of the format:
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts
