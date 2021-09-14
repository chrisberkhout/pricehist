import logging
from abc import ABC, abstractmethod
from textwrap import TextWrapper
from typing import List, Tuple

import curlify

from pricehist import exceptions
from pricehist.series import Series


class BaseSource(ABC):
    @abstractmethod
    def id(self) -> str:
        pass  # pragma: nocover

    @abstractmethod
    def name(self) -> str:
        pass  # pragma: nocover

    @abstractmethod
    def description(self) -> str:
        pass  # pragma: nocover

    @abstractmethod
    def source_url(self) -> str:
        pass  # pragma: nocover

    @abstractmethod
    def start(self) -> str:
        pass  # pragma: nocover

    @abstractmethod
    def types(self) -> List[str]:
        pass  # pragma: nocover

    @abstractmethod
    def notes(self) -> str:
        pass  # pragma: nocover

    def normalizesymbol(self, str) -> str:
        return str.upper()

    @abstractmethod
    def symbols(self) -> List[Tuple[str, str]]:
        pass  # pragma: nocover

    def search(self, query) -> List[Tuple[str, str]]:
        pass  # pragma: nocover

    @abstractmethod
    def fetch(self, series: Series) -> Series:
        pass  # pragma: nocover

    def log_curl(self, response):
        curl = curlify.to_curl(response.request, compressed=True)
        logging.debug(curl)
        return response

    def format_symbols(self) -> str:
        with exceptions.handler():
            symbols = self.symbols()

        width = max([len(sym) for sym, desc in symbols] + [0])
        lines = [sym.ljust(width + 4) + desc + "\n" for sym, desc in symbols]
        return "".join(lines)

    def format_search(self, query) -> str:
        with exceptions.handler():
            symbols = self.search(query)

        if symbols is None:
            logging.error(f"Symbol search is not possible for the {self.id()} source.")
            exit(1)
        elif symbols == []:
            logging.info(f"No results found for query '{query}'.")
            return ""
        else:
            width = max([len(sym) for sym, desc in symbols] + [0])
            lines = [sym.ljust(width + 4) + desc + "\n" for sym, desc in symbols]
            return "".join(lines)

    def format_info(self, total_width=80) -> str:
        k_width = 11
        with exceptions.handler():
            parts = [
                self._fmt_field("ID", self.id(), k_width, total_width),
                self._fmt_field("Name", self.name(), k_width, total_width),
                self._fmt_field(
                    "Description", self.description(), k_width, total_width
                ),
                self._fmt_field("URL", self.source_url(), k_width, total_width, False),
                self._fmt_field("Start", self.start(), k_width, total_width),
                self._fmt_field("Types", ", ".join(self.types()), k_width, total_width),
                self._fmt_field("Notes", self.notes(), k_width, total_width),
            ]
        return "\n".join(filter(None, parts))

    def _fmt_field(self, key, value, key_width, total_width, force=True):
        separator = " : "
        initial_indent = key + (" " * (key_width - len(key))) + separator
        subsequent_indent = " " * len(initial_indent)
        wrapper = TextWrapper(
            width=total_width,
            drop_whitespace=True,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
            break_long_words=force,
        )
        first, *rest = value.split("\n")
        first_output = wrapper.wrap(first)
        wrapper.initial_indent = subsequent_indent
        rest_output = sum([wrapper.wrap(line) if line else [""] for line in rest], [])
        output = "\n".join(first_output + rest_output)
        if output != "":
            return output
        else:
            return None
