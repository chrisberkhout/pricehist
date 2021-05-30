import hashlib
from datetime import datetime
from importlib.resources import read_text

from pricehist import __version__
from pricehist.format import Format

from .baseoutput import BaseOutput


class GnuCashSQL(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        base = fmt.base or series.base
        quote = fmt.quote or series.quote
        src = f"pricehist:{source.id()}"

        values_parts = []
        for price in series.prices:
            date = f"{fmt.format_date(price.date)} {fmt.time}"
            m = hashlib.sha256()
            m.update(
                "".join(
                    [
                        date,
                        base,
                        quote,
                        src,
                        series.type,
                        str(price.amount),
                    ]
                ).encode("utf-8")
            )
            guid = m.hexdigest()[0:32]
            value_num, value_denom = self._fractional(price.amount)
            v = (
                "("
                f"'{guid}', "
                f"'{date}', "
                f"'{base}', "
                f"'{quote}', "
                f"'{src}', "
                f"'{series.type}', "
                f"{value_num}, "
                f"{value_denom}"
                ")"
            )
            values_parts.append(v)
        values = ",\n".join(values_parts)

        sql = read_text("pricehist.resources", "gnucash.sql").format(
            version=__version__,
            timestamp=datetime.utcnow().isoformat() + "Z",
            base=base,
            quote=quote,
            values=values,
        )

        return sql

    def _fractional(num):
        num = str(num).replace(".", "")
        denom = 10 ** len(f"{num}.".split(".")[1])
        return (num, denom)
