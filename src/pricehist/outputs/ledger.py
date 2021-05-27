from pricehist.format import Format

from .baseoutput import BaseOutput


class Ledger(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        lines = []
        for price in series.prices:
            date = str(price.date).replace("-", fmt.datesep)

            amount_parts = f"{fmt.quantize(price.amount):,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", fmt.thousands)
            amount = fmt.decimal.join(amount_parts)

            qa_parts = [amount]
            if fmt.symbol == "left":
                qa_parts = [series.quote] + qa_parts
            elif fmt.symbol == "leftspace":
                qa_parts = [series.quote, " "] + qa_parts
            elif fmt.symbol == "right":
                qa_parts = qa_parts + [series.quote]
            else:
                qa_parts = qa_parts + [" ", series.quote]
            quote_amount = "".join(qa_parts)

            lines.append(f"P {date} {fmt.time} {series.base} {quote_amount}")
        return "\n".join(lines) + "\n"

    # TODO support additional details of the format:
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts
