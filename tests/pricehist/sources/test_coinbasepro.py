import logging
import os
import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.coinbasepro import CoinbasePro


@pytest.fixture
def src():
    return CoinbasePro()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


@pytest.fixture
def products_url():
    return "https://api.pro.coinbase.com/products"


@pytest.fixture
def currencies_url():
    return "https://api.pro.coinbase.com/currencies"


def product_url(base, quote):
    return f"https://api.pro.coinbase.com/products/{base}-{quote}/candles"


@pytest.fixture
def products_json():
    return (Path(os.path.splitext(__file__)[0]) / "products-partial.json").read_text()


@pytest.fixture
def currencies_json():
    return (Path(os.path.splitext(__file__)[0]) / "currencies-partial.json").read_text()


@pytest.fixture
def products_response_ok(requests_mock, products_url, products_json):
    requests_mock.add(responses.GET, products_url, body=products_json, status=200)
    yield requests_mock


@pytest.fixture
def currencies_response_ok(requests_mock, currencies_url, currencies_json):
    requests_mock.add(responses.GET, currencies_url, body=currencies_json, status=200)
    yield requests_mock


@pytest.fixture
def recent_response_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "recent.json").read_text()
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), body=json, status=200)
    yield requests_mock


@pytest.fixture
def multi_response_ok(requests_mock):
    url1 = re.compile(
        r"https://api\.pro\.coinbase\.com/products/BTC-EUR/candles\?start=2020-01-01.*"
    )
    url2 = re.compile(
        r"https://api\.pro\.coinbase\.com/products/BTC-EUR/candles\?start=2020-10-17.*"
    )
    json1 = (
        Path(os.path.splitext(__file__)[0]) / "2020-01-01--2020-10-16.json"
    ).read_text()
    json2 = (
        Path(os.path.splitext(__file__)[0]) / "2020-10-17--2021-01-07.json"
    ).read_text()
    requests_mock.add(responses.GET, url1, body=json1, status=200)
    requests_mock.add(responses.GET, url2, body=json2, status=200)
    yield requests_mock


@pytest.fixture
def response_empty(requests_mock):
    requests_mock.add(
        responses.GET,
        product_url("BTC", "EUR"),
        status=200,
        body="[]",
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


def test_symbols(src, products_response_ok, currencies_response_ok):
    syms = src.symbols()
    assert ("BTC/EUR", "Bitcoin against Euro") in syms
    assert len(syms) > 2


def test_symbols_requests_logged(
    src, products_response_ok, currencies_response_ok, caplog
):
    with caplog.at_level(logging.DEBUG):
        src.symbols()
    matching = filter(
        lambda r: "DEBUG" == r.levelname and "curl " in r.message,
        caplog.records,
    )
    assert len(list(matching)) == 2


def test_symbols_not_found(src, requests_mock, products_url, currencies_response_ok):
    requests_mock.add(responses.GET, products_url, body="[]", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "data not found" in str(e.value)


def test_symbols_network_issue(
    src, requests_mock, products_response_ok, currencies_url
):
    requests_mock.add(
        responses.GET,
        currencies_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_bad_status(src, requests_mock, products_url, currencies_response_ok):
    requests_mock.add(responses.GET, products_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_parsing_error(
    src, requests_mock, products_response_ok, currencies_url
):
    requests_mock.add(responses.GET, currencies_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "while parsing data" in str(e.value)


def test_fetch_known_pair(src, type, recent_response_ok):
    series = src.fetch(Series("BTC", "EUR", type, "2021-01-01", "2021-01-07"))
    req = recent_response_ok.calls[0].request
    assert req.params["granularity"] == "86400"
    assert req.params["start"] == "2021-01-01"
    assert req.params["end"] == "2021-01-07"
    assert series.prices[0] == Price("2021-01-01", Decimal("23881.35"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("31208.49"))
    assert len(series.prices) == 7


def test_fetch_types_all_available(src, recent_response_ok):
    mid = src.fetch(Series("BTC", "EUR", "mid", "2021-01-01", "2021-01-07"))
    opn = src.fetch(Series("BTC", "EUR", "open", "2021-01-01", "2021-01-07"))
    hgh = src.fetch(Series("BTC", "EUR", "high", "2021-01-01", "2021-01-07"))
    low = src.fetch(Series("BTC", "EUR", "low", "2021-01-01", "2021-01-07"))
    cls = src.fetch(Series("BTC", "EUR", "close", "2021-01-01", "2021-01-07"))
    assert mid.prices[0].amount == Decimal("23881.35")
    assert opn.prices[0].amount == Decimal("23706.73")
    assert hgh.prices[0].amount == Decimal("24250")
    assert low.prices[0].amount == Decimal("23512.7")
    assert cls.prices[0].amount == Decimal("24070.97")


def test_fetch_type_mid_is_mean_of_low_and_high(src, recent_response_ok):
    mid = src.fetch(Series("BTC", "EUR", "mid", "2021-01-01", "2021-01-07")).prices
    low = src.fetch(Series("BTC", "EUR", "low", "2021-01-01", "2021-01-07")).prices
    hgh = src.fetch(Series("BTC", "EUR", "high", "2021-01-01", "2021-01-07")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 7)
        ]
    )


def test_fetch_requests_logged(src, type, recent_response_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("BTC", "EUR", type, "2021-01-01", "2021-01-07"))
    assert any(
        ["DEBUG" == r.levelname and "curl " in r.message for r in caplog.records]
    )


def test_fetch_long_hist_multi_segment(src, type, multi_response_ok):
    series = src.fetch(Series("BTC", "EUR", type, "2020-01-01", "2021-01-07"))
    assert series.prices[0] == Price("2020-01-01", Decimal("6430.175"))
    assert series.prices[-1] == Price("2021-01-07", Decimal("31208.49"))
    assert len(series.prices) > 3


def test_fetch_from_before_start(src, type, requests_mock):
    body = '{"message":"End is too old"}'
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), status=400, body=body)
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "EUR", type, "1960-01-01", "1960-01-07"))
    assert "too early" in str(e.value)


