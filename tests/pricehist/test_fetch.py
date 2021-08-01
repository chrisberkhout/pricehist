import logging
from datetime import date, timedelta
from decimal import Decimal

import pytest

from pricehist import exceptions
from pricehist.fetch import fetch
from pricehist.format import Format
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.basesource import BaseSource


@pytest.fixture
def res_series(mocker):
    series = mocker.MagicMock()
    series.start = "2021-01-01"
    series.end = "2021-01-03"
    return series


@pytest.fixture
def source(res_series, mocker):
    source = mocker.MagicMock(BaseSource)
    source.start = mocker.MagicMock(return_value="2021-01-01")
    source.fetch = mocker.MagicMock(return_value=res_series)
    return source


@pytest.fixture
def output(mocker):
    output = mocker.MagicMock()
    output.format = mocker.MagicMock(return_value="")
    return output


@pytest.fixture
def fmt(mocker):
    return Format()


def test_fetch_warns_if_start_before_source_start(source, output, fmt, mocker, caplog):
    req_series = Series("BTC", "EUR", "close", "2020-12-31", "2021-01-03")
    source.start = mocker.MagicMock(return_value="2021-01-01")
    with caplog.at_level(logging.INFO):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    assert any(
        [
            "WARNING" == r.levelname and "start date 2020-12-31 preceeds" in r.message
            for r in caplog.records
        ]
    )


def test_fetch_returns_formatted_output(source, res_series, output, fmt, mocker):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    output.format = mocker.MagicMock(return_value="rendered output")

    result = fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)

    output.format.assert_called_once_with(res_series, source, fmt=fmt)
    assert result == "rendered output"


def test_fetch_inverts_if_requested(source, res_series, output, fmt, mocker):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    inv_series = mocker.MagicMock(res_series)
    res_series.invert = mocker.MagicMock(return_value=inv_series)

    fetch(req_series, source, output, invert=True, quantize=None, fmt=fmt)

    res_series.invert.assert_called_once_with()
    output.format.assert_called_once_with(inv_series, source, fmt=fmt)


def test_fetch_quantizes_if_requested(source, res_series, output, fmt, mocker):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    qnt_series = mocker.MagicMock(res_series)
    res_series.quantize = mocker.MagicMock(return_value=qnt_series)

    fetch(req_series, source, output, invert=False, quantize=2, fmt=fmt)

    res_series.quantize.assert_called_once_with(2)
    output.format.assert_called_once_with(qnt_series, source, fmt=fmt)


def test_fetch_warns_if_no_data(source, res_series, output, fmt, mocker, caplog):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    res_series.prices = mocker.MagicMock(return_value=[])
    with caplog.at_level(logging.INFO):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    assert any(
        [
            "WARNING" == r.levelname and "No data found" in r.message
            for r in caplog.records
        ]
    )


def test_fetch_warns_if_missing_data_at_start(source, res_series, output, fmt, caplog):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    res_series.prices = [
        Price("2021-01-02", Decimal("1.2")),
        Price("2021-01-03", Decimal("1.3")),
    ]
    with caplog.at_level(logging.INFO):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    r = caplog.records[0]
    assert r.levelname == "WARNING"
    assert r.message == (
        "Available data covers the interval [2021-01-02--2021-01-03], "
        "which starts 1 day later than requested."
    )


def test_fetch_warns_if_missing_data_at_end(source, res_series, output, fmt, caplog):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    res_series.prices = [Price("2021-01-01", Decimal("1.1"))]
    with caplog.at_level(logging.INFO):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    r = caplog.records[0]
    assert r.levelname == "WARNING"
    assert r.message == (
        "Available data covers the interval [2021-01-01--2021-01-01], "
        "which ends 2 days earlier than requested."
    )


def test_fetch_warns_if_missing_data_at_both_ends(
    source, res_series, output, fmt, caplog
):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    res_series.prices = [Price("2021-01-02", Decimal("1.2"))]
    with caplog.at_level(logging.INFO):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    r = caplog.records[0]
    assert r.levelname == "WARNING"
    assert r.message == (
        "Available data covers the interval [2021-01-02--2021-01-02], "
        "which starts 1 day later and ends 1 day earlier than requested."
    )


def test_fetch_debug_not_warning_message_if_only_today_missing(
    source, res_series, output, fmt, caplog
):
    start = (date.today() - timedelta(days=2)).isoformat()
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    today = date.today().isoformat()
    req_series = Series("BTC", "EUR", "close", start, today)
    res_series.start = start
    res_series.end = today
    res_series.prices = [Price(start, Decimal("1.1")), Price(yesterday, Decimal("1.2"))]
    with caplog.at_level(logging.DEBUG):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    r = caplog.records[0]
    assert r.levelname == "DEBUG"
    assert r.message == (
        f"Available data covers the interval [{start}--{yesterday}], "
        "which ends 1 day earlier than requested."
    )


def test_fetch_debug_not_warning_message_if_as_requested(
    source, res_series, output, fmt, caplog
):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")
    res_series.prices = [
        Price("2021-01-01", Decimal("1.1")),
        Price("2021-01-02", Decimal("1.2")),
        Price("2021-01-03", Decimal("1.3")),
    ]
    with caplog.at_level(logging.DEBUG):
        fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)
    r = caplog.records[0]
    assert r.levelname == "DEBUG"
    assert r.message == (
        "Available data covers the interval [2021-01-01--2021-01-03], as requested."
    )


def test_fetch_handles_source_exceptions(source, output, fmt, mocker, caplog):
    req_series = Series("BTC", "EUR", "close", "2021-01-01", "2021-01-03")

    def side_effect(_):
        raise exceptions.RequestError("something strange")

    source.fetch = mocker.MagicMock(side_effect=side_effect)

    with caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as e:
            fetch(req_series, source, output, invert=False, quantize=None, fmt=fmt)

    r = caplog.records[0]
    assert r.levelname == "CRITICAL"
    assert "something strange" in r.message

    assert e.value.code == 1
