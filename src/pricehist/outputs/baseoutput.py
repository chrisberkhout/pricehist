from abc import ABC, abstractmethod


class BaseOutput(ABC):
    @abstractmethod
    def format(self) -> str:
        pass
