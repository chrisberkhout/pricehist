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
from pricehist.sources.coindesk import CoinDesk


@pytest.fixture
def src():
    return CoinDesk()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def currencies_url():
    return "https://api.coindesk.com/v1/bpi/supported-currencies.json"


@pytest.fixture
def currencies_json():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "supported-currencies-partial.json").read_text()


@pytest.fixture
def currencies_response_ok(requests_mock, currencies_url, currencies_json):
    requests_mock.add(
        responses.GET,
        currencies_url,
        body=currencies_json,
        status=200,
    )
    yield requests_mock


@pytest.fixture
def recent_json():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "recent.json").read_text()


@pytest.fixture
def recent_response_ok(requests_mock, recent_json):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        body=recent_json,
        status=200,
    )
    yield requests_mock


@pytest.fixture
def all_json():
    dir = Path(os.path.splitext(__file__)[0])
    return (dir / "all-partial.json").read_text()


@pytest.fixture
def all_response_ok(requests_mock, all_json):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        body=all_json,
        status=200,
    )
    yield requests_mock


@pytest.fixture
def not_found_response(requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=404,
        body="Sorry, that currency was not found",
    )


def test_normalizesymbol(src):
    assert src.normalizesymbol("btc") == "BTC"
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


def test_symbols(src, currencies_response_ok):
    syms = src.symbols()
    assert ("BTC/AUD", "Bitcoin against Australian Dollar") in syms
    assert len(syms) > 3


def test_symbols_requests_logged(src, currencies_response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    assert any(
        ["DEBUG" == r.levelname and " curl " in r.message for r in caplog.records]
    )


def test_symbols_not_found(src, requests_mock, currencies_url):
    requests_mock.add(
        responses.GET,
        currencies_url,
        body="[]",
        status=200,
    )
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "data not found" in str(e.value)


def test_symbols_network_issue(src, requests_mock, currencies_url):
    requests_mock.add(
        responses.GET,
        currencies_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_bad_status(src, requests_mock, currencies_url):
    requests_mock.add(
        responses.GET,
        currencies_url,
        status=500,
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_parsing_error(src, requests_mock, currencies_url):
    requests_mock.add(
        responses.GET,
        currencies_url,
        body="NOT JSON",
    )
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "while parsing data" in str(e.value)


def test_fetch_known_pair(src, type, recent_response_ok):
    series = src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    req = recent_response_ok.calls[0].request
    assert req.params["currency"] == "AUD"
    assert req.params["start"] == "2021-01-01"
    assert req.params["end"] == "2021-01-07"
    assert series.prices[0] == Price("2021-01-01", Decimal("38204.8987"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("50862.227"))
    assert len(series.prices) == 7


def test_fetch_requests_logged(src, type, recent_response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert any(
        ["DEBUG" == r.levelname and " curl " in r.message for r in caplog.records]
    )


def test_fetch_long_hist_from_start(src, type, all_response_ok):
    series = src.fetch(Series("BTC", "AUD", type, src.start(), "2021-01-07"))
    assert series.prices[0] == Price("2010-07-18", Decimal("0.0984"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("50862.227"))
    assert len(series.prices) > 13


def test_fetch_from_before_start(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=404,
        body="Sorry, the CoinDesk BPI only covers data from 2010-07-17 onwards.",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2010-01-01", "2010-07-24"))
    assert "only covers data from" in str(e.value)


def test_fetch_to_future(src, type, all_response_ok):
    series = src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2100-01-01"))
    assert len(series.prices) > 0


def test_wrong_dates_order(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=404,
        body="Sorry, but your specified end date is before your start date.",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-07", "2021-01-01"))
    assert "End date is before start date." in str(e.value)


def test_fetch_in_future(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=404,
        body="Sorry, but your specified end date is before your start date.",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2030-01-01", "2030-01-07"))
    assert "start date must be in the past" in str(e.value)


def test_fetch_empty(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        body="{}",
    )
    series = src.fetch(Series("BTC", "AUD", type, "2010-07-17", "2010-07-17"))
    assert len(series.prices) == 0


def test_fetch_known_pair_no_data(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=500,
        body="No results returned from database",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "CUP", type, "2010-07-17", "2010-07-23"))
    assert "No results returned from database" in str(e.value)


def test_fetch_non_btc_base(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("USD", "AUD", type, "2021-01-01", "2021-01-07"))


def test_fetch_unknown_quote(src, type, not_found_response):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("BTC", "XZY", type, "2021-01-01", "2021-01-07"))


def test_fetch_no_quote(src, type, not_found_response):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("BTC", "", type, "2021-01-01", "2021-01-07"))


def test_fetch_unknown_pair(src, type):
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("ABC", "XZY", type, "2021-01-01", "2021-01-07"))


def test_fetch_network_issue(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        status=500,
        body="Some other reason",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, requests_mock):
    requests_mock.add(
        responses.GET,
        "https://api.coindesk.com/v1/bpi/historical/close.json",
        body="NOT JSON",
    )
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-01", "2021-01-07"))
    assert "while parsing data" in str(e.value)
