from typing import TypeVar

from ..plugins.discovery import validator_list
from .validator import Validator


class DatasetProxy:
    def __init__(self) -> None:
        """Proxy to lazy import the data_container module."""
        self._dataset = None

    def _load_dataset(self):
        from ..loaders.data_container import DataContainer

        class Dataset(DataContainer):
            def _get_class_validators(self) -> list[Validator]:
                """Fill the list of validators for this class"""
                return [Validator() for Validator in validator_list]

        self._dataset = Dataset()

    def __getattr__(self, name):
        if self._dataset is None:
            self._load_dataset()

        return getattr(self._dataset, name)


dataset = DatasetProxy()


T = TypeVar("T", bound=Validator)


def get_global_validator(validator_class: type[T]) -> T:
    """Get a global validator instance given its class."""
    for validator in dataset.validators:
        if isinstance(validator, validator_class):
            return validator

    raise ValueError(f"Validator {validator_class.name} not found in global validators")
