import logging
import os
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.yahoo import Yahoo


def timestamp(date):
    return int(
        datetime.strptime(date, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp()
    )


@pytest.fixture
def src():
    return Yahoo()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


def url(base):
    return f"https://query1.finance.yahoo.com/v8/finance/chart/{base}"


@pytest.fixture
def recent_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "tsla-recent.json").read_text()
    requests_mock.add(responses.GET, url("TSLA"), body=json, status=200)
    yield requests_mock


@pytest.fixture
def long_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "ibm-long-partial.json").read_text()
    requests_mock.add(responses.GET, url("IBM"), body=json, status=200)
    yield requests_mock


@pytest.fixture
def with_null_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "inrx-with-null.json").read_text()
    requests_mock.add(responses.GET, url("INR=X"), body=json, status=200)
    yield requests_mock


def test_normalizesymbol(src):
    assert src.normalizesymbol("tsla") == "TSLA"


def test_metadata(src):
    assert isinstance(src.id(), str)
    assert len(src.id()) > 0

    assert isinstance(src.name(), str)
    assert len(src.name()) > 0

    assert isinstance(src.description(), str)
    assert len(src.description()) > 0

    assert isinstance(src.source_url(), str)
    assert src.source_url().startswith("http")

    assert datetime.strptime(src.start(), "%Y-%m-%d")

    assert isinstance(src.types(), list)
    assert len(src.types()) > 0
    assert isinstance(src.types()[0], str)
    assert len(src.types()[0]) > 0

    assert isinstance(src.notes(), str)


def test_symbols(src, caplog):
    with caplog.at_level(logging.INFO):
        symbols = src.symbols()
    assert symbols == []
    assert any(["Find the symbol of interest on" in r.message for r in caplog.records])


def test_fetch_known(src, type, recent_ok):
    series = src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    req = recent_ok.calls[0].request
    assert req.params["events"] == "capitalGain%7Cdiv%7Csplit"
    assert req.params["includeAdjustedClose"] == "true"
    assert (series.base, series.quote) == ("TSLA", "USD")
    assert len(series.prices) == 5


def test_fetch_requests_and_receives_correct_times(src, type, recent_ok):
    series = src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    req = recent_ok.calls[0].request
    assert req.params["period1"] == str(timestamp("2021-01-04"))
    assert req.params["period2"] == str(timestamp("2021-01-09"))  # rounded up one
    assert req.params["interval"] == "1d"
    assert series.prices[0] == Price("2021-01-04", Decimal("243.2566680908203125"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("293.339996337890625"))


def test_fetch_ignores_any_extra_row(src, type, recent_ok):
    series = src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-07"))
    assert series.prices[0] == Price("2021-01-04", Decimal("243.2566680908203125"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("272.013336181640625"))


def test_fetch_requests_logged(src, type, recent_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    logged_requests = 0
    for r in caplog.records:
        if r.levelname == "DEBUG" and "curl " in r.message:
            logged_requests += 1
    assert logged_requests == 1


def test_fetch_types_all_available(src, recent_ok):
    adj = src.fetch(Series("TSLA", "", "adjclose", "2021-01-04", "2021-01-08"))
    opn = src.fetch(Series("TSLA", "", "open", "2021-01-04", "2021-01-08"))
    hgh = src.fetch(Series("TSLA", "", "high", "2021-01-04", "2021-01-08"))
    low = src.fetch(Series("TSLA", "", "low", "2021-01-04", "2021-01-08"))
    cls = src.fetch(Series("TSLA", "", "close", "2021-01-04", "2021-01-08"))
    mid = src.fetch(Series("TSLA", "", "mid", "2021-01-04", "2021-01-08"))
    assert adj.prices[0].amount == Decimal("243.2566680908203125")
    assert opn.prices[0].amount == Decimal("239.82000732421875")
    assert hgh.prices[0].amount == Decimal("248.163330078125")
    assert low.prices[0].amount == Decimal("239.0633392333984375")
    assert cls.prices[0].amount == Decimal("243.2566680908203125")
    assert mid.prices[0].amount == Decimal("243.61333465576171875")


def test_fetch_type_mid_is_mean_of_low_and_high(src, recent_ok):
    mid = src.fetch(Series("TSLA", "", "mid", "2021-01-04", "2021-01-08")).prices
    hgh = src.fetch(Series("TSLA", "", "high", "2021-01-04", "2021-01-08")).prices
    low = src.fetch(Series("TSLA", "", "low", "2021-01-04", "2021-01-08")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 5)
        ]
    )


def test_fetch_from_before_start(src, type, long_ok):
    series = src.fetch(Series("IBM", "", type, "1900-01-01", "2021-01-08"))
    assert series.prices[0] == Price("1962-01-02", Decimal("1.5133211612701416015625"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("103.2923736572265625"))
    assert len(series.prices) > 9


def test_fetch_skips_dates_with_nulls(src, type, with_null_ok):
    series = src.fetch(Series("INR=X", "", type, "2017-07-10", "2017-07-12"))
    assert series.prices[0] == Price("2017-07-10", Decimal("64.61170196533203125"))
    assert series.prices[1] == Price("2017-07-12", Decimal("64.52559661865234375"))
    assert len(series.prices) == 2


def test_fetch_to_future(src, type, recent_ok):
    series = src.fetch(Series("TSLA", "", type, "2021-01-04", "2100-01-08"))
    assert len(series.prices) > 0


def test_fetch_no_data_in_past(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        url("TSLA"),
        status=400,
        body=(
            "400 Bad Request: Data doesn't exist for "
            "startDate = 1262304000, endDate = 1262995200"
        ),
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("TSLA", "", type, "2010-01-04", "2010-01-08"))
    assert "No data for the given interval" in str(e.value)


def test_fetch_no_data_in_future(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        url("TSLA"),
        status=400,
        body=(
            "400 Bad Request: Data doesn't exist for "
            "startDate = 1893715200, endDate = 1894147200"
        ),
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("TSLA", "", type, "2030-01-04", "2030-01-08"))
    assert "No data for the given interval" in str(e.value)


def test_fetch_no_data_on_weekend(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        url("TSLA"),
        status=404,
        body="404 Not Found: Timestamp data missing.",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("TSLA", "", type, "2021-01-09", "2021-01-10"))
    assert "may be for a gap in the data" in str(e.value)


def test_fetch_bad_sym(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        url("NOTABASE"),
        status=404,
        body="404 Not Found: No data found, symbol may be delisted",
    )
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("NOTABASE", "", type, "2021-01-04", "2021-01-08"))
    assert "Symbol not found" in str(e.value)


def test_fetch_giving_quote(src, type):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("TSLA", "USD", type, "2021-01-04", "2021-01-08"))
    assert "quote currency" in str(e.value)


def test_fetch_network_issue(src, type, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, url("TSLA"), body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock):
    requests_mock.add(responses.GET, url("TSLA"), status=500, body="Some other reason")
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, requests_mock):
    requests_mock.add(responses.GET, url("TSLA"), body="")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("TSLA", "", type, "2021-01-04", "2021-01-08"))
    assert "error occurred while parsing data from the source" in str(e.value)
