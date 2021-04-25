class CSV:
    def format(self, prices, time=None):
        lines = ["date,base,quote,amount"]
        for price in prices:
            line = ",".join([price.date, price.base, price.quote, str(price.amount)])
            lines.append(line)
        return "\n".join(lines) + "\n"
