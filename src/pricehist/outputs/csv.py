"""
CSV output

Comma Separated Values output is easily processed with other command-line tools
or imported into a spreadsheet or database.

Python's `csv <https://docs.python.org/3/library/csv.html>`_ module is used to
produce Excel-style CSV output, except with UNIX-style line endings. The field
delimiter can be set with a formatting option, and date, number and base/quote
formatting options will be respected.

Classes:

    CSV

"""

import csv
import io

from pricehist.format import Format

from .baseoutput import BaseOutput


class CSV(BaseOutput):
    def format(self, series, source, fmt=Format()):
        output = io.StringIO()
        writer = csv.writer(
            output,
            delimiter=fmt.csvdelim,
            lineterminator="\n",
            quotechar='"',
            doublequote=True,
            skipinitialspace=False,
            quoting=csv.QUOTE_MINIMAL,
        )

        header = ["date", "base", "quote", "amount", "source", "type"]
        writer.writerow(header)

        base = fmt.base or series.base
        quote = fmt.quote or series.quote

        for price in series.prices:
            date = fmt.format_date(price.date)
            amount = fmt.format_num(price.amount)
            writer.writerow([date, base, quote, amount, source.id(), series.type])

        return output.getvalue()
