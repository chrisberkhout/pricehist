from abc import ABC, abstractmethod

from pricehist.format import Format
from pricehist.series import Series
from pricehist.sources.basesource import BaseSource


class BaseOutput(ABC):
    @abstractmethod
    def format(self, series: Series, source: BaseSource, fmt: Format) -> str:
        pass  # pragma: nocover
