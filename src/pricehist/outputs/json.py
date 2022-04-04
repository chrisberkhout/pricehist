"""
JSON output

Date, number and base/quote formatting options will be respected.

Classes:

    JSON

"""

import io
import json

from pricehist.format import Format

from .baseoutput import BaseOutput


class JSON(BaseOutput):
    def __init__(self, jsonl=False):
        self.jsonl = jsonl

    def format(self, series, source, fmt=Format()):
        data = []
        output = io.StringIO()

        base = fmt.base or series.base
        quote = fmt.quote or series.quote

        for price in series.prices:
            date = fmt.format_date(price.date)
            amount = fmt.format_num(price.amount)

            data.append(
                {
                    "date": date,
                    "base": base,
                    "quote": quote,
                    "amount": amount,
                    "source": source.id(),
                    "type": series.type,
                }
            )

        if self.jsonl:
            for row in data:
                json.dump(row, output, ensure_ascii=False)
                output.write("\n")
        else:
            json.dump(data, output, ensure_ascii=False, indent=2)
            output.write("\n")

        return output.getvalue()
