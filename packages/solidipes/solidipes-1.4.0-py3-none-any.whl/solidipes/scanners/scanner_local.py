import os
from typing import Optional, Set

from ..loaders.file import load_file
from ..loaders.virtual_file import load_virtual_file
from ..utils import logging, solidipes_dirname
from .scanner import FileStruct, Scanner  # , cached_scan

################################################################

print = logging.invalidPrint
logger = logging.getLogger()

################################################################


class ScannerLocal(Scanner):
    """A class to scan a directory to load files and groups.

    All paths are given relative to the scanner's root path.
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

    def fill_filepath_tree(self) -> None:
        """Get a tree of all filepaths, organized by directory.
        relative to the search path.
        """
        for root, dirs, files in os.walk(self.search_path):
            dirpath = os.path.relpath(root, self.search_path)
            if self.is_excluded(dirpath):
                logger.warning(f"Exclude {dirpath}")
                dirs.clear()
                continue

            # Add filepaths to the tree
            for fname in files:
                full_filepath = os.path.relpath(os.path.join(dirpath, fname))
                self.add_filepath(FileStruct(filepath=fname, dirpath=dirpath, full_filepath=full_filepath))

    def add_filepath(self, filestruct: FileStruct) -> None:
        name = filestruct.filepath
        fpath = filestruct.full_filepath
        dirpath = filestruct.dirpath
        if name == "cloud_info.yaml":
            cloud_info_text = open(fpath).read()
            import yaml

            cloud_info = yaml.safe_load(cloud_info_text)
            if cloud_info["type"] != "dtool":
                logger.warning(f"Cannot scan unmounted: {fpath}\n{cloud_info_text}")
            else:
                logger.warning(f"Scanning remote dtool: {fpath} => {cloud_info['endpoint']}")
                from .scanner_dtool import ScannerDTool

                sub_scan = ScannerDTool(search_path=dirpath, uri=cloud_info["endpoint"])
                sub_scan.fill_filepath_tree()
                self.add_subdir(dirpath, sub_scan.tree)
        else:
            super().add_filepath(filestruct)

    def get_loader(self, filestruct: FileStruct):
        if not filestruct.virtual:
            return load_file(os.path.join(self.search_path, filestruct.full_filepath))

        return load_virtual_file(
            os.path.join(filestruct.virtual_root, filestruct.filepath),
            filestruct.entry,
            unique_identifier=filestruct.entry["uuid"],
        )


################################################################


class ExportScanner(ScannerLocal):
    """A scanner that keeps the .solidipes directory."""

    "Individual paths inside .solidipes can still be excluded."

    def __init__(self, search_path: str = ".") -> None:
        super().__init__(search_path=search_path)

        if solidipes_dirname in self.excluded_patterns:
            self.excluded_patterns.remove(solidipes_dirname)

    def is_excluded(self, path: str, excluded_patterns: Optional[Set[str]] = None) -> bool:
        """Check whether the provided path is excluded by any of the scanner's patterns."""
        if excluded_patterns is None:
            excluded_patterns = self.excluded_patterns

        # Create a set of excluded patterns specific to the .solidipes directory
        # Typically: removes `.*` from the set of excluded patterns
        if solidipes_dirname in path:
            solidipes_excluded_patterns = set()

            for pattern in excluded_patterns:
                if solidipes_dirname in pattern and pattern != solidipes_dirname:
                    solidipes_excluded_patterns.add(pattern)

        else:
            solidipes_excluded_patterns = excluded_patterns

        return super().is_excluded(path, solidipes_excluded_patterns)
