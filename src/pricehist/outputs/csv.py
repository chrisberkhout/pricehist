import csv
import io

from pricehist.format import Format

from .baseoutput import BaseOutput


class CSV(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
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
