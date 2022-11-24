import logging
import os
import re
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path

import pytest
import requests
import responses

from pricehist import __version__, exceptions
from pricehist.price import Price
from pricehist.series import Series
from pricehist.sources.alphavantage import AlphaVantage

api_key_name = "ALPHAVANTAGE_API_KEY"


@pytest.fixture(autouse=True)
def mock_settings_env_vars(monkeypatch):
    value = "NOTAREALKEY12345"
    if not os.getenv(api_key_name):
        monkeypatch.setenv(api_key_name, value, prepend=False)
    yield


@pytest.fixture
def src():
    return AlphaVantage()


@pytest.fixture
def type(src):
    return src.types()[0]


@pytest.fixture
def requests_mock():
    with responses.RequestsMock() as mock:
        yield mock


physical_list_url = "https://www.alphavantage.co/physical_currency_list/"
digital_list_url = "https://www.alphavantage.co/digital_currency_list/"

search_url = re.compile(
    r"https://www\.alphavantage\.co/query\?function=SYMBOL_SEARCH.*"
)
stock_url = re.compile(
    r"https://www\.alphavantage\.co/query\?function=TIME_SERIES_DAILY_ADJUSTED.*"
)
physical_url = re.compile(r"https://www\.alphavantage\.co/query\?function=FX_DAILY.*")
digital_url = re.compile(
    r"https://www\.alphavantage\.co/query\?function=DIGITAL_CURRENCY_DAILY.*"
)

rate_limit_json = (
    '{ "Note": "'
    "Thank you for using Alpha Vantage! Our standard API call frequency is 5 "
    "calls per minute and 500 calls per day. Please visit "
    "https://www.alphavantage.co/premium/ if you would like to target a higher "
    "API call frequency."
    '" }'
)

premium_json = (
    '{ "Information": "Thank you for using Alpha Vantage! This is a premium '
    "endpoint. You may subscribe to any of the premium plans at "
    "https://www.alphavantage.co/premium/ to instantly unlock all premium "
    'endpoints" }'
)


@pytest.fixture
def physical_list_ok(requests_mock):
    text = (Path(os.path.splitext(__file__)[0]) / "physical-partial.csv").read_text()
    requests_mock.add(responses.GET, physical_list_url, body=text, status=200)
    yield requests_mock


@pytest.fixture
def digital_list_ok(requests_mock):
    text = (Path(os.path.splitext(__file__)[0]) / "digital-partial.csv").read_text()
    requests_mock.add(responses.GET, digital_list_url, body=text, status=200)
    yield requests_mock


@pytest.fixture
def search_ok(requests_mock):
    text = (Path(os.path.splitext(__file__)[0]) / "search-ibm.json").read_text()
    requests_mock.add(responses.GET, search_url, body=text, status=200)
    yield requests_mock


@pytest.fixture
def search_not_found(requests_mock):
    requests_mock.add(responses.GET, search_url, body='{"bestMatches":[]}', status=200)
    yield requests_mock


@pytest.fixture
def ibm_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "ibm-partial.json").read_text()
    requests_mock.add(responses.GET, stock_url, body=json, status=200)
    yield requests_mock


@pytest.fixture
def ibm_adj_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "ibm-partial-adj.json").read_text()
    requests_mock.add(responses.GET, stock_url, body=json, status=200)
    yield requests_mock


@pytest.fixture
def euraud_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "eur-aud-partial.json").read_text()
    requests_mock.add(responses.GET, physical_url, body=json, status=200)
    yield requests_mock


@pytest.fixture
def btcaud_ok(requests_mock):
    json = (Path(os.path.splitext(__file__)[0]) / "btc-aud-partial.json").read_text()
    requests_mock.add(responses.GET, digital_url, body=json, status=200)
    yield requests_mock


def test_normalizesymbol(src):
    assert src.normalizesymbol("tsla") == "TSLA"
    assert src.normalizesymbol("btc") == "BTC"
    assert src.normalizesymbol("eur") == "EUR"


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


def test_symbols_stock_message(src, physical_list_ok, digital_list_ok, caplog):
    with caplog.at_level(logging.INFO):
        src.symbols()
    assert any(["Stock symbols can be discovered" in r.message for r in caplog.records])


def test_symbols(src, physical_list_ok, digital_list_ok):
    syms = src.symbols()
    assert ("BTC", "Digital: Bitcoin") in syms
    assert ("AUD", "Physical: Australian Dollar") in syms
    assert len(syms) > 2


def test_symbols_digital_network_issue(src, requests_mock):
    requests_mock.add(
        responses.GET,
        digital_list_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_digital_bad_status(src, requests_mock):
    requests_mock.add(responses.GET, digital_list_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_digital_no_data(src, requests_mock):
    requests_mock.add(responses.GET, digital_list_url, body="NOT CSV", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "Symbols data missing." in str(e.value)


def test_symbols_digital_bad_data(src, requests_mock):
    requests_mock.add(responses.GET, digital_list_url, body="A,B,C\na,b,c", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "too many values" in str(e.value)


def test_symbols_physical_network_issue(src, digital_list_ok, requests_mock):
    requests_mock.add(
        responses.GET,
        physical_list_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.symbols()
    assert "Network issue" in str(e.value)


def test_symbols_physical_bad_status(src, digital_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_list_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.symbols()
    assert "Server Error" in str(e.value)


def test_symbols_physical_no_data(src, digital_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_list_url, body="", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.symbols()
    assert "Symbols data missing." in str(e.value)


def test_search(src, search_ok):
    results = src.search("IBM")
    req = search_ok.calls[0].request
    assert req.params["function"] == "SYMBOL_SEARCH"
    assert req.params["keywords"] == "IBM"
    assert len(req.params["apikey"]) > 0
    assert len(results) == 10
    for expected in [
        ("IBM", "International Business Machines Corp, Equity, United States, USD"),
        ("IBMJ", "iShares iBonds Dec 2021 Term Muni Bond ETF, ETF, United States, USD"),
        ("IBMK", "iShares iBonds Dec 2022 Term Muni Bond ETF, ETF, United States, USD"),
        ("IBM.DEX", "International Business Machines Corporation, Equity, XETRA, EUR"),
    ]:
        assert expected in results


def test_search_network_issue(src, requests_mock):
    requests_mock.add(
        responses.GET,
        search_url,
        body=requests.exceptions.ConnectionError("Network issue"),
    )
    with pytest.raises(exceptions.RequestError) as e:
        src.search("IBM")
    assert "Network issue" in str(e.value)


def test_search_bad_status(src, requests_mock):
    requests_mock.add(responses.GET, search_url, status=500)
    with pytest.raises(exceptions.BadResponse) as e:
        src.search("IBM")
    assert "Server Error" in str(e.value)


def test_search_bad_data(src, requests_mock):
    requests_mock.add(responses.GET, search_url, body="NOT JSON", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.search("IBM")
    assert "while parsing data" in str(e.value)


def test_search_bad_json(src, requests_mock):
    requests_mock.add(responses.GET, search_url, body="{}", status=200)
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.search("IBM")
    assert "Unexpected content." in str(e.value)


def test_search_bad_json_tricky(src, requests_mock):
    requests_mock.add(
        responses.GET, search_url, body='{"bestMatches": [{}]}', status=200
    )
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.search("IBM")
    assert "Unexpected content." in str(e.value)


def test_search_rate_limit(src, type, requests_mock):
    requests_mock.add(responses.GET, search_url, body=rate_limit_json)
    with pytest.raises(exceptions.RateLimit) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "rate limit" in str(e.value)


def test_fetch_stock_known(src, type, search_ok, ibm_ok):
    series = src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    search_req = search_ok.calls[0].request
    stock_req = ibm_ok.calls[1].request
    assert search_req.params["function"] == "SYMBOL_SEARCH"
    assert search_req.params["keywords"] == "IBM"
    assert stock_req.params["function"] == "TIME_SERIES_DAILY_ADJUSTED"
    assert stock_req.params["symbol"] == "IBM"
    assert stock_req.params["outputsize"] == "full"
    assert (series.base, series.quote) == ("IBM", "USD")
    assert len(series.prices) == 5
    assert series.prices[0] == Price("2021-01-04", Decimal("123.94"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("128.53"))


def test_fetch_stock_compact_if_recent(src, type, search_ok, ibm_ok):
    today = datetime.now().date()
    start = (today - timedelta(days=30)).isoformat()
    end = today.isoformat()
    src.fetch(Series("IBM", "", type, start, end))
    stock_req = ibm_ok.calls[1].request
    assert stock_req.params["outputsize"] == "compact"


def test_fetch_stock_requests_logged(src, type, search_ok, ibm_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    logged_requests = 0
    for r in caplog.records:
        if r.levelname == "DEBUG" and "curl " in r.message:
            logged_requests += 1
    assert logged_requests == 2


def test_fetch_stock_types_all_available(src, search_ok, ibm_ok):
    cls = src.fetch(Series("IBM", "", "close", "2021-01-04", "2021-01-08"))
    opn = src.fetch(Series("IBM", "", "open", "2021-01-04", "2021-01-08"))
    hgh = src.fetch(Series("IBM", "", "high", "2021-01-04", "2021-01-08"))
    low = src.fetch(Series("IBM", "", "low", "2021-01-04", "2021-01-08"))
    mid = src.fetch(Series("IBM", "", "mid", "2021-01-04", "2021-01-08"))
    assert cls.prices[0].amount == Decimal("123.94")
    assert opn.prices[0].amount == Decimal("125.85")
    assert hgh.prices[0].amount == Decimal("125.9174")
    assert low.prices[0].amount == Decimal("123.04")
    assert mid.prices[0].amount == Decimal("124.4787")


def test_fetch_stock_types_adj_available(src, search_ok, ibm_adj_ok):
    adj = src.fetch(Series("IBM", "", "adjclose", "2021-01-04", "2021-01-08"))
    assert adj.prices[0].amount == Decimal("120.943645029")


def test_fetch_stock_type_mid_is_mean_of_low_and_high(src, search_ok, ibm_ok):
    hgh = src.fetch(Series("IBM", "", "high", "2021-01-04", "2021-01-08")).prices
    low = src.fetch(Series("IBM", "", "low", "2021-01-04", "2021-01-08")).prices
    mid = src.fetch(Series("IBM", "", "mid", "2021-01-04", "2021-01-08")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 5)
        ]
    )


def test_fetch_stock_bad_sym(src, type, search_not_found, requests_mock):
    requests_mock.add(
        responses.GET,
        stock_url,
        status=200,
        body="""{
            "Error Message": "Invalid API call. Please retry or..."
        }""",
    )
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("NOTASTOCK", "", type, "2021-01-04", "2021-01-08"))
    assert "Unknown stock symbol" in str(e.value)


def test_fetch_stock_quote_found_prices_error(src, type, search_ok, requests_mock):
    requests_mock.add(
        responses.GET,
        stock_url,
        status=200,
        body="""{
            "Error Message": "Invalid API call. Please retry or..."
        }""",
    )
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "bad response" in str(e.value)


def test_fetch_stock_network_issue(src, type, search_ok, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, stock_url, body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "Network issue" in str(e.value)


def test_fetch_stock_bad_status(src, type, search_ok, requests_mock):
    requests_mock.add(responses.GET, stock_url, status=500, body="Some other reason")
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_stock_parsing_error(src, type, search_ok, requests_mock):
    requests_mock.add(responses.GET, stock_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "while parsing data" in str(e.value)


def test_fetch_stock_unexpected_json(src, type, search_ok, requests_mock):
    requests_mock.add(responses.GET, stock_url, body='{"notdata": []}')
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "Unexpected content" in str(e.value)


def test_fetch_stock_rate_limit(src, type, search_ok, requests_mock):
    requests_mock.add(responses.GET, stock_url, body=rate_limit_json)
    with pytest.raises(exceptions.RateLimit) as e:
        src.fetch(Series("IBM", "", type, "2021-01-04", "2021-01-08"))
    assert "rate limit" in str(e.value)


def test_fetch_stock_premium(src, search_ok, requests_mock):
    requests_mock.add(responses.GET, stock_url, body=premium_json)
    with pytest.raises(exceptions.CredentialsError) as e:
        src.fetch(Series("IBM", "", "adjclose", "2021-01-04", "2021-01-08"))
    assert "denied access to a premium endpoint" in str(e.value)


def test_fetch_physical_known(src, type, physical_list_ok, euraud_ok):
    series = src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    req = euraud_ok.calls[1].request
    assert req.params["function"] == "FX_DAILY"
    assert req.params["from_symbol"] == "EUR"
    assert req.params["to_symbol"] == "AUD"
    assert req.params["outputsize"] == "full"
    assert (series.base, series.quote) == ("EUR", "AUD")
    assert len(series.prices) == 5
    assert series.prices[0] == Price("2021-01-04", Decimal("1.59718"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("1.57350"))


def test_fetch_physical_compact_if_recent(src, type, physical_list_ok, euraud_ok):
    today = datetime.now().date()
    start = (today - timedelta(days=30)).isoformat()
    end = today.isoformat()
    src.fetch(Series("EUR", "AUD", type, start, end))
    req = euraud_ok.calls[1].request
    assert req.params["outputsize"] == "compact"


def test_fetch_physical_requests_logged(src, type, physical_list_ok, euraud_ok, caplog):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    logged_requests = 0
    for r in caplog.records:
        if r.levelname == "DEBUG" and "curl " in r.message:
            logged_requests += 1
    assert logged_requests == 2


def test_fetch_physical_types_but_adjclose_available(src, physical_list_ok, euraud_ok):
    cls = src.fetch(Series("EUR", "AUD", "close", "2021-01-04", "2021-01-08"))
    opn = src.fetch(Series("EUR", "AUD", "open", "2021-01-04", "2021-01-08"))
    hgh = src.fetch(Series("EUR", "AUD", "high", "2021-01-04", "2021-01-08"))
    low = src.fetch(Series("EUR", "AUD", "low", "2021-01-04", "2021-01-08"))
    mid = src.fetch(Series("EUR", "AUD", "mid", "2021-01-04", "2021-01-08"))
    assert cls.prices[0].amount == Decimal("1.59718")
    assert opn.prices[0].amount == Decimal("1.58741")
    assert hgh.prices[0].amount == Decimal("1.60296")
    assert low.prices[0].amount == Decimal("1.58550")
    assert mid.prices[0].amount == Decimal("1.59423")


def test_fetch_physical_adjclose_not_available(src):
    with pytest.raises(exceptions.InvalidType) as e:
        src.fetch(Series("EUR", "AUD", "adjclose", "2021-01-04", "2021-01-08"))
    assert "Invalid price type 'adjclose' for pair 'EUR/AUD'." in str(e)


def test_fetch_physical_type_mid_is_mean_of_low_and_high(
    src, physical_list_ok, euraud_ok
):
    hgh = src.fetch(Series("EUR", "AUD", "high", "2021-01-04", "2021-01-08")).prices
    low = src.fetch(Series("EUR", "AUD", "low", "2021-01-04", "2021-01-08")).prices
    mid = src.fetch(Series("EUR", "AUD", "mid", "2021-01-04", "2021-01-08")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 5)
        ]
    )


def test_fetch_physical_bad_sym(src, type, physical_list_ok, digital_list_ok):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("NOTPHYSICAL", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "base must be a known physical or digital currency" in str(e.value)


def test_fetch_physical_network_issue(src, type, physical_list_ok, requests_mock):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, physical_url, body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Network issue" in str(e.value)


def test_fetch_physical_bad_status(src, type, physical_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_url, status=500, body="Some other reason")
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_physical_parsing_error(src, type, physical_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "while parsing data" in str(e.value)


def test_fetch_physical_unexpected_json(src, type, physical_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_url, body='{"notdata": []}')
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Unexpected content" in str(e.value)


def test_fetch_physical_rate_limit(src, type, physical_list_ok, requests_mock):
    requests_mock.add(responses.GET, physical_url, body=rate_limit_json)
    with pytest.raises(exceptions.RateLimit) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "rate limit" in str(e.value)


def test_fetch_digital_known(src, type, physical_list_ok, digital_list_ok, btcaud_ok):
    series = src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    req = btcaud_ok.calls[2].request
    assert req.params["function"] == "DIGITAL_CURRENCY_DAILY"
    assert req.params["symbol"] == "BTC"
    assert req.params["market"] == "AUD"
    assert (series.base, series.quote) == ("BTC", "AUD")
    assert len(series.prices) == 5
    assert series.prices[0] == Price("2021-01-04", Decimal("43406.76014740"))
    assert series.prices[-1] == Price("2021-01-08", Decimal("55068.43820140"))


def test_fetch_digital_requests_logged(
    src, type, physical_list_ok, digital_list_ok, btcaud_ok, caplog
):
    with caplog.at_level(logging.DEBUG):
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    logged_requests = 0
    for r in caplog.records:
        if r.levelname == "DEBUG" and "curl " in r.message:
            logged_requests += 1
    assert logged_requests == 3


def test_fetch_digital_types_but_adjclose_available(
    src, physical_list_ok, digital_list_ok, btcaud_ok
):
    cls = src.fetch(Series("BTC", "AUD", "close", "2021-01-04", "2021-01-08"))
    opn = src.fetch(Series("BTC", "AUD", "open", "2021-01-04", "2021-01-08"))
    hgh = src.fetch(Series("BTC", "AUD", "high", "2021-01-04", "2021-01-08"))
    low = src.fetch(Series("BTC", "AUD", "low", "2021-01-04", "2021-01-08"))
    mid = src.fetch(Series("BTC", "AUD", "mid", "2021-01-04", "2021-01-08"))
    assert cls.prices[0].amount == Decimal("43406.76014740")
    assert opn.prices[0].amount == Decimal("44779.08784700")
    assert hgh.prices[0].amount == Decimal("45593.18400000")
    assert low.prices[0].amount == Decimal("38170.72220000")
    assert mid.prices[0].amount == Decimal("41881.95310000")


def test_fetch_digital_adjclose_not_available(src):
    with pytest.raises(exceptions.InvalidType) as e:
        src.fetch(Series("BTC", "AUD", "adjclose", "2021-01-04", "2021-01-08"))
    assert "Invalid price type 'adjclose' for pair 'BTC/AUD'." in str(e.value)


def test_fetch_digital_type_mid_is_mean_of_low_and_high(
    src, physical_list_ok, digital_list_ok, btcaud_ok
):
    hgh = src.fetch(Series("BTC", "AUD", "high", "2021-01-04", "2021-01-08")).prices
    low = src.fetch(Series("BTC", "AUD", "low", "2021-01-04", "2021-01-08")).prices
    mid = src.fetch(Series("BTC", "AUD", "mid", "2021-01-04", "2021-01-08")).prices
    assert all(
        [
            mid[i].amount == (sum([low[i].amount, hgh[i].amount]) / 2)
            for i in range(0, 5)
        ]
    )


def test_fetch_digital_bad_sym(src, type, physical_list_ok, digital_list_ok):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("NOTDIGITAL", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "base must be a known physical or digital currency" in str(e.value)


def test_fetch_digital_network_issue(
    src, type, physical_list_ok, digital_list_ok, requests_mock
):
    body = requests.exceptions.ConnectionError("Network issue")
    requests_mock.add(responses.GET, digital_url, body=body)
    with pytest.raises(exceptions.RequestError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Network issue" in str(e.value)


def test_fetch_digital_bad_status(
    src, type, physical_list_ok, digital_list_ok, requests_mock
):
    requests_mock.add(responses.GET, digital_url, status=500, body="Some other reason")
    with pytest.raises(exceptions.BadResponse) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Internal Server Error" in str(e.value)


def test_fetch_digital_parsing_error(
    src, type, physical_list_ok, digital_list_ok, requests_mock
):
    requests_mock.add(responses.GET, digital_url, body="NOT JSON")
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "while parsing data" in str(e.value)


def test_fetch_digital_unexpected_json(
    src, type, physical_list_ok, digital_list_ok, requests_mock
):
    requests_mock.add(responses.GET, digital_url, body='{"notdata": []}')
    with pytest.raises(exceptions.ResponseParsingError) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "Unexpected content" in str(e.value)


def test_fetch_digital_rate_limit(
    src, type, physical_list_ok, digital_list_ok, requests_mock
):
    requests_mock.add(responses.GET, digital_url, body=rate_limit_json)
    with pytest.raises(exceptions.RateLimit) as e:
        src.fetch(Series("BTC", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "rate limit" in str(e.value)


def test_fetch_bad_pair_quote_non_physical(src, type, physical_list_ok):
    with pytest.raises(exceptions.InvalidPair) as e:
        src.fetch(Series("EUR", "BTC", type, "2021-01-04", "2021-01-08"))
    assert "quote must be a physical currency" in str(e.value)


def test_fetch_api_key_defaults_to_generic(
    src, type, physical_list_ok, euraud_ok, monkeypatch
):
    monkeypatch.delenv(api_key_name)
    src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    req = euraud_ok.calls[-1].request
    assert req.params["apikey"] == f"pricehist_{__version__}"


def test_fetch_api_key_invalid(src, type, physical_list_ok, requests_mock):
    body = (
        '{ "Error Message": "the parameter apikey is invalid or missing. Please '
        "claim your free API key on (https://www.alphavantage.co/support/#api-key). "
        'It should take less than 20 seconds." }'
    )
    requests_mock.add(responses.GET, physical_url, body=body)
    with pytest.raises(exceptions.CredentialsError) as e:
        src.fetch(Series("EUR", "AUD", type, "2021-01-04", "2021-01-08"))
    assert "unavailable or invalid" in str(e.value)
