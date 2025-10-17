import os

from ..loaders.virtual_file import load_virtual_file
from ..utils import logging
from .scanner import FileStruct, Scanner  # , cached_scan

################################################################


print = logging.invalidPrint
logger = logging.getLogger()

################################################################


class ScannerDTool(Scanner):
    """A class to scan a distant dtool repository.
    All paths are given relative to the scanner's root path.
    """

    def __init__(self, search_path="./", uri=None) -> None:
        super().__init__(search_path)
        self.uri = uri

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, uri) -> None:
        if isinstance(uri, str) and uri.startswith("dtool:"):
            uri = uri[len("dtool:") :]
        self._uri = uri

    def fill_filepath_tree(self) -> None:
        """Get a tree of all filepaths, organized by directory."""
        from dtoolcore import DataSet  # , EndpointConnectionError

        self.tree = {}

        if self.uri is None:
            raise RuntimeError("FATAL: no uri given to scan")
        dtool_dataset = DataSet.from_uri(self.uri)
        manifest = dtool_dataset.generate_manifest()

        self.entries_files = {}

        for uuid, entry in manifest["items"].items():
            entry["uuid"] = uuid
            fullpath = entry["relpath"]
            dirpath, filepath = os.path.split(fullpath)

            if self.is_excluded(filepath):
                logger.debug(f"Exclude {filepath}")
                continue

            self.add_filepath(
                FileStruct(
                    virtual_root=self.search_path,
                    filepath=filepath,
                    dirpath=dirpath,
                    full_filepath=fullpath,
                    entry=entry,
                    virtual=True,
                    uri=self.uri,
                )
            )

    def get_loader(self, filestruct: FileStruct):
        return load_virtual_file(
            filestruct.filepath,
            filestruct.entry,
            unique_identifier=filestruct.entry["uuid"],
        )
