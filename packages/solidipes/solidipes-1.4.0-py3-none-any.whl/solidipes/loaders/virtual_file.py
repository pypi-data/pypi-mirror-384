import os
from copy import copy

from solidipes.loaders.data_container import DataContainer

from ..utils import solidipes_logging as logging
from .cached_metadata import CachedMetadata

logger = logging.getLogger()


class VirtualFile(CachedMetadata):
    """Remote file, potentially formatted with markdown."""

    from solidipes.viewers.binary import Binary as BinaryViewer

    _compatible_viewers = [BinaryViewer]

    def __init__(self, path=None, metadata=None, **kwargs) -> None:
        self._metadata = copy(metadata)
        self._path = path
        self._metadata["path"] = path
        logger.debug(path)
        logger.debug(metadata)

        self._metadata["size"] = self._metadata["size_in_bytes"]
        self._metadata["type"] = "virtual (dtool)"
        self._metadata["extension"] = os.path.splitext(self._metadata["relpath"])[1][1:]
        self._discussions = []
        self._archived_discussions = False

        super().__init__(**kwargs)

    def is_cache_invalid(self) -> bool:
        return True

    @CachedMetadata.cached_loadable
    def discussions(self):
        return self._discussions

    @DataContainer.loadable
    def path(self):
        return self._path

    @DataContainer.loadable
    def file_info(self):
        import argparse

        return argparse.Namespace(**self._metadata)

    @DataContainer.loadable
    def valid_loading(self) -> bool:
        return True

    @CachedMetadata.cached_loadable
    def modified_time(self):
        return self._metadata["utc_timestamp"]


def load_virtual_file(path, metadata, **kwargs):
    """Load a virtual file from path into the appropriate object type."""
    # Get cached preferred loader
    try:
        obj = VirtualFile(path=path, metadata=metadata, **kwargs)
        return obj
    except RuntimeError as e:
        logger.error(f"Cannot load {type(path)}: {type(e)}")
        logger.error(f"Cannot load {path}: {e}")

    raise RuntimeError(f"cannot load remote file: {path}")
