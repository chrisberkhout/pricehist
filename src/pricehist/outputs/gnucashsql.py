"""
GnuCash SQL output

Support for the `GnuCash <https://www.gnucash.org/>`_ accounting program is
achieved by generating SQL that can later be applied to a GnuCash database.

This allows pricehist to support GnuCash with simple text output rather than by
depending on GnuCash Python bindings or direct database interaction.

The generated SQL can be run in SQLite, MariaDB/MySQL or PostgreSQL.

Rows in GnuCash's prices table must include GUIDs for the related commodities.
The generated SQL selects the relevant GUIDs by mnemonic from the commodities
table and stores them in a temporary table. Another temprary table is populated
with new price data and the two are joined to produce the new rows that are
inserted into the prices table.

Users need to ensure that the base and quote of the new prices already have
commodities with matching mnemonics in the GnuCash database. If this condition
is not met, the SQL will fail without making changes. The names of the base and
quote can be adjusted with pricehist formatting options in case the source and
GnuCash names don't already match. Other formatting options can adjust date
formatting and the time of day used.

Each row in the prices table has a GUID of its own. These are generated in
pricehist by hashing the price data, so the same GUID will always be used for a
given date, base, quote, source, type & amount. Existing GUIDs are skipped
during the final insert into the prices table, so there's no problem with
running one SQL file multiple times or running multiple SQL files with
overlapping data.

Warnings are generated when string escaping or number limit issues are detected
and it should be easy for users to avoid those issues.

Classes:

    GnuCashSQL

"""

import hashlib
import logging
from datetime import datetime
from decimal import Decimal
from importlib.resources import read_text

from pricehist import __version__
from pricehist.format import Format

from .baseoutput import BaseOutput


class GnuCashSQL(BaseOutput):
    def format(self, series, source, fmt=Format()):
        base = fmt.base or series.base
        quote = fmt.quote or series.quote
        src = source.id()

        self._warn_about_backslashes(
            {
                "date": fmt.format_date("1970-01-01"),
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
            logging.warning(
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
            logging.warning(
                f"Before running this SQL, check the formatting of the "
                f"{self._english_join(hits)} strings. "
                f"SQLite treats backslashes in strings as plain characters, but "
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
        # Documentation regarding SQL string literals:
        # * https://www.sqlite.org/lang_expr.html#literal_values_constants_
        # * https://mariadb.com/kb/en/string-literals/
        # * https://dev.mysql.com/doc/refman/8.0/en/string-literals.html
        # * https://www.postgresql.org/docs/devel/sql-syntax-lexical.html
        escaped = s.replace("'", "''")
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
