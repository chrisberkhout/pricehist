"""
Ledger output

Supports both `Ledger <https://www.ledger-cli.org/>`_ and
`hledger <https://hledger.org/>`_ plain text accounting formats.

By default the output should be valid for Ledger, but can be customized for
hledger or other variants via formatting options. Invalid variants are
possible, so the user should be familiar with the requirements of the target
format.

Relevant sections of the Ledger manual:

* `Commodities and Currencies
   <https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies>`_
* `Commoditized Amounts
   <https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts>`_

Relevant sections of the hledger manual:

* `Declaring market prices <https://hledger.org/hledger.html#declaring-market-prices>`_:
* `Declaring commodities <https://hledger.org/hledger.html#declaring-commodities`_:

Classes:

    Ledger

"""

from pricehist.format import Format

from .baseoutput import BaseOutput


class Ledger(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        output = ""
        for price in series.prices:
            date = fmt.format_date(price.date)
            base = fmt.base or series.base
            quote = fmt.quote or series.quote
            quote_amount = fmt.format_quote_amount(quote, price.amount)
            timesep = " " if fmt.time else ""
            output += f"P {date}{timesep}{fmt.time} {base} {quote_amount}\n"
        return output
