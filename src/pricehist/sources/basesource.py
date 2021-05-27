from abc import ABC, abstractmethod

from pricehist.series import Series


class BaseSource(ABC):
    @abstractmethod
    def id(self) -> str:
        pass

    @abstractmethod
    def name(self) -> str:
        pass

    def description(self) -> str:
        pass

    def source_url(self) -> str:
        pass

    def start(self) -> str:
        pass

    def types(self) -> list[str]:
        pass

    def notes(self) -> str:
        pass

    def symbols(self) -> list[str]:
        pass

    def fetch(self, series: Series) -> Series:
        pass
