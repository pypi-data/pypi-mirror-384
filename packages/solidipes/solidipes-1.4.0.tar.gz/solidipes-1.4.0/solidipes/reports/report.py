import argparse
from abc import ABC, abstractmethod

from solidipes.utils.utils import classproperty


class Report(ABC):
    command: str
    command_help: str
    _aliases: list[str] = []

    @classproperty
    def aliases(cls) -> list[str]:
        return cls._aliases if "_aliases" in cls.__dict__ else []

    @abstractmethod
    def make(self, args: argparse.Namespace) -> None:
        pass

    @abstractmethod
    def populate_parser(self, parser: argparse.ArgumentParser) -> None:
        pass
