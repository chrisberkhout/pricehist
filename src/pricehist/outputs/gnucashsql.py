import hashlib
from datetime import datetime
from importlib.resources import read_text

from pricehist import __version__
from pricehist.format import Format

from .baseoutput import BaseOutput


class GnuCashSQL(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        src = f"pricehist:{source.id()}"

        values_parts = []
        for price in series.prices:
            date = f"{price.date} {fmt.time}"
            amount = fmt.quantize(price.amount)
            m = hashlib.sha256()
            m.update(
                "".join(
                    [date, series.base, series.quote, src, series.type, str(amount)]
                ).encode("utf-8")
            )
            guid = m.hexdigest()[0:32]
            value_num = str(amount).replace(".", "")
            value_denom = 10 ** len(f"{amount}.".split(".")[1])
            v = (
                "("
                f"'{guid}', "
                f"'{date}', "
                f"'{series.base}', "
                f"'{series.quote}', "
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
            base=series.base,
            quote=series.quote,
            values=values,
        )

        return sql
