class CSV():

    def format(self, prices):
        lines = ["date,base,quote,amount"]
        for price in prices:
            date = str(price.date).translate(str.maketrans('-','/'))
            line = ','.join([price.date, price.base, price.quote, str(price.amount)])
            lines.append(line)
        return "\n".join(lines)
