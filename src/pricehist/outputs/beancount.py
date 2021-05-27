from pricehist.format import Format

from .baseoutput import BaseOutput


class Beancount(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        lines = []
        for price in series.prices:
            quote_amount = fmt.format_quote_amount(series.quote, price.amount)
            # TODO warn if fmt settings make an invalid number (not . for decimal)
            # TODO warn if fmt settings make an invalid quote (not right/rightspace)

            date = str(price.date).replace("-", fmt.datesep)
            lines.append(f"{date} price {series.base} {quote_amount}")
        return "\n".join(lines) + "\n"


# NOTE: Beancount always has commodity to the right. It seems to be possible to
# skip the space, according to https://plaintextaccounting.org/quickref/#h.n4b87oz9ku6t

# https://beancount.github.io/docs/fetching_prices_in_beancount.html
# https://beancount.github.io/docs/beancount_language_syntax.html#commodities-currencies
# https://beancount.github.io/docs/beancount_language_syntax.html#comments
