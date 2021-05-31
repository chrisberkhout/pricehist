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
            output += f"P {date} {fmt.time} {base} {quote_amount}\n"
        return output

    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # > The commodity may be any non-numeric string that does not contain a
    # > period, comma, forward slash or at-sign. It may appear before or after
    # > the amount, although it is assumed that symbols appearing before the
    # > amount refer to currencies, while non-joined symbols appearing after the
    # > amount refer to commodities.

    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts
    # > A commoditized amount is an integer amount which has an associated
    # > commodity. This commodity can appear before or after the amount, and may
    # > or may not be separated from it by a space. Most characters are allowed
    # > in a commodity name, except for the following:
    # > - Any kind of white-space
    # > - Numerical digits
    # > - Punctuation: .,;:?!
    # > - Mathematical and logical operators: -+*/^&|=
    # > - Bracketing characters: <>[](){}
    # > - The at symbol: @
    # > And yet, any of these may appear in a commodity name if it is
    # > surrounded by double quotes
