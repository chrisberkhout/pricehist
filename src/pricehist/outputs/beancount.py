from pricehist.format import Format

from .baseoutput import BaseOutput


class Beancount(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        output = ""
        for price in series.prices:
            # TODO warn if fmt settings make an invalid number (not . for decimal)
            # TODO warn if fmt settings make an invalid quote (not right/rightspace)
            date = fmt.format_date(price.date)
            base = fmt.base or series.base
            quote = fmt.quote or series.quote
            quote_amount = fmt.format_quote_amount(quote, price.amount)
            output += f"{date} price {base} {quote_amount}\n"
        return output


# NOTE: Beancount always has commodity to the right. It seems to be possible to
# skip the space, according to https://plaintextaccounting.org/quickref/#h.n4b87oz9ku6t

# https://beancount.github.io/docs/fetching_prices_in_beancount.html
# https://beancount.github.io/docs/beancount_language_syntax.html#commodities-currencies
# https://beancount.github.io/docs/beancount_language_syntax.html#comments
