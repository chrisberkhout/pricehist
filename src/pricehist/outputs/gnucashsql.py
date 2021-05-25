import hashlib
from datetime import datetime
from importlib.resources import read_text

from pricehist import __version__
from pricehist.format import Format


class GnuCashSQL:
    def format(self, prices, source=None, type=None, fmt=Format()):
        src = f"pricehist:{source.id()}"

        values_parts = []
        for price in prices:
            date = f"{price.date} {fmt.time}"
            amount = fmt.quantize(price.amount)
            m = hashlib.sha256()
            m.update(
                "".join([date, price.base, price.quote, src, type, str(amount)]).encode(
                    "utf-8"
                )
            )
            guid = m.hexdigest()[0:32]
            value_num = str(amount).replace(".", "")
            value_denom = 10 ** len(f"{amount}.".split(".")[1])
            v = (
                "("
                f"'{guid}', "
                f"'{date}', "
                f"'{price.base}', "
                f"'{price.quote}', "
                f"'{src}', "
                f"'{type}', "
                f"{value_num}, "
                f"{value_denom}"
                ")"
            )
            values_parts.append(v)
        values = ",\n".join(values_parts)

        sql = read_text("pricehist.resources", "gnucash.sql").format(
            version=__version__,
            timestamp=datetime.utcnow().isoformat() + "Z",
            base=price.base,
            quote=price.quote,
            values=values,
        )

        return sql
