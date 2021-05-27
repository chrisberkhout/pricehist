import logging
from abc import ABC, abstractmethod

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
