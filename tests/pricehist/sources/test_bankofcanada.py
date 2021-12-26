import logging
import os
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.bankofcanada import BankOfCanada


@pytest.fixture
def src():
    return BankOfCanada()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def series_list_url():
    return "https://www.bankofcanada.ca/valet/lists/series/json"


def fetch_url(series_name):
    return f"https://www.bankofcanada.ca/valet/observations/{series_name}/json"


@pytest.fixture
def series_list_json():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "series-partial.json").read_text()


@pytest.fixture
def series_list_response_ok(requests_mock, series_list_url, series_list_json):
    requests_mock.add(responses.GET, series_list_url, body=series_list_json, status=200)
    yield requests_mock


@pytest.fixture
def recent_response_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "recent.json").read_text()
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), body=json, status=200)
    yield requests_mock


@pytest.fixture
def all_response_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "all-partial.json").read_text()
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), body=json, status=200)
    yield requests_mock


def test_normalizesymbol(src):
    assert src.normalizesymbol("cad") == "CAD"
    assert src.normalizesymbol("usd") == "USD"


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


def test_symbols(src, series_list_response_ok):
    syms = src.symbols()
    assert ("CAD/USD", "Canadian dollar to US dollar daily exchange rate") in syms
    assert len(syms) > 3


def test_symbols_requests_logged(src, series_list_response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    assert any(
        ["DEBUG" == r.levelname and "curl " in r.message for r in caplog.records]
    )


def test_symbols_not_found(src, requests_mock, series_list_url):
    requests_mock.add(responses.GET, series_list_url, body='{"series":{}}', status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "data not found" in str(e.value)


def test_symbols_network_issue(src, requests_mock, series_list_url):
    requests_mock.add(
        responses.GET,
        series_list_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_bad_status(src, requests_mock, series_list_url):
    requests_mock.add(responses.GET, series_list_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_parsing_error(src, requests_mock, series_list_url):
    requests_mock.add(responses.GET, series_list_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "while parsing data" in str(e.value)


def test_fetch_known_pair(src, type, recent_response_ok):
    series = src.fetch(Series("CAD", "USD", type, "2021-01-01", "2021-01-07"))
    req = recent_response_ok.calls[0].request
    assert req.params["order_dir"] == "asc"
    assert req.params["start_date"] == "2021-01-01"
    assert req.params["end_date"] == "2021-01-07"
    assert series.prices[0] == Price("2021-01-04", Decimal("0.7843"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("0.7870"))
    assert len(series.prices) == 4


def test_fetch_requests_logged(src, type, recent_response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("CAD", "USD", type, "2021-01-01", "2021-01-07"))
    assert any(
        ["DEBUG" == r.levelname and "curl " in r.message for r in caplog.records]
    )


def test_fetch_long_hist_from_start(src, type, all_response_ok):
    series = src.fetch(Series("CAD", "USD", type, src.start(), "2021-01-07"))
    assert series.prices[0] == Price("2017-01-03", Decimal("0.7443"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("0.7870"))
    assert len(series.prices) > 13


def test_fetch_from_before_start(src, type, requests_mock):
    body = """{ "observations": [] }"""
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), status=200, body=body)
    series = src.fetch(Series("CAD", "USD", type, "2000-01-01", "2017-01-01"))
    assert len(series.prices) == 0


def test_fetch_to_future(src, type, all_response_ok):
    series = src.fetch(Series("CAD", "USD", type, "2021-01-01", "2100-01-01"))
    assert len(series.prices) > 0


def test_wrong_dates_order(src, type, requests_mock):
    body = """{ "message": "The End date must be greater than the Start date." }"""
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), status=400, body=body)
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("CAD", "USD", type, "2021-01-07", "2021-01-01"))
    assert "End date must be greater" in str(e.value)


def test_fetch_in_future(src, type, requests_mock):
    body = """{ "observations": [] }"""
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), status=200, body=body)
    series = src.fetch(Series("CAD", "USD", type, "2030-01-01", "2030-01-07"))
    assert len(series.prices) == 0


def test_fetch_empty(src, type, requests_mock):
    requests_mock.add(
        responses.GET, fetch_url("FXCADUSD"), body="""{"observations":{}}"""
    )
    series = src.fetch(Series("CAD", "USD", type, "2021-01-03", "2021-01-03"))
    assert len(series.prices) == 0


def test_fetch_no_quote(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("CAD", "", type, "2021-01-01", "2021-01-07"))


def test_fetch_unknown_pair(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        fetch_url("FXCADAFN"),
        status=404,
        body="""{
            "message": "Series FXCADAFN not found.",
            "docs": "https://www.bankofcanada.ca/valet/docs"
        }""",
    )
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("CAD", "AFN", type, "2021-01-01", "2021-01-07"))


def test_fetch_network_issue(src, type, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("CAD", "USD", type, "2021-01-01", "2021-01-07"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        fetch_url("FXCADUSD"),
        status=500,
        body="""{"message": "Some other reason"}""",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("CAD", "USD", type, "2021-01-01", "2021-01-07"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, requests_mock):
    requests_mock.add(responses.GET, fetch_url("FXCADUSD"), body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("CAD", "USD", type, "2021-01-01", "2021-01-07"))
    assert "while parsing data" in str(e.value)
