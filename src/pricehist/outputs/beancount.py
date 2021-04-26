from pricehist.format import Format


class Beancount:
    def format(self, prices, fmt=Format()):
        lines = []
        for price in prices:

            amount_parts = f"{fmt.quantize(price.amount):,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", fmt.thousands)
            amount = ".".join(amount_parts)

            qa_parts = [amount]
            if fmt.symbol == "right":
                qa_parts = qa_parts + [price.quote]
            else:
                qa_parts = qa_parts + [" ", price.quote]
            quote_amount = "".join(qa_parts)

            date = str(price.date).replace("-", fmt.datesep)
            lines.append(f"{date} price {price.base} {quote_amount}")
        return "\n".join(lines) + "\n"


# NOTE: Beancount always has commodity to the right. It seems to be possible to
# skip the space, according to https://plaintextaccounting.org/quickref/#h.n4b87oz9ku6t

# https://beancount.github.io/docs/fetching_prices_in_beancount.html
# https://beancount.github.io/docs/beancount_language_syntax.html#commodities-currencies
# https://beancount.github.io/docs/beancount_language_syntax.html#comments
