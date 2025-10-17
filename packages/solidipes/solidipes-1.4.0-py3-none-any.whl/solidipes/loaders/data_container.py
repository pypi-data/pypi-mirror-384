from typing import TYPE_CHECKING, Optional, Type

if TYPE_CHECKING:
    from ..viewers.viewer import Viewer

from ..plugins.discovery import apply_to_object_parent_classes, viewer_list
from ..utils import solidipes_logging as logging
from ..utils.utils import classproperty, transform_dict_to_data_containers
from ..validators.validator import ValidationResult, Validator, validator

logger = logging.getLogger()

################################################################


#: Lists of validators for each DataContainer class
_validators: dict[str, list[Validator]] = {}


################################################################


class TemporaryFile:
    def __init__(self, delete=False, init=True) -> None:
        import os
        import tempfile

        self._delete = delete

        if not init:
            return
        with tempfile.NamedTemporaryFile(delete=True) as fp:
            self._name = fp.name
        self._dir = os.path.dirname(self._name)
        self._basename = os.path.split(self._name)[-1]
        self._extensions = set()

    def open(self, ext=None, options="r"):
        return open(self.fname(ext), options)

    def fname(self, ext=None):
        import os

        name = os.path.join(self._dir, self._basename)
        if ext is not None:
            name += "." + ext
        return name

    def __del__(self) -> None:
        if not self._delete:
            return
        import os

        for ext in self._extensions:
            os.remove(self.fname(ext))

    def add_extensions(self, extensions) -> None:
        for i in extensions:
            self._extensions.add(i)

    def getstate(self):
        state = self.__dict__.copy()
        return state

    def setstate(self, state) -> None:
        self.__dict__.update(state)

    def __repr__(self) -> str:
        return "TemporaryFiles:" + self.fname() + "[" + ",".join(self._extensions) + "]"


################################################################


class loadable(property):
    def __init__(self, fget, *args, **kwargs) -> None:
        """Decorator for DataContainer properties that are loaded on demand."""

        self.key = fget.__name__
        self.original_fget = fget

        super().__init__(fget=self.wrapped_fget, fset=self.wrapped_fset, doc=fget.__doc__)

    def wrapped_fget(self, obj):
        if self.key in obj._data_collection and obj._data_collection[self.key] is not None:
            return obj._data_collection[self.key]

        data = self.original_fget(obj)

        if data is None:
            message = f'Data "{self.key}" could not be loaded'
            logger.error(message)
            raise Exception(message)

        obj._data_collection[self.key] = data

        return data

    def wrapped_fset(self, obj, value) -> None:
        obj._data_collection[self.key] = transform_dict_to_data_containers(value)


################################################################


