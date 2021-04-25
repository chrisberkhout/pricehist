class Beancount:
    def format(self, prices, time=None):
        lines = []
        for price in prices:
            lines.append(
                f"{price.date} price {price.base} {price.amount} {price.quote}"
            )
        return "\n".join(lines) + "\n"


# https://beancount.github.io/docs/fetching_prices_in_beancount.html
# https://beancount.github.io/docs/beancount_language_syntax.html#commodities-currencies
# https://beancount.github.io/docs/beancount_language_syntax.html#comments
