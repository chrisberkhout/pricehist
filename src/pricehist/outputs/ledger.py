class Ledger():

    def format(self, prices):
        lines = []
        for price in prices:
            date = str(price.date).translate(str.maketrans('-','/'))
            lines.append(f"P {date} 00:00:00 {price.base} {price.amount} {price.quote}")
        return "\n".join(lines)

    # TODO support additional details of the format:
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commodities-and-Currencies
    # https://www.ledger-cli.org/3.0/doc/ledger3.html#Commoditized-Amounts