class DataContainer:
    """Container class for other structured data containers."""

    from ..viewers.viewer import Viewer

    #: List of compatible Viewer classes. Doesn't need to include Viewer classes already listed in parent classes.
    _compatible_viewers: list[Type[Viewer]] = []

    loadable = loadable

    def __init__(self, initial_data={}, name=None, unique_identifier=None, **kwargs) -> None:
        super().__init__(**kwargs)
        logger.debug(f"Creating data container {type(self)}")
        self.name = None
        self.unique_identifier = unique_identifier

        #: Dictionary of other DataContainer or arbitrary objects.
        #: Set entry to "None" to mark as loadable.
        self._data_collection = initial_data.copy()

        def register_to_data_collection(cls) -> None:
            for key, v in cls.__dict__.items():
                if isinstance(v, loadable):
                    if key not in self._data_collection:
                        self.add(key)

        apply_to_object_parent_classes(self.__class__, register_to_data_collection)

        self.validators = self._get_class_validators()
        self._validator_enabled = {validator.name: True for validator in self.validators}

    @classproperty
    def class_path(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    def _get_class_validators(self) -> list[Validator]:
        """Fill the list of validators for this class."""
        cls = self.__class__
        cls_name = f"{cls.__module__}.{cls.__qualname__}"

        if cls_name in _validators:
            return _validators[cls_name]

        _validators[cls_name] = []

        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)

            if isinstance(attribute, Validator):
                _validators[cls_name].append(attribute)

        return _validators[cls_name]

    @property
    def validator_enabled(self) -> dict[str, bool]:
        """Dictionary of validator names and enabled status."""
        return self._validator_enabled

    def enable_validator(self, name: str) -> None:
        """Enable a specific validator."""
        self.validator_enabled[name] = True

    def disable_validator(self, name: str) -> None:
        """Disable a specific validator."""
        for validator_ in self.validators:
            if validator_.name != name:
                continue

            if validator_.mandatory:
                raise ValueError(f"Cannot disable mandatory validator {name}")

        self.validator_enabled[name] = False

    @property
    def validation_results(self) -> list[ValidationResult]:
        """Dictionary of validation results."""
        return [validator.validate(self) for validator in self.validators]

    @property
    def errors(self) -> list[str]:
        """List of validation errors."""
        errors = []

        for validation_result in self.validation_results:
            errors.extend(validation_result.errors)

        return errors

    @property
    def is_valid(self) -> bool:
        """Evaluate if all validators are passing."""
        for validation_result in self.validation_results:
            validator = validation_result.validator

            if not validation_result.valid and (self.validator_enabled[validator.name] or validator.mandatory):
                return False

        return True

    def copy(self):
        """Returns a shallow copy without the need to read from disk again."""
        cls = self.__class__
        new = cls.__new__(cls)
        new.__dict__.update(self.__dict__)
        new._data_collection = self._data_collection.copy()
        return new

    @property
    def data_info(self):
        """Returns a multi-line string with information about data keys."""
        info_list = []

        for key, data in self._data_collection.items():
            if data is None:
                info_list.append(f"{key}: Not loaded")
            else:
                info_list.append(f"{key}: {type(self._data_collection[key])}")

        return "\n".join(info_list)

    @property
    def data(self):
        """Load all data if necessary and return it.

        Accessing this property for the first time will load the data.
        If self.__loaded_data has only one entry, returns it directly.

        Override the _load_data method in subclasses to define how data is
        loaded or built using other data containers.
        """
        self.load_all()

        # Return data
        if len(self._data_collection) == 1:
            return list(self._data_collection.values())[0]
        else:
            return self._data_collection

    @validator(description="Data is loadable")
    def load_all(self) -> None:
        """Load all data."""
        # Find keys that have a None value and load them
        keys = [e for e in self._data_collection.keys()]
        for key in keys:
            if self._data_collection[key] is None:
                # Trigger loading of data
                self.get(key)

    def add(self, key, data=None) -> None:
        """Add an arbitrary object to the data collection."""
        self._data_collection[key] = data

    def get(self, key):
        """Get a data object by key, loading it if necessary."""
        logger.debug(f"get({key})")
        try:
            data = self._data_collection[key]
        except KeyError as e:
            raise KeyError(f"{e}\nDid you register this key somehow ?")

        # Load data
        if data is None:
            data = getattr(self, key)
            if data is None:
                raise Exception(f'Data "{key}" could not be loaded')
            self._data_collection[key] = data

        logger.debug(f"got({key}) = {data}")
        return data

    def remove(self, key) -> None:
        """Remove a data object from the data collection."""
        del self._data_collection[key]

    def has(self, key):
        """Check if data is available in this container."""
        return key in self._data_collection

    def _has_native_attr(self, key) -> bool | None:
        """Check if attribute is present, outside of _data_collection, without using __getattr__."""
        try:
            self.__getattribute__(key)
            return True
        except AttributeError:
            return False

    def __getattr__(self, name):
        """Get a data object by key, loading it if necessary.

        Only works if the name is not already an attribute of this class.
        """
        try:
            return self.get(name)
        except KeyError:
            raise AttributeError(f"'{self.__class__.__name__}' has no attribute '{name}'")

    def __getitem__(self, key):
        """Get a data object by key, loading it if necessary."""
        return self.get(key)

    def __setitem__(self, key, value) -> None:
        """Set a data object by key."""
        self.add(key, value)

    def __delitem__(self, key) -> None:
        """Remove a data object by key."""
        self.remove(key)

    def __contains__(self, key) -> bool:
        """Check if data is available in this container."""
        return self.has(key)

    @classproperty
    def compatible_viewers(cls) -> list[Type[Viewer]]:
        return [
            viewer
            for c in cls.mro()
            if issubclass(c, DataContainer) and "_compatible_viewers" in c.__dict__
            for viewer in c._compatible_viewers
        ]

    @property
    def preferred_viewer_name(self) -> str:
        """Returns the default viewer name for this data container."""
        if "preferred_viewer_name" not in self.__dict__:
            self.__dict__["preferred_viewer_name"] = (
                self.compatible_viewers[0].class_path if len(self.compatible_viewers) != 0 else ""
            )

        return self.__dict__["preferred_viewer_name"]

    @preferred_viewer_name.setter
    def preferred_viewer_name(self, viewer_name: str) -> None:
        """Set the default viewer name for this data container."""
        self.__dict__["preferred_viewer_name"] = viewer_name

    @property
    def preferred_viewer(self) -> Optional[Type["Viewer"]]:
        """Returns the default viewer for this data container."""
        return viewer_list.as_full_dict().get(self.preferred_viewer_name, None)

    @preferred_viewer.setter
    def preferred_viewer(self, viewer: Optional[Type["Viewer"]]) -> None:
        """Set the default viewer for this data container. Adds the viewer to the list of compatible viewers."""
        if viewer is not None and viewer not in self.compatible_viewers:
            self.compatible_viewers.insert(0, viewer)

        self.preferred_viewer_name = viewer.class_path if viewer is not None else ""

    def view(self, **kwargs):
        """View the file using the preferred viewer."""
        if self.preferred_viewer is None:
            raise Exception("This File cannot be viewed directly. Use get_data to get a Dataobject.")

        viewer = self.preferred_viewer(self, **kwargs)

        return viewer

    def __str__(self) -> str:
        return self.__class__.__name__

    def __repr__(self) -> str:
        return self._data_collection.__repr__()

    def __eq__(self, other) -> bool:
        """Check equality based on _data_collection."""
        if isinstance(other, DataContainer):
            other = other._data_collection
        return self._data_collection == other
