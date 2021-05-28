import logging
from abc import ABC, abstractmethod
from textwrap import TextWrapper

import curlify

from pricehist.series import Series


class BaseSource(ABC):
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    @abstractmethod
    def description(self) -> str:
        pass

    @abstractmethod
    def source_url(self) -> str:
        pass

    @abstractmethod
    def start(self) -> str:
        pass

    @abstractmethod
    def types(self) -> list[str]:
        pass

    @abstractmethod
    def notes(self) -> str:
        pass

    @abstractmethod
    def symbols(self) -> list[(str, str)]:
        pass

    @abstractmethod
    def fetch(self, series: Series) -> Series:
        pass

    def log_curl(self, response):
        curl = curlify.to_curl(response.request, compressed=True)
        logging.debug(f"Request to {self.id()}: {curl}")
        return response

    def format_symbols(self) -> str:
        symbols = self.symbols()
        width = max([len(sym) for sym, desc in symbols])
        lines = [sym.ljust(width + 4) + desc for sym, desc in symbols]
        return "\n".join(lines)

    def format_info(self, total_width=80) -> str:
        k_width = 11
        parts = [
            self._fmt_field("ID", self.id(), k_width, total_width),
            self._fmt_field("Name", self.name(), k_width, total_width),
            self._fmt_field("Description", self.description(), k_width, total_width),
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
        rest_output = sum([wrapper.wrap(line) if line else ["\n"] for line in rest], [])
        output = "\n".join(first_output + rest_output)
        if output != "":
            return output
        else:
            return None
