from pricehist.format import Format


class Ledger:
    def format(self, prices, fmt=Format()):
        lines = []
        for price in prices:
            date = str(price.date).replace("-", fmt.datesep)

            amount_parts = f"{fmt.quantize(price.amount):,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", fmt.thousands)
            amount = fmt.decimal.join(amount_parts)

            qa_parts = [amount]
            if fmt.symbol == "left":
                qa_parts = [price.quote] + qa_parts
            elif fmt.symbol == "leftspace":
                qa_parts = [price.quote, " "] + qa_parts
            elif fmt.symbol == "right":
                qa_parts = qa_parts + [price.quote]
            else:
                qa_parts = qa_parts + [" ", price.quote]
            quote_amount = "".join(qa_parts)

            lines.append(f"P {date} {fmt.time} {price.base} {quote_amount}")
        return "\n".join(lines) + "\n"

    # TODO support additional details of the format:
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts
