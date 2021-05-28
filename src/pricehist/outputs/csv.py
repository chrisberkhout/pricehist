from pricehist.format import Format

from .baseoutput import BaseOutput


class CSV(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        lines = ["date,base,quote,amount,source,type"]
        for price in series.prices:
            date = fmt.format_date(price.date)
            base = fmt.base or series.base
            quote = fmt.quote or series.quote
            amount = fmt.format_num(price.amount)
            line = ",".join([date, base, quote, amount, source.id(), series.type])
            lines.append(line)
        return "\n".join(lines) + "\n"
