"""Lazy list classes reactive to plugin updates."""

import inspect
import pprint
import sys
from typing import TYPE_CHECKING, Optional, Type, NoReturn

if sys.version_info < (3, 10):
    from importlib_metadata import entry_points
else:
    from importlib.metadata import entry_points


if TYPE_CHECKING:
    from ..loaders.data_container import DataContainer


def _get_list_ordered_by_inheritance(object_set: set) -> list:
    """Get a list of objects ordered by their inheritance depth. Children first."""

    def get_inheritance_depth(cls):
        return -len(inspect.getmro(cls))

    return sorted(object_set, key=get_inheritance_depth)


class LazyList:
    """Lazily evaluated list."""

    def __init__(self) -> None:
        self._list = []

    def _populate_list(self) -> NoReturn:
        raise NotImplementedError

    def reset(self) -> None:
        self._list = []

    @property
    def list(self):
        if not self._list:
            self._populate_list()

        return self._list

    def __iter__(self):
        return iter(self.list)

    def __getitem__(self, item):
        return self.list[item]

    def __len__(self) -> int:
        return len(self.list)

    def __add__(self, other):
        return self.list + other

    def __repr__(self) -> str:
        return pprint.pformat(self.list)


class PluginPackageNames(LazyList):
    """Lazily evaluated list of plugin package names."""

    def __init__(self, plugins_group_name: str) -> None:
        super().__init__()
        self._plugins_group_name = plugins_group_name

    def _populate_list(self) -> None:
        plugins = entry_points(group=self._plugins_group_name)
        self._list = [p.value for p in plugins]


class ClassList(LazyList):
    """Lazily evaluated list of classes."""

    def __init__(self, plugins_package_names: PluginPackageNames) -> None:
        super().__init__()
        self._plugins_package_names = plugins_package_names

        #: List of subclasses, ordered by priority
        self._list = []

        #: Dictionary of subclasses, keyed by class name.
        #: Classes further down the inheritance chain take precedence
        self._dict = {}

        #: Dictionary of subclasses, keyed by full class path (__module__ + __qualname__)
        self._full_dict = {}

    #: Name of the plugin's subpackage in which classes are searched
    subpackage_name: Optional[str] = None

    @property
    def BaseClass(self) -> type:
        """Base class of the classes to search for.

        Keep as a property (instead of a static attribute) to allow for lazy evaluation.
        """
        raise NotImplementedError

    def _get_classes_set(self):
        from .discovery import get_subclasses_from_plugins

        if self.subpackage_name is None:
            raise ValueError("subpackage_name must be set in ClassList definition")

        return get_subclasses_from_plugins(self._plugins_package_names, self.subpackage_name, self.BaseClass)

    def _populate_list(self) -> None:
        classes_set = self._get_classes_set()
        self._list = _get_list_ordered_by_inheritance(classes_set)

    def _populate_dict(self) -> None:
        for cls in self.list:
            class_name = cls.__name__
            self._dict[class_name] = cls

    def _populate_full_dict(self) -> None:
        for cls in self.list:
            class_path = f"{cls.__module__}.{cls.__qualname__}"
            self._full_dict[class_path] = cls

    def reset(self) -> None:
        self._list = []
        self._dict = {}
        self._full_dict = {}

    def as_dict(self) -> dict[str, type]:
        if not self._dict:
            self._populate_dict()

        return self._dict

    def as_full_dict(self) -> dict[str, type]:
        if not self._full_dict:
            self._populate_full_dict()

        return self._full_dict


class DownloaderList(ClassList):
    """Lazily evaluated list of downloaders."""

    subpackage_name = "downloaders"

    @property
    def BaseClass(self) -> type:
        from ..downloaders.downloader import Downloader

        return Downloader


