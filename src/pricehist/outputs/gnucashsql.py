import hashlib
import logging
import re
from datetime import datetime
from importlib.resources import read_text
from decimal import Decimal

from pricehist import __version__
from pricehist.format import Format

from .baseoutput import BaseOutput


class GnuCashSQL(BaseOutput):
    def format(self, series, source=None, fmt=Format()):
        base = fmt.base or series.base
        quote = fmt.quote or series.quote
        src = f"pricehist:{source.id()}"

        self._warn_about_backslashes(
            {
                "time": fmt.time,
                "base": base,
                "quote": quote,
                "source": src,
                "price type": series.type,
            }
        )

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

            value_num, value_denom = self._rational(price.amount)
            v = (
                "("
                + ", ".join(
                    [
                        self._sql_str(guid),
                        self._sql_str(date),
                        self._sql_str(base),
                        self._sql_str(quote),
                        self._sql_str(src),
                        self._sql_str(series.type),
                        str(value_num),
                        str(value_denom),
                    ]
                )
                + ")"
            )
            values_parts.append(v)
        values = ",\n".join(values_parts)

        sql = read_text("pricehist.resources", "gnucash.sql").format(
            version=__version__,
            timestamp=datetime.utcnow().isoformat() + "Z",
            base=self._sql_str(base),
            quote=self._sql_str(quote),
            values=values,
        )

        return sql

    def _warn_about_backslashes(self, fields):
        hits = [name for name, value in fields.items() if "\\" in value]
        if hits:
            logging.warn(
                f"Before running this SQL, check the formatting of the "
                f"{self._english_join(hits)} strings. "
                f"SQLite treats backslahes in strings as plain characters, but "
                f"MariaDB/MySQL and PostgreSQL may interpret them as escape "
                f"codes."
            )

    def _english_join(self, strings):
        if len(strings) == 0:
            return ""
        elif len(strings) == 1:
            return str(strings[0])
        else:
            return f"{', '.join(strings[0:-1])} and {strings[-1]}"

    def _sql_str(self, s):
        # Documentation regarding SQL string literals
        # - https://www.sqlite.org/lang_expr.html#literal_values_constants_
        # - https://mariadb.com/kb/en/string-literals/
        # - https://dev.mysql.com/doc/refman/8.0/en/string-literals.html
        # - https://www.postgresql.org/docs/devel/sql-syntax-lexical.html
        escaped = re.sub("'", "''", s)
        quoted = f"'{escaped}'"
        return quoted

    def _rational(self, number: Decimal) -> (str, str):
        tup = number.as_tuple()
        sign = "-" if tup.sign == 1 else ""
        if tup.exponent > 0:
            numerator = (
                sign + "".join([str(d) for d in tup.digits]) + ("0" * tup.exponent)
            )
            denom = str(1)
        else:
            numerator = sign + "".join([str(d) for d in tup.digits])
            denom = str(10 ** -tup.exponent)
        return (numerator, denom)
