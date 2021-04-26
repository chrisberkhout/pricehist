from pricehist.formatinfo import FormatInfo


class Ledger:
    def format(self, prices, format_info=FormatInfo()):
        fi = format_info
        lines = []
        for price in prices:
            date = str(price.date).replace("-", fi.datesep)

            amount_parts = f"{price.amount:,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", format_info.thousands)
            amount = format_info.decimal.join(amount_parts)

            qa_parts = [amount]
            if format_info.symbol == "left":
                qa_parts = [price.quote] + qa_parts
            elif format_info.symbol == "leftspace":
                qa_parts = [price.quote, " "] + qa_parts
            elif format_info.symbol == "right":
                qa_parts = qa_parts + [price.quote]
            else:
                qa_parts = qa_parts + [" ", price.quote]
            quote_amount = "".join(qa_parts)

            lines.append(f"P {date} {fi.time} {price.base} {quote_amount}")
        return "\n".join(lines) + "\n"

    # TODO support additional details of the format:
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts
