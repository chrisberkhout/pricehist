import argparse

import pytest

from pricehist import __version__, cli, sources


def w(string):
    return string.split(" ")


def test_valid_pair():
    assert cli.valid_pair("BTC/AUD") == ("BTC", "AUD")
    assert cli.valid_pair("BTC/AUD/ignored") == ("BTC", "AUD")
    assert cli.valid_pair("SYM") == ("SYM", "")
    assert cli.valid_pair("SYM/") == ("SYM", "")
    with pytest.raises(argparse.ArgumentTypeError):
        cli.valid_pair("/SYM")
    with pytest.raises(argparse.ArgumentTypeError):
        cli.valid_pair("")


def test_valid_date():
    assert cli.valid_date("today") == cli.today()
    assert cli.valid_date("2021-12-30") == "2021-12-30"
    with pytest.raises(argparse.ArgumentTypeError) as e:
        cli.valid_date("2021-12-40")
    assert "Not a valid" in str(e.value)


def test_valid_date_before():
    assert cli.valid_date_before("2021-12-30") == "2021-12-29"
    with pytest.raises(argparse.ArgumentTypeError) as e:
        cli.valid_date_before("2021-12-40")
    assert "Not a valid" in str(e.value)


def test_valid_date_after():
    assert cli.valid_date_after("2021-12-30") == "2021-12-31"
    with pytest.raises(argparse.ArgumentTypeError) as e:
        cli.valid_date_after("2021-12-40")
    assert "Not a valid" in str(e.value)


def test_valid_char():
    assert cli.valid_char(",") == ","
    with pytest.raises(argparse.ArgumentTypeError):
        cli.valid_char("")
    with pytest.raises(argparse.ArgumentTypeError):
        cli.valid_char("12")


def test_cli_no_args_shows_usage(capfd):
    cli.cli(w("pricehist"))
    out, err = capfd.readouterr()
    assert "usage: pricehist" in out
    assert "optional arguments:" in out or "options:" in out
    assert "commands:" in out


def test_cli_help_shows_usage_and_exits(capfd):
    with pytest.raises(SystemExit) as e:
        cli.cli(w("pricehist -h"))
    assert e.value.code == 0
    out, err = capfd.readouterr()
    assert "usage: pricehist" in out
    assert "optional arguments:" in out or "options:" in out
    assert "commands:" in out


def test_cli_verbose(capfd, mocker):
    cli.cli(w("pricehist --verbose"))
    out, err = capfd.readouterr()
    assert "Ended pricehist run at" in err


def test_cli_version(capfd):
    cli.cli(w("pricehist --version"))
    out, err = capfd.readouterr()
    assert f"pricehist {__version__}\n" == out


def test_cli_sources(capfd):
    cli.cli(w("pricehist sources"))
    out, err = capfd.readouterr()
    for source_id in sources.by_id.keys():
        assert source_id in out


def test_cli_source(capfd):
    expected = sources.by_id["ecb"].format_info() + "\n"
    cli.cli(w("pricehist source ecb"))
    out, err = capfd.readouterr()
    assert out == expected


def test_cli_source_symbols(capfd, mocker):
    sources.by_id["ecb"].symbols = mocker.MagicMock(
        return_value=[("EUR/AUD", "Euro against Australian Dollar")]
    )
    cli.cli(w("pricehist source ecb --symbols"))
    out, err = capfd.readouterr()
    assert out == "EUR/AUD    Euro against Australian Dollar\n"


def test_cli_source_search(capfd, mocker):
    sources.by_id["alphavantage"].search = mocker.MagicMock(
        return_value=[("TSLA", "Tesla Inc, Equity, United States, USD")]
    )
    cli.cli(w("pricehist source alphavantage --search TSLA"))
    out, err = capfd.readouterr()
    assert out == "TSLA    Tesla Inc, Equity, United States, USD\n"


def test_cli_source_fetch(capfd, mocker):
    formatted_result = "P 2021-01-01 00:00:00 BTC 24139.4648 EUR\n"
    cli.fetch = mocker.MagicMock(return_value=formatted_result)
    argv = w("pricehist fetch coindesk BTC/EUR -s 2021-01-01 -e 2021-01-01 -o ledger")
    cli.cli(argv)
    out, err = capfd.readouterr()
    assert out == formatted_result


def test_cli_source_fetch_invalid_start(capfd, mocker):
    argv = w("pricehist fetch coindesk BTC/EUR -s 2021-01-01 -e 2020-12-01")
    with pytest.raises(SystemExit) as e:
        cli.cli(argv)
    assert e.value.code != 0
    out, err = capfd.readouterr()
    assert "end date '2020-12-01' preceeds the start date" in err


def test_cli_source_fetch_invalid_type(capfd, mocker):
    argv = w("pricehist fetch coindesk BTC/EUR -t notype")
    with pytest.raises(SystemExit) as e:
        cli.cli(argv)
    assert e.value.code != 0
    out, err = capfd.readouterr()
    assert "price type 'notype' is not recognized" in err


def test_cli_source_fetch_sets_source_defaults(mocker):
    cli.fetch = mocker.MagicMock(return_value="")
    cli.cli(w("pricehist fetch coindesk BTC/EUR"))
    captured_series = cli.fetch.call_args.args[0]
    assert captured_series.start == sources.by_id["coindesk"].start()
    assert captured_series.type == sources.by_id["coindesk"].types()[0]


def test_cli_source_fetch_normalizes_symbols(mocker):
    cli.fetch = mocker.MagicMock(return_value="")
    cli.cli(w("pricehist fetch coindesk btc/eur"))
    captured_series = cli.fetch.call_args.args[0]
    assert captured_series.base == "BTC"
    assert captured_series.quote == "EUR"


def test_cli_source_fetch_handles_brokenpipeerror(caplog, mocker):
    cli.fetch = mocker.MagicMock(side_effect=BrokenPipeError())
    cli.cli(w("pricehist fetch coindesk BTC/EUR --verbose"))
    assert any(
        [
            "DEBUG" == r.levelname and "output pipe was closed early" in r.message
            for r in caplog.records
        ]
    )
