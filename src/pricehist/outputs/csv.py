from pricehist.format import Format


class CSV:
    def format(self, series, source=None, fmt=Format()):
        lines = ["date,base,quote,amount,source,type"]
        for price in series.prices:
            date = str(price.date).replace("-", fmt.datesep)
            amount_parts = f"{fmt.quantize(price.amount):,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", fmt.thousands)
            amount = fmt.decimal.join(amount_parts)
            line = ",".join(
                [date, series.base, series.quote, amount, source.id(), series.type]
            )
            lines.append(line)
        return "\n".join(lines) + "\n"
