import hashlib
from datetime import datetime
from importlib.resources import read_text

from pricehist import __version__


class GnuCashSQL:
    def format(self, prices):
        source = "pricehist"
        typ = "unknown"

        values_parts = []
        for price in prices:
            date = f"{price.date} 00:00:00"
            m = hashlib.sha256()
            m.update(
                "".join(
                    [date, price.base, price.quote, source, typ, str(price.amount)]
                ).encode("utf-8")
            )
            guid = m.hexdigest()[0:32]
            value_num = str(price.amount).replace(".", "")
            value_denom = 10 ** len(f"{price.amount}.".split(".")[1])
            v = (
                "("
                f"'{guid}', "
                f"'{date}', "
                f"'{price.base}', "
                f"'{price.quote}', "
                f"'{source}', "
                f"'{typ}', "
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
