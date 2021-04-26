from pricehist.format import Format


class CSV:
    def format(self, prices, fmt=Format()):
        lines = ["date,base,quote,amount"]
        for price in prices:
            date = str(price.date).replace("-", fmt.datesep)
            amount_parts = f"{fmt.quantize(price.amount):,}".split(".")
            amount_parts[0] = amount_parts[0].replace(",", fmt.thousands)
            amount = fmt.decimal.join(amount_parts)
            line = ",".join([date, price.base, price.quote, amount])
            lines.append(line)
        return "\n".join(lines) + "\n"
