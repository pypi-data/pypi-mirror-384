import os
import re

from rocrate.model.dataset import Dataset as ROCrateDataset

from ..utils import get_path_relative_to_root
from .cached_metadata import CachedMetadata
from .rocrate_metadata import ROCrateMetadata
from .file import load_file
from .group import Group
from .rocrate_metadata import rocrate
from .sequence import Sequence
from ..utils import solidipes_logging as logging


logger = logging.getLogger()


class FileSequence(Sequence, ROCrateMetadata, Group):
    """Sequence of files."""

    _compatible_viewers = []

    def __init__(self, pattern, paths=None) -> None:
        if paths is None:
            cached_metadata = CachedMetadata.get_global_cached_metadata()
            if pattern not in cached_metadata:
                raise RuntimeError("Cache must be filled at least once for sequence to be displayed")
            cache = cached_metadata[pattern]
            paths = cache["paths"]

        self.dirname = os.path.dirname(paths[0])
        self.path = os.path.join(self.dirname, pattern)
        self._paths = paths
        self._element_count = len(paths)
        super().__init__(
            name=self.path,
            paths=paths,
            pattern=pattern,
            unique_identifier=get_path_relative_to_root(self.path),
        )
        self._rocrate_type = "dataset"
        self._set_total_size()

        cached_metadata = CachedMetadata.get_global_cached_metadata()
        # import streamlit as st

        if self.path not in cached_metadata:
            cached_metadata[self.path] = {}
        cached_metadata[self.path]["paths"] = paths

    @property
    def _element_unique_identifiers(self):
        return [get_path_relative_to_root(path) for path in self._paths]

    def get_rocrate_entity(self) -> ROCrateDataset:
        if self._rocrate_entity is None:
            self._rocrate_entity = rocrate.get(self.unique_identifier)

        if self._rocrate_entity is None:
            rocrate_add_method = getattr(rocrate, f"add_{self._rocrate_type}")
            rocrate_entity = rocrate_add_method(self._paths[0], dest_path=self.unique_identifier)

            for [path, element_unique_identifier] in zip(self._paths, self._element_unique_identifiers):
                if rocrate.get(element_unique_identifier) is not None:
                    continue
                rocrate.crate.add_file(
                    path, dest_path=element_unique_identifier
                )  # Access inner .crate to bypass JSON writing

            rocrate_entity["hasPart"] = [{"@id": id} for id in self._element_unique_identifiers]
            self._schedule_commit()
            self._rocrate_entity = rocrate_entity

        return self._rocrate_entity

    def _set_total_size(self) -> None:
        self.total_size = 0
        for p in self._paths:
            stats = os.stat(p)
            self.total_size += stats.st_size

    @CachedMetadata.cached_loadable
    def modified_time(self):
        return self.file_info.modified_time

    def _load_element(self, n):
        if n < 0 or n >= self._element_count:
            raise KeyError(f"File {n} does not exist")

        path = self._paths[n]
        try:
            return load_file(path)
        except Exception as e:
            import traceback

            logger.error(traceback.format_exc())
            logger.error(e)

    def select_file(self, n) -> None:
        self.select_element(n)

    @property
    def paths(self):
        return self._paths

    @staticmethod
    def _split_numbers(path):
        groups = re.split(r"(\d+)", path)
        if len(groups) > 2:
            prefix = "".join(groups[:-2])
            number = groups[-2]
            suffix = groups[-1]
            return prefix, number, suffix
        return None

    @staticmethod
    def _find_groups(is_dir_path_dict: dict[str, bool]) -> dict[str, list[str]]:
        filenames = {name for name, is_dir in is_dir_path_dict.items() if not is_dir}
        groups = {}

        # Find sequences
        for filename in filenames:
            _split = FileSequence._split_numbers(filename)
            if _split is None:
                continue

            prefix, _, suffix = _split
            wildcard = prefix + "*" + suffix
            if wildcard not in groups:
                groups[wildcard] = []

            groups[wildcard].append(filename)

        # Remove sequences of length 1
        groups = {wildcard: filenames for wildcard, filenames in groups.items() if len(filenames) > 1}

        # Sort sequences' filenames by number (removing prefix 0s)
        for filenames in groups.values():
            filenames.sort(key=lambda name: int(FileSequence._split_numbers(name)[1]))

        return groups
