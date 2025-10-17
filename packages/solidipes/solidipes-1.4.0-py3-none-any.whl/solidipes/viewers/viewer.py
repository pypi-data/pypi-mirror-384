from abc import ABC, abstractmethod

from ..utils.utils import classproperty
from . import backends
from typing import NoReturn

################################################################


def wrap_errors(func):
    def foo(self, *args, **kwargs):
        try:
            return func(self, *args, **kwargs)
        except Exception as e:
            if backends.current_backend == "jupyter notebook":
                from IPython.display import display

                display(e)
            elif backends.current_backend == "streamlit":
                import streamlit as st

                st.text(e)
            else:  # python
                print(e)

    return foo


################################################################


class Viewer(ABC):
    """Abstract class for viewers.

    If istanciated with data, it will directly display it.

    Args:
        data: data to display
        add_kwargs: kwargs to pass to the add method. Note: cannot be passed
            as a positional argument because of get_data_from_container
            decorator.
        show_kwargs: kwargs to pass to the show method
        **kwargs: kwargs to pass to the init method

    """

    def __init__(self, data_container=None, add_kwargs={}, show_kwargs={}, **kwargs) -> None:
        #: List of data types (apart from DataContainers) that are compatible with the viewer
        #: DataContainers themselves already declare their compatible Viewers
        self.compatible_data_types = []
        self.data_container = data_container

        if data_container is None:
            return

        self.add(data_container, **add_kwargs)
        self.show(**show_kwargs)

    @classproperty
    def class_path(cls) -> str:
        return f"{cls.__module__}.{cls.__qualname__}"

    def check_data_compatibility(self, data) -> bool:
        """Check if data is compatible with the viewer."""
        from ..loaders.data_container import DataContainer
        from ..loaders.file_sequence import FileSequence

        if isinstance(data, FileSequence):
            data = data._current_element

        if isinstance(data, DataContainer):
            for viewer_class in data.compatible_viewers:
                if isinstance(self, viewer_class):
                    return True

        else:
            if type(data) in self.compatible_data_types:
                return True

        raise TypeError(f"Data type {type(data)} is not compatible with {self.__class__.__name__} viewer.")

    @abstractmethod
    def add(self, data, **kwargs) -> None:
        """Add data to the viewer."""
        self.check_data_compatibility(data)

    @abstractmethod
    def show(self, **kwargs):
        """Show the viewer."""
        pass

    def save(self, path, **kwargs) -> NoReturn:
        """Save the view to a file."""
        raise Exception("This Viewer cannot save content to file.")
