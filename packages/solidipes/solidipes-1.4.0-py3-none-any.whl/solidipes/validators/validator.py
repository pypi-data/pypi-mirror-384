from abc import ABC, abstractmethod
from typing import Any, Callable, Generic, Optional, TypeVar, Union

T = TypeVar("T")
_validation_errors: list[str] = []  # Not thread-safe


def add_validation_error(errors: Union[str, list[str]]) -> None:
    """Add a validation error to the current validation context."""
    if isinstance(errors, str):
        errors = [errors]

    _validation_errors.extend(errors)


class Validator(ABC, Generic[T]):
    """Abstract class for validators."""

    def __init__(self, description: str, mandatory: bool = True, manually_settable: bool = False):
        self.description = description
        self.mandatory = mandatory
        self.manually_settable = manually_settable

    @property
    def name(self):
        return self.__class__.__name__

    @abstractmethod
    def _validate(self, obj: Optional[T] = None) -> Union[bool, Any]:
        """Validate an object and optionally return a boolean. Can raise exceptions."""
        pass

    def validate(self, obj: Optional[T] = None) -> "ValidationResult":
        """Validate an object and return a ValidationResult, also catching exceptions."""
        global _validation_errors
        _validation_errors = []

        try:
            result = self._validate(obj)

            if result is False:
                return ValidationResult(self, False, _validation_errors)

            return ValidationResult(self, True, _validation_errors)

        except Exception as e:
            return ValidationResult(self, False, _validation_errors + [str(e)])

    def __call__(self, *args, **kwargs) -> "ValidationResult":
        """Call the `validate` method."""
        return self.validate(*args, **kwargs)


class ValidationResult:
    """Result of a validation, evaluable as a boolean, and containing the list of errors and warnings."""

    def __init__(self, validator: Validator, valid: bool, errors: list[str]) -> None:
        self.validator = validator
        self.valid = valid
        #: List of errors and warnings
        self.errors = errors

        if len(self.errors) == 0 and not self.valid:
            self.errors.append(f'"{validator.description}" is not fulfilled')

    def __bool__(self) -> bool:
        return self.valid

    def __str__(self) -> str:
        return f"{self.validator.description}: {self.valid}" + (
            "\n- " + "\n- ".join(self.errors) if self.errors else ""
        )

    def __repr__(self) -> str:
        return str(self)


def validator(description: str, mandatory: bool = True, manually_settable=False) -> Callable:
    """Decorator to add a Validator class attribute to another class.

    The decorated method should return None or a list of strings with the errors. The method can also raise exceptions.
    """

    def decorator(func: Callable[[T], Union[bool, Any]]) -> Validator[T]:
        class NewValidator(Validator):
            def _validate(self, obj: T) -> Any:
                return func(obj)

            def __get__(self, obj: Optional[T], obj_class: type[T]) -> Union[Validator[T], bool, Any]:
                if obj is None:
                    return self
                return lambda: self._validate(obj)

        name = "".join(word.capitalize() for word in func.__name__.split("_")) + "Validator"
        NewValidator.__name__ = name
        NewValidator.__qualname__ = name

        validator = NewValidator(description=description, mandatory=mandatory, manually_settable=manually_settable)
        validator.__doc__ = func.__doc__
        return validator

    return decorator
