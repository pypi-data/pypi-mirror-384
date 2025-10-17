"""Computational solid mechanics package for loading and visualizing files."""

from importlib.metadata import PackageNotFoundError, version

import lazy_loader as lazy

__getattr__, __dir__, __all__ = lazy.attach(
    __name__,
    [
        "downloaders",
        "loaders",
        "mounters",
        "plugins",
        "reports",
        "scanners",
        "uploaders",
        "utils",
        "validators",
        "viewers",
    ],
    submod_attrs={
        "loaders": ["load_file", "load_groups"],
    },
)


class Loader:
    """Lazy mirror of loaders module, including plugin loaders."""

    @property
    def dict(self) -> dict[str, type]:
        from .loaders.data_container import DataContainer
        from .loaders.file import File
        from .loaders.file_sequence import FileSequence
        from .plugins.discovery import loader_list

        loader_dict = loader_list.as_dict()
        loader_dict.update({
            "DataContainer": DataContainer,
            "File": File,
            "FileSequence": FileSequence,
        })
        return loader_dict

    def __getattr__(self, key):
        return self.dict[key]

    def __dir__(self):
        return list(self.dict.keys())


loader = Loader()


class Viewer:
    """Lazy mirror of viewers module, including plugin viewers."""

    def __getattr__(self, key):
        from .plugins.discovery import viewer_list

        return viewer_list.as_dict()[key]

    def __dir__(self):
        from .plugins.discovery import viewer_list

        return list(viewer_list.as_dict().keys())


viewer = Viewer()


def close_cached_metadata() -> None:
    """Close cached metadata and write RO-Crate file."""
    from solidipes.loaders.rocrate_metadata import ROCrateMetadata

    ROCrateMetadata.close_cached_metadata()


try:
    __version__ = version("solidipes")
except PackageNotFoundError:
    pass
