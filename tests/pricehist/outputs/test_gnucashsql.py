import dataclasses
import logging
import re
from decimal import Decimal

import pytest

from pricehist.format import Format
from pricehist.outputs.gnucashsql import GnuCashSQL
from pricehist.price import Price
from pricehist.series import Series


@pytest.fixture
def out():
    return GnuCashSQL()


@pytest.fixture
def series():
    prices = [
        Price("2021-01-01", Decimal("24139.4648")),
        Price("2021-01-02", Decimal("26533.576")),
        Price("2021-01-03", Decimal("27001.2846")),
    ]
    return Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03", prices)


@pytest.fixture
def src(mocker):
    source = mocker.MagicMock()
    source.id = mocker.MagicMock(return_value="coindesk")
    return source


def test_format_base_and_quote(out, series, src):
    result = out.format(series, src, Format())
    base, quote = re.findall(r"WHERE mnemonic = (.*) LIMIT", result, re.MULTILINE)
    assert base == "'BTC'"
    assert quote == "'EUR'"


def test_format_new_price_values(out, series, src):
    result = out.format(series, src, Format())
    values = re.search(
        r"\(guid, date, base, quote, source, type, "
        r"value_num, value_denom\) VALUES\n([^;]*);",
        result,
        re.MULTILINE,
    )[1]
    assert values == (
        "('0c4c01bd0a252641b806ce46f716f161', '2021-01-01 00:00:00', "
        "'BTC', 'EUR', 'coindesk', 'close', 241394648, 10000),\n"
        "('47f895ddfcce18e2421387e0e1b636e9', '2021-01-02 00:00:00', "
        "'BTC', 'EUR', 'coindesk', 'close', 26533576, 1000),\n"
        "('0d81630c4ac50c1b9b7c8211bf99c94e', '2021-01-03 00:00:00', "
        "'BTC', 'EUR', 'coindesk', 'close', 270012846, 10000)\n"
    )


def test_format_customized(out, series, src):
    fmt = Format(
        base="XBT",
        quote="EURO",
        datesep="/",
        time="23:59:59",
    )
    result = out.format(series, src, fmt)
    base, quote = re.findall(r"WHERE mnemonic = (.*) LIMIT", result, re.MULTILINE)
    values = re.search(
        r"\(guid, date, base, quote, source, type, "
        r"value_num, value_denom\) VALUES\n([^;]*);",
        result,
        re.MULTILINE,
    )[1]
    assert base == "'XBT'"
    assert quote == "'EURO'"
    assert values == (
        "('448173eef5dea23cea9ff9d5e8c7b07e', '2021/01/01 23:59:59', "
        "'XBT', 'EURO', 'coindesk', 'close', 241394648, 10000),\n"
        "('b6c0f4474c91c50e8f65b47767f874ba', '2021/01/02 23:59:59', "
        "'XBT', 'EURO', 'coindesk', 'close', 26533576, 1000),\n"
        "('2937c872cf0672863e11b9f46ee41e09', '2021/01/03 23:59:59', "
        "'XBT', 'EURO', 'coindesk', 'close', 270012846, 10000)\n"
    )


def test_format_escaping_of_strings(out, series, src):
    result = out.format(series, src, Format(base="B'tc''n"))
    base, quote = re.findall(r"WHERE mnemonic = (.*) LIMIT", result, re.MULTILINE)
    assert base == "'B''tc''''n'"


def test_format_insert_commented_out_if_no_values(out, series, src):
    empty_series = dataclasses.replace(series, prices=[])
    result = out.format(empty_series, src, Format())
    (
        "-- INSERT INTO new_prices (guid, date, base, quote, source, type, "
        "value_num, value_denom) VALUES\n"
        "-- \n"
        "-- ;\n"
    ) in result


def test_format_warns_about_backslash(out, series, src, caplog):
    with caplog.at_level(logging.WARNING):
        out.format(series, src, Format(quote="EU\\RO"))
    r = caplog.records[0]
    assert r.levelname == "WARNING"
    assert "backslashes in strings" in r.message


def test__english_join_other_cases(out):
    assert out._english_join([]) == ""
    assert out._english_join(["one"]) == "one"
    assert out._english_join(["one", "two"]) == "one and two"
    assert out._english_join(["one", "two", "three"]) == "one, two and three"


def test_format_warns_about_out_of_range_numbers(out, series, src, caplog):
    too_big_numerator = Decimal("9223372036854.775808")
    s = dataclasses.replace(series, prices=[Price("2021-01-01", too_big_numerator)])
    with caplog.at_level(logging.WARNING):
        out.format(s, src, Format())
    r = caplog.records[0]
    assert r.levelname == "WARNING"
    assert "outside of the int64 range" in r.message


def test__rational_other_exponent_cases(out):
    assert out._rational(Decimal("9223372036854e6")) == (
        "9223372036854000000",
        "1",
        True,
    )
    assert out._rational(Decimal("9223372036854e-6")) == (
        "9223372036854",
        "1000000",
        True,
    )
