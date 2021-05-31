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

        too_big = False
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

            value_num, value_denom, fit = self._rational(price.amount)
            too_big |= not fit
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
        values_comment = "" if values_parts else "-- "

        if too_big:
            # https://code.gnucash.org/docs/MAINT/group__Numeric.html
            # https://code.gnucash.org/docs/MAINT/structgnc__price__s.html
            logging.warn(
                "This SQL contains numbers outside of the int64 range required "
                "by GnuCash for the numerators and denominators of prices. "
                "Using the --quantize option to limit the number of decimal "
                "places will usually reduce the size of the rational form as "
                "well."
            )

        sql = read_text("pricehist.resources", "gnucash.sql").format(
            version=__version__,
            timestamp=datetime.utcnow().isoformat() + "Z",
            base=self._sql_str(base),
            quote=self._sql_str(quote),
            values_comment=values_comment,
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

    def _rational(self, number: Decimal) -> (str, str, bool):
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
        fit = self._fit_in_int64(Decimal(numerator), Decimal(denom))
        return (numerator, denom, fit)

    def _fit_in_int64(self, *numbers):
        return all(n >= -(2 ** 63) and n <= (2 ** 63) - 1 for n in numbers)