def test_fetch_in_future(src, type, response_empty):
    series = src.fetch(Series("BTC", "EUR", type, "2100-01-01", "2100-01-07"))
    assert len(series.prices) == 0


def test_fetch_wrong_dates_order_alledged(src, type, requests_mock):
    # Is actually prevented in argument parsing and inside the source.
    body = '{"message":"start must be before end"}'
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), status=400, body=body)
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-07", "2021-01-01"))
    assert "end can't preceed" in str(e.value)


def test_fetch_too_many_data_points_alledged(src, type, requests_mock):
    # Should only happen if limit is reduced or calculated segments lengthened
    body = "aggregations requested exceeds"
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), status=400, body=body)
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-07", "2021-01-01"))
    assert "Too many data points" in str(e.value)


def test_fetch_rate_limit(src, type, requests_mock):
    body = "Too many requests"
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), status=429, body=body)
    with pytest.raises(exceptions.RateLimit) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-07", "2021-01-01"))
    assert "rate limit has been exceeded" in str(e.value)


def test_fetch_empty(src, type, response_empty):
    series = src.fetch(Series("BTC", "EUR", type, "2000-01-01", "2000-01-07"))
    assert len(series.prices) == 0


def test_fetch_unknown_base(src, type, requests_mock):
    body = '{"message":"NotFound"}'
    requests_mock.add(
        responses.GET, product_url("UNKNOWN", "EUR"), status=404, body=body
    )
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("UNKNOWN", "EUR", type, "2021-01-01", "2021-01-07"))


def test_fetch_unknown_quote(src, type, requests_mock):
    body = '{"message":"NotFound"}'
    requests_mock.add(responses.GET, product_url("BTC", "XZY"), status=404, body=body)
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("BTC", "XZY", type, "2021-01-01", "2021-01-07"))


def test_fetch_no_quote(src, type, requests_mock):
    body = '{"message":"NotFound"}'
    requests_mock.add(responses.GET, product_url("BTC", ""), status=404, body=body)
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("BTC", "", type, "2021-01-01", "2021-01-07"))


def test_fetch_unknown_pair(src, type, requests_mock):
    body = '{"message":"NotFound"}'
    requests_mock.add(responses.GET, product_url("ABC", "XZY"), status=404, body=body)
    with pytest.raises(exceptions.InvalidPair):
        src.fetch(Series("ABC", "XZY", type, "2021-01-01", "2021-01-07"))


def test_fetch_network_issue(src, type, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-01", "2021-01-07"))
    assert "Network issue" in str(e.value)


def test_fetch_bad_status(src, type, requests_mock):
    requests_mock.add(
        responses.GET, product_url("BTC", "EUR"), status=500, body="Some other reason"
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-01", "2021-01-07"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_parsing_error(src, type, requests_mock):
    requests_mock.add(responses.GET, product_url("BTC", "EUR"), body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "EUR", type, "2021-01-01", "2021-01-07"))
    assert "while parsing data" in str(e.value)
