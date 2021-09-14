import logging
from typing import List, Tuple

import pytest

from pricehist.series import Series
from pricehist.sources.basesource import BaseSource


class TestSource(BaseSource):
    def id(self) -> str:
        return ""

    def name(self) -> str:
        return ""

    def description(self) -> str:
        return ""

    def source_url(self) -> str:
        return ""

    def start(self) -> str:
        return ""

    def types(self) -> List[str]:
        return []

    def notes(self) -> str:
        return ""

    def symbols(self) -> List[Tuple[str, str]]:
        return []

    def fetch(self, series: Series) -> Series:
        pass


@pytest.fixture
def src():
    return TestSource()


def test_normalizesymbol_default_uppercase(src):
    assert src.normalizesymbol("eur") == "EUR"


def test_format_symbols_one(src, mocker):
    src.symbols = mocker.MagicMock(return_value=[("A", "Description")])
    assert src.format_symbols() == "A    Description\n"


def test_format_symbols_many(src, mocker):
    src.symbols = mocker.MagicMock(
        return_value=[
            ("A", "Description"),
            ("BB", "Description longer"),
            ("CCC", "Description longer again"),
            ("DDDD", f"Description {'very '*15}long"),
        ]
    )
    assert src.format_symbols() == (
        "A       Description\n"
        "BB      Description longer\n"
        "CCC     Description longer again\n"
        "DDDD    Description very very very very very very very very "
        "very very very very very very very long\n"
    )


def test_format_search(src, mocker):
    src.search = mocker.MagicMock(
        return_value=[
            ("A", "Description"),
            ("BB", "Description longer"),
            ("CCC", "Description longer again"),
            ("DDDD", f"Description {'very '*15}long"),
        ]
    )
    assert src.format_search("some query") == (
        "A       Description\n"
        "BB      Description longer\n"
        "CCC     Description longer again\n"
        "DDDD    Description very very very very very very very very "
        "very very very very very very very long\n"
    )


def test_format_search_not_possible(src, mocker, caplog):
    src.search = mocker.MagicMock(return_value=None)
    with caplog.at_level(logging.INFO):
        with pytest.raises(SystemExit) as e:
            src.format_search("some query")
    assert e.value.code == 1
    r = caplog.records[0]
    assert r.levelname == "ERROR"
    assert "Symbol search is not possible for" in r.message


def test_format_search_no_results(src, mocker, caplog):
    src.search = mocker.MagicMock(return_value=[])
    with caplog.at_level(logging.INFO):
        results = src.format_search("some query")
    r = caplog.records[0]
    assert r.levelname == "INFO"
    assert "No results found" in r.message
    assert results == ""


def test_format_info_skips_renderes_all_fields(src, mocker):
    src.id = mocker.MagicMock(return_value="sourceid")
    src.name = mocker.MagicMock(return_value="Source Name")
    src.description = mocker.MagicMock(return_value="Source description.")
    src.source_url = mocker.MagicMock(return_value="https://example.com/")
    src.start = mocker.MagicMock(return_value="2021-01-01")
    src.types = mocker.MagicMock(return_value=["open", "close"])
    src.notes = mocker.MagicMock(return_value="Notes for user.")
    output = src.format_info()
    assert output == (
        "ID          : sourceid\n"
        "Name        : Source Name\n"
        "Description : Source description.\n"
        "URL         : https://example.com/\n"
        "Start       : 2021-01-01\n"
        "Types       : open, close\n"
        "Notes       : Notes for user."
    )


def test_format_info_skips_empty_fields(src, mocker):
    src.notes = mocker.MagicMock(return_value="")
    output = src.format_info()
    assert "Notes" not in output


def test_format_info_wraps_long_values_with_indent(src, mocker):
    notes = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim "
        "ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut "
        "aliquip ex ea commodo consequat."
    )
    src.notes = mocker.MagicMock(return_value=notes)
    output = src.format_info(total_width=60)
    assert output == (
        "Notes       : Lorem ipsum dolor sit amet, consectetur\n"
        "              adipiscing elit, sed do eiusmod tempor\n"
        "              incididunt ut labore et dolore magna aliqua.\n"
        "              Ut enim ad minim veniam, quis nostrud\n"
        "              exercitation ullamco laboris nisi ut aliquip\n"
        "              ex ea commodo consequat."
    )


def test_format_info_newline_handling(src, mocker):
    notes = (
        "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do "
        "eiusmod tempor incididunt ut labore.\n"
        "Ut enim ad minim veniam.\n"
        "\n"
        "Quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
        "commodo consequat."
    )
    src.notes = mocker.MagicMock(return_value=notes)
    output = src.format_info(total_width=60)
    assert output == (
        "Notes       : Lorem ipsum dolor sit amet, consectetur\n"
        "              adipiscing elit, sed do eiusmod tempor\n"
        "              incididunt ut labore.\n"
        "              Ut enim ad minim veniam.\n"
        "\n"
        "              Quis nostrud exercitation ullamco laboris nisi\n"
        "              ut aliquip ex ea commodo consequat."
    )


def test_format_info_does_not_wrap_source_url(src, mocker):
    url = "https://www.example.com/longlonglonglonglonglonglonglong/"
    src.source_url = mocker.MagicMock(return_value=url)
    output = src.format_info(total_width=60)
    assert output == (
        "URL         : https://www.example.com/longlonglonglonglonglonglonglong/"
    )