class LoaderList(ClassList):
    """Lazily evaluated list of loaders."""

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        #: Dictionary of mime types to extensions
        self._mime_type2extensions: dict[str, list[str]] = {}

        #: Dictionary of extensions to mime types
        self._extension2mime_types: dict[str, list[str]] = {}

        #: Dictionary of mime types to loaders
        self._mime_type2loaders: dict[str, list[Type["DataContainer"]]] = {}

        #: Dictionary of extensions to loaders
        self._extension2loaders: dict[str, list[Type["DataContainer"]]] = {}

    def reset(self) -> None:
        super().reset()
        self._mime_type2extensions = {}
        self._extension2mime_types = {}
        self._mime_type2loaders = {}
        self._extension2loaders = {}

    subpackage_name = "loaders"

    @property
    def BaseClass(self) -> type:
        from ..loaders.data_container import DataContainer

        return DataContainer

    def _populate_list(self) -> None:
        from ..loaders.binary import Binary
        from ..loaders.file import File
        from ..loaders.file_sequence import FileSequence
        from ..loaders.sequence import Sequence

        # Note: the first matching type is used
        loaders_set = self._get_classes_set()
        loaders_set = loaders_set - {Binary, File, FileSequence, Sequence}

        self._list = _get_list_ordered_by_inheritance(loaders_set)
        self._list.append(Binary)  # Needs to stay at the end

    def _populate_mime_type2extensions(self) -> None:
        self._mime_type2extensions = {}

        for _cls in self.list:
            try:
                for supported_mime, exts in _cls.supported_mime_types.items():
                    if isinstance(exts, str) or not isinstance(exts, list):
                        exts = [exts]

                    for mime in [supported_mime] + _cls.other_allowed_mime_types:
                        if mime not in self._mime_type2extensions:
                            self._mime_type2extensions[mime] = []

                        for ext in exts:  # Use loop to preserve order
                            if ext not in self._mime_type2extensions[mime]:
                                self._mime_type2extensions[mime].append(ext)

            except AttributeError:
                pass

    def _populate_extension2_mime_types(self) -> None:
        self._extension2mime_types = {}

        from ..plugins.discovery import loader_list

        for _cls in loader_list:
            try:
                for supported_mime, exts in _cls.supported_mime_types.items():
                    if isinstance(exts, str) or not isinstance(exts, list):
                        exts = [exts]

                    for mime in [supported_mime] + _cls.other_allowed_mime_types:
                        for ext in exts:  # Use loop to preserve order
                            if ext not in self._extension2mime_types:
                                self._extension2mime_types[ext] = []

                            if mime not in self._extension2mime_types[ext]:
                                self._extension2mime_types[ext].append(mime)

            except AttributeError:
                pass

    def _populate_mime_type2loaders(self) -> None:
        self._mime_type2loaders = {}

        for _cls in self.list:
            try:
                if not isinstance(_cls.supported_mime_types, dict):
                    raise RuntimeError(f'"supported_mime_types" attribute of "{_cls}" class is not a dictionary')

                for mime in [e for e in _cls.supported_mime_types.keys()] + _cls.other_allowed_mime_types:
                    if mime not in self._mime_type2loaders:
                        self._mime_type2loaders[mime] = []

                    if _cls not in self._mime_type2loaders[mime]:
                        self._mime_type2loaders[mime].append(_cls)

            except AttributeError:
                pass

    def _populate_extension2loaders(self) -> None:
        self._extension2loaders = {}

        for _cls in self.list:
            try:
                if not isinstance(_cls.supported_mime_types, dict):
                    raise RuntimeError(f'"supported_mime_types" attribute of "{_cls}" class is not a dictionary')

                for ext in _cls._supported_extensions():
                    if ext not in self._extension2loaders:
                        self._extension2loaders[ext] = []

                    if _cls not in self._extension2loaders[ext]:
                        self._extension2loaders[ext].append(_cls)

            except AttributeError:
                pass

    def get_mime_type2extensions(self) -> dict[str, list[str]]:
        if not self._mime_type2extensions:
            self._populate_mime_type2extensions()

        return self._mime_type2extensions

    def get_extension2mime_types(self) -> dict[str, list[str]]:
        if not self._extension2mime_types:
            self._populate_extension2_mime_types()

        return self._extension2mime_types

    def get_mime_type2loaders(self) -> dict[str, list[Type["DataContainer"]]]:
        if not self._mime_type2loaders:
            self._populate_mime_type2loaders()

        return self._mime_type2loaders

    def get_extension2loaders(self) -> dict[str, list[Type["DataContainer"]]]:
        if not self._extension2loaders:
            self._populate_extension2loaders()

        return self._extension2loaders


class ReportList(ClassList):
    """Lazily evaluated list of reports."""

    subpackage_name = "reports"

    @property
    def BaseClass(self) -> type:
        from ..reports.report import Report

        return Report


class ScannerList(ClassList):
    """Lazily evaluated list of scanners."""

    subpackage_name = "scanners"

    @property
    def BaseClass(self) -> type:
        from ..scanners.scanner import Scanner

        return Scanner


class UploaderList(ClassList):
    """Lazily evaluated list of uploaders."""

    subpackage_name = "uploaders"

    @property
    def BaseClass(self) -> type:
        from ..uploaders.uploader import Uploader

        return Uploader


class ValidatorList(ClassList):
    """Lazily evaluated list of global validators."""

    subpackage_name = "validators"

    @property
    def BaseClass(self) -> type:
        from ..validators.validator import Validator

        return Validator


class ViewerList(ClassList):
    """Lazily evaluated list of viewers."""

    subpackage_name = "viewers"

    @property
    def BaseClass(self) -> type:
        from ..viewers.viewer import Viewer

        return Viewer
