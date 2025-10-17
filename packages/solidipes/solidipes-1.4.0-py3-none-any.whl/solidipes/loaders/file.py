import os
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Type, Union

if TYPE_CHECKING:
    pass

from ..plugins.discovery import get_all_subclasses, loader_list
from ..utils import get_path_relative_to_root
from ..utils import solidipes_logging as logging
from ..validators.validator import add_validation_error, validator
from .cached_metadata import CachedMetadata
from .rocrate_metadata import ROCrateMetadata
from .data_container import DataContainer
from .mime_types import get_extension, get_mime_type, is_valid_extension

logger = logging.getLogger()


#: List of supported extensions per class
_supported_extensions = {}


class File(ROCrateMetadata):
    """Abstract container class for file metadata.

    A File can be read from disk and may contain multiple DataContainer
    entries.
    """

    from ..viewers.viewer import Viewer

    #: List of supported mime types and extensions. Override in subclasses.
    #: The key is the mime type and the value is one or more file extensions (string or list of strings)
    supported_mime_types = {}

    #: List of other allowed mime types (when automatic detection is inaccurate).
    other_allowed_mime_types = ["text/plain"]

    #: List of compatible Viewer classes. Doesn't need to include Viewer classes already listed in parent classes.
    _compatible_viewers: list[Type[Viewer]] = []

    @classmethod
    def _supported_extensions(cls):
        name = cls.class_path
        if name in _supported_extensions:
            return _supported_extensions[name]
        _supported_extensions[name] = []

        if not isinstance(cls.supported_mime_types, dict):
            raise RuntimeError(f"need adapting class {cls}")
        for _, exts in cls.supported_mime_types.items():
            if isinstance(exts, str) or not isinstance(exts, list):
                exts = [exts]
            _supported_extensions[name] += exts
        _supported_extensions[name] = list(set(_supported_extensions[name]))
        return _supported_extensions[name]

    def __init__(self, path=None) -> None:
        if path is None:
            raise RuntimeError("File need a path to be initialized")

        logger.debug(f"Loading a file as data container {path}")
        self.path = path
        self._discussions = []
        self._archived_discussions = False
        super().__init__(
            unique_identifier=get_path_relative_to_root(path),
            name=os.path.basename(path),
        )

    @CachedMetadata.cached_loadable
    def modified_time(self):
        return os.lstat(self.path).st_mtime

    @CachedMetadata.cached_loadable
    def preferred_loader_name(self) -> str:
        return self.class_path

    @CachedMetadata.cached_loadable
    def preferred_viewer_name(self) -> Optional[str]:
        return super().preferred_viewer_name

    def add_message(self, author, msg) -> None:
        self._discussions = self.discussions
        self._discussions.append((author, msg))
        self.discussions = self._discussions

    def archive_discussions(self, flag=True) -> None:
        self._archived_discussions = flag
        self.archived_discussions = self._archived_discussions

    @validator(description="File not empty")
    def _is_not_empty(self) -> bool:
        return self.file_info.size > 0

    @validator(description="File's extension matches its mime type")
    def _has_valid_extension(self) -> bool:
        if is_valid_extension(self.file_info.path, self.file_info.type):
            return True

        else:
            add_validation_error([
                f"Mime type '{self.file_info.type}' does not match extension"
                f" '{os.path.splitext(self.file_info.path)[1]}'"
            ])
            return False

    @ROCrateMetadata.rocrate_metadata
    def discussions(self):
        return self._discussions

    @CachedMetadata.cached_loadable
    def archived_discussions(self):
        return self._archived_discussions

    @validator(description="All comments resolved")
    def _has_unresolved_comments(self) -> bool:
        return len(self.discussions) == 0 or self.archived_discussions

    @DataContainer.loadable
    def file_stats(self):
        stats = os.lstat(self.path)
        return stats

    @CachedMetadata.cached_loadable
    def file_info(self):
        stats = self.file_stats
        mime_type, charset = get_mime_type(self.path)
        return DataContainer({
            "size": stats.st_size,
            "changed_time": stats.st_ctime,
            "created_time": stats.st_ctime,
            "modified_time": stats.st_mtime,
            "permissions": stats.st_mode,
            "owner": stats.st_uid,
            "group": stats.st_gid,
            "path": self.path.strip(),
            "type": mime_type or "",
            "charset": charset.strip(),
            "extension": get_extension(self.path).strip(),
        })


def load_file(path: Union[str, Path]) -> File:
    """Load a file from path into the appropriate object type."""
    from .binary import Binary
    from .symlink import SymLink

    path = str(path)  # In case path is a Path object
    if os.path.islink(path):
        return SymLink(path=path)

    if not os.path.isfile(path):
        raise FileNotFoundError(f'File "{path}" does not exist')

    # Get cached preferred loader
    preferred_loader = get_cached_preferred_loader(path)

    if preferred_loader:
        try:
            obj = preferred_loader(path=path)

            for pref_type in preferred_loader.supported_mime_types:
                if obj.file_info.type.startswith(pref_type):
                    return obj

            if obj.file_info.extension in preferred_loader._supported_extensions():
                return obj

            if preferred_loader == Binary:
                return obj

        except RuntimeError as e:
            import streamlit as st

            st.error(f"Cannot load {type(path)}: {type(e)}")
            st.error(f"Cannot load {path}: {e}")

        logger.warning(
            "Cache miss:"
            f" {path} {preferred_loader} {preferred_loader.supported_mime_types}"
            f" {preferred_loader._supported_extensions()}"
        )

    # If no cached preferred loader, try to find a loader
    extension = get_extension(path)

    # If unknown type, assume binary
    if extension == "":
        mime_type = get_mime_type(path)[0]
        logger.info(f"mime_type: {mime_type}")
        mime2loader = loader_list.get_mime_type2loaders()
        logger.debug(f"mime2loader: {mime2loader.keys()}")
        if mime_type in mime2loader:
            loaders = mime2loader[mime_type]
            logger.error(f"possible loaders: {loaders}")
            sorted_loaders = [(e, len(get_all_subclasses(e))) for e in loaders]
            sorted_loaders = sorted(sorted_loaders, key=lambda x: x[1], reverse=True)
            sorted_loaders = [e[0] for e in sorted_loaders]
            logger.error(f"sorted possible loaders: {sorted_loaders}")
            loader = sorted_loaders[0]
            logger.error(f"loader selected from mime: {loader}")

            return loader(path=path)
        return Binary(path=path)

    if extension in loader_list.get_extension2loaders():
        loader = loader_list.get_extension2loaders()[extension][0]
        return loader(path=path)

    # If unknown type, assume binary
    return Binary(path=path)


def get_cached_preferred_loader(path: str) -> Optional[Type[File]]:
    """Get the preferred loader for a file from global cache."""
    from .cached_metadata import CachedMetadata

    unique_identifier = get_path_relative_to_root(path)
    preferred_loader_name = (
        CachedMetadata.get_global_cached_metadata().get(unique_identifier, {}).get("preferred_loader_name", None)
    )

    return loader_list.as_full_dict().get(preferred_loader_name, None)
