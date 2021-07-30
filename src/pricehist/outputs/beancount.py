"""
Beancount output

Supports the `Beancount <https://beancount.github.io/>`_ plain text accounting
format.

The default output should be valid for Beancount. Customizing it via formatting
options may generate invalid output, so users should keep the requirements of
the Beancount format in mind.

Relevant sections of the Beancount documentation:

* `Commodities / Currencies
   <https://beancount.github.io/docs/beancount_language_syntax.html#commodities-currencies>`_
* `Prices <https://beancount.github.io/docs/beancount_language_syntax.html#prices>`_
* `Fetching Prices in Beancount
   <https://beancount.github.io/docs/fetching_prices_in_beancount.html>`_

Classes:

    Beancount

"""

from pricehist.format import Format

from .baseoutput import BaseOutput


class Beancount(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        output = ""
        for price in series.prices:
            date = fmt.format_date(price.date)
            base = fmt.base or series.base
            quote = fmt.quote or series.quote
            quote_amount = fmt.format_quote_amount(quote, price.amount)
            output += f"{date} price {base} {quote_amount}\n"
        return output
