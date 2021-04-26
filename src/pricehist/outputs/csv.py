from pricehist.formatinfo import FormatInfo


class CSV:
    def format(self, prices, format_info=FormatInfo()):
        lines = ["date,base,quote,amount"]
        for price in prices:
            date = str(price.date).replace("-", format_info.datesep)
            amount_parts = f"{price.amount:,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", format_info.thousands)
            amount = format_info.decimal.join(amount_parts)
            line = ",".join([date, price.base, price.quote, amount])
            lines.append(line)
        return "\n".join(lines) + "\n"
