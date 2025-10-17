import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Any, Callable, Optional, Set, Union

from ..loaders.file import File
from ..loaders.group import Group, load_groups
from ..utils import default_ignore_patterns, get_ignore, logging  # get_study_root_path,
from ..utils.progress import ProgressBar, get_progress_bar

################################################################


print = logging.invalidPrint
logger = logging.getLogger()

################################################################


@dataclass
class FileStruct:
    filepath: str
    dirpath: str
    full_filepath: str
    virtual: bool = False
    virtual_root: str = ""
    entry: dict = field(default_factory=dict)
    uri: str = ""
    is_file: bool = True


################################################################


class DictTree(dict):
    def __init__(self, *args, **kwargs) -> None:
        """A nested dictionary that counts the number of leaves under each node."""
        super().__init__(*args, **kwargs)

        # Convert all nested dictionaries to DictTree
        for key, value in self.items():
            if isinstance(value, dict):
                self[key] = self.__class__(value)

        self.count = self.count_leaves()

    def count_leaves(self) -> int:
        """Count the number of leaves in the tree."""
        count = 0

        for value in self.values():
            if isinstance(value, DictTree):
                count += value.count
            else:
                count += 1

        return count

    def flatten(
        self,
        value_func: Callable = lambda value: value,
        keys_join_func: Callable[[list[str]], str] = lambda keys: os.path.join(*keys),
        add_dicts: bool = False,
        dict_func: Callable = lambda _: None,
        keys: list[str] = [],
    ) -> dict:
        """Flatten the tree into a flat dictionary."""
        flattened = {}

        if add_dicts:
            joined_keys = keys_join_func(keys) if len(keys) > 0 else "."
            flattened[joined_keys] = dict_func(self)

        for key, value in sorted(self.items()):
            new_keys = keys + [key]
            joined_keys = keys_join_func(new_keys)

            if isinstance(value, DictTree):
                flattened.update(
                    value.flatten(
                        value_func=value_func,
                        keys_join_func=keys_join_func,
                        add_dicts=add_dicts,
                        dict_func=dict_func,
                        keys=new_keys,
                    )
                )

            else:
                flattened[joined_keys] = value_func(value)

        return flattened

    def filter(
        self,
        value_filter: Callable = lambda _: True,
        keys_join_func: Callable[[list[str]], str] = lambda keys: os.path.join(*keys),
        joined_keys_filter: Callable = lambda _: True,
        keep_empty_dicts: bool = False,
        keys: list[str] = [],
    ) -> "DictTree":
        """Filter the tree based on the values and keys. Both filters must be satisfied."""
        filtered = self.__class__()

        for key, value in sorted(self.items()):
            new_keys = keys + [key]
            joined_keys = keys_join_func(new_keys)

            if isinstance(value, DictTree):
                sub_tree = value.filter(
                    value_filter=value_filter,
                    keys_join_func=keys_join_func,
                    joined_keys_filter=joined_keys_filter,
                    keep_empty_dicts=keep_empty_dicts,
                    keys=new_keys,
                )

                if len(sub_tree) > 0 or keep_empty_dicts:
                    filtered[key] = sub_tree

            elif value_filter(value) and joined_keys_filter(joined_keys):
                filtered[key] = value

        return filtered

    def apply(
        self,
        func: Callable,
    ) -> "DictTree":
        """Apply a function to all values in the tree."""
        applied = self.__class__()

        for key, value in self.items():
            if isinstance(value, DictTree):
                applied[key] = value.apply(func)
            else:
                applied[key] = func(value)

        return applied

    def reduce(
        self,
        func: Callable,
        initial: Any,
    ) -> Any:
        """Reduce the tree to a single value."""
        acc = initial

        for value in self.values():
            if isinstance(value, DictTree):
                acc = value.reduce(func, acc)
            else:
                acc = func(acc, value)

        return acc


Loader = Union[File, Group]
LoaderTree = DictTree  # dict[str, "LoaderTree | Loader"]


class FilepathTree(DictTree):  # dict[str, "FilepathTree | FileStruct"]"]
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.is_file = False


def cached_scan(func: Callable) -> Callable:
    """Decorator to cache the result of the scan.

    Adds a "force_rescan" parameter to the decorated function.
    Assumes that the result of the scan only depends on search_path and excluded_patterns.
    """

    @lru_cache(maxsize=1)
    def cached_func(self, search_path: str, excluded_patterns: frozenset[str], *args, **kwargs):
        logger.debug(f"Scanning with {func.__name__}")
        return func(self, *args, **kwargs)

    def wrapper(self, *args, force_rescan: bool = False, **kwargs):
        if force_rescan:
            cached_func.cache_clear()

        return cached_func(self, self.search_path, frozenset(self.excluded_patterns), *args, **kwargs)

    return wrapper


class Scanner(ABC):
    """A class to scan a directory to load files and groups.

    All paths are given relative to the scanner's root path.
    """

    def __init__(self, search_path=".", reload_excluded=True) -> None:
        self.search_path = search_path
        self._load_excluded()
        self.reload_excluded = reload_excluded

    def _load_excluded(self) -> None:
        if hasattr(self, "reload_excluded") and self.reload_excluded is False:
            return
        try:
            # Get ignored patterns from .solidipes
            self.excluded_patterns = get_ignore()
        except FileNotFoundError:
            self.excluded_patterns = default_ignore_patterns.copy()

    @cached_scan
    def get_filepath_tree(self) -> FilepathTree:
        """Get a tree of all filepaths, organized by directory.
        relative to the search path.
        """
        self._load_excluded()
        self.tree = {}

        self.fill_filepath_tree()
        return FilepathTree(self.tree)

    def add_subdir(self, dirname, subdir) -> None:
        current_directory = self.get_directory_tree(dirpath=dirname)
        current_directory.update(subdir)

    def add_filepath(self, filestruct: FileStruct) -> None:
        dirpath = filestruct.dirpath
        filepath = filestruct.filepath
        full_filepath = filestruct.full_filepath

        if self.is_excluded(dirpath):
            logger.warning(f"Exclude dirpath {dirpath}")
            return

        if self.is_excluded(filepath):
            logger.warning(f"Exclude filepath {filepath}")
            return

        if self.is_excluded(full_filepath):
            logger.warning(f"Exclude full_filepath {full_filepath}")
            return

        current_directory = self.get_directory_tree(dirpath=dirpath)
        current_directory[filepath] = filestruct

    @abstractmethod
    def fill_filepath_tree(self):
        pass

    def get_directory_tree(self, dirpath=""):
        tree = self.tree

        for dirname in dirpath.split(os.sep):
            if dirname == ".":
                continue

            if dirname not in tree:
                tree[dirname] = {}

            tree = tree[dirname]
        return tree

    @cached_scan
    def get_dirpath_tree(self) -> FilepathTree:
        """Get a tree of all directory paths."""
        return self.get_filepath_tree().filter(
            value_filter=lambda _: False,
            keep_empty_dicts=True,
        )

    @cached_scan
    def get_path_list(self) -> list[str]:
        """Get a list of all paths (files and directories)."""
        return list(
            self.get_filepath_tree()
            .flatten(
                value_func=lambda _: None,
                add_dicts=True,
            )
            .keys()
        )

    @cached_scan
    def get_filepath_list(self) -> list[str]:
        """Get a list of all file paths."""
        return list(
            self.get_filepath_tree()
            .flatten(
                value_func=lambda _: None,
            )
            .keys()
        )

    @cached_scan
    def get_loader_tree(
        self,
    ) -> LoaderTree:
        """Get a tree of loaders, with groups, organized by directory."""
        filepath_tree = self.get_filepath_tree()

        with get_progress_bar("Loading files", total=filepath_tree.count) as progress_bar:
            tree = self.convert_filepath_tree_to_loader_tree(filepath_tree=filepath_tree, progress_bar=progress_bar)
            tree = LoaderTree(tree)

        return tree

    def get_filtered_loader_tree(
        self,
        dirs: list[str] = [],
        recursive: bool = True,
    ) -> LoaderTree:
        """Get a tree of loaders for the given directories."""
        if recursive:

            def path_filter(path: str):
                return any(path.startswith(d) for d in dirs)

        else:

            def path_filter(path: str):
                path = (
                    os.path.dirname(
                        os.path.relpath(
                            path,
                            self.search_path,
                        )
                    )
                    or "."
                )
                return path in dirs

        return self.get_loader_tree().filter(
            joined_keys_filter=path_filter,
        )

    @cached_scan
    def get_loader_dict(self) -> dict[str, Loader]:
        """Get a dictionary mapping paths (potentially grouped) to loaders."""
        return self.get_loader_tree().flatten()

    def get_filtered_loader_dict(self, dirs: list[str] = [], recursive: bool = True) -> dict[str, Loader]:
        """Get a dictionary mapping paths (potentially grouped) to loaders."""
        return self.get_filtered_loader_tree(dirs, recursive=recursive).flatten()

    @cached_scan
    def get_loader_path_list(
        self,
    ) -> list[str]:
        """Get a list of all loaded paths (potentially grouped)."""
        return list(self.get_loader_dict().keys())

    def scan(self) -> None:
        """Trigger the creation of loaders."""
        self.get_loader_tree()

    def is_excluded(self, path: str, excluded_patterns: Optional[Set[str]] = None) -> bool:
        """Check whether the provided path is excluded by any of the scanner's patterns."""
        if excluded_patterns is None:
            excluded_patterns = self.excluded_patterns

        p = Path(path)

        for pattern in excluded_patterns:
            if not pattern.strip():
                continue
            # If the pattern ends with a trailing slash, test whether the path is a directory
            if pattern.endswith("/"):
                if p.match(pattern) and p.is_dir():
                    return True

            # Otherwise, only test whether the path matches the pattern
            else:
                if p.match(pattern):
                    return True

        return False

    @cached_scan
    def get_modified_time(
        self,
    ) -> float:
        """Get the most recent modified time of all files."""
        return self.get_filepath_tree().reduce(
            func=lambda acc, value: max(acc, os.path.getmtime(value.full_filepath)),
            initial=0,
        )

    @cached_scan
    def get_total_size(
        self,
    ) -> int:
        """Get the total size of all files."""
        return self.get_filepath_tree().reduce(
            func=lambda acc, value: acc + os.path.getsize(value.full_filepath),
            initial=0,
        )

    def convert_filepath_tree_to_loader_tree(
        self,
        filepath_tree: FilepathTree,
        current_dir: str = None,
        progress_bar: Optional[ProgressBar] = None,
    ) -> LoaderTree:
        """Convert a tree of filepaths (relative to search path)
        to a tree of loaders, while detecting file groups.
        """
        if current_dir is None:
            current_dir = "."

        loaders = {}

        if progress_bar is not None:
            progress_bar.update(text=current_dir)

        _dir = os.path.join(self.search_path, current_dir)
        _dir = os.path.normpath(_dir)
        loaded_groups, remaining_files = load_groups(filepath_tree, _dir)
        loaders.update(loaded_groups)

        # Update progressbar for groups
        if progress_bar is not None:
            processed = set(filepath_tree.keys()) - set(remaining_files)
            for key in processed:
                if isinstance(filepath_tree[key], FilepathTree):
                    progress_bar.update(filepath_tree[key].count)
                else:
                    progress_bar.update(1)

        # Load files
        for name, filestruct in filepath_tree.items():
            if not filestruct.is_file:
                continue

            if name not in remaining_files:
                continue

            if progress_bar is not None:
                progress_bar.update(text=os.path.join(current_dir, name))
            loaders[name] = self.get_loader(filestruct)

            if progress_bar is not None:
                progress_bar.update(1)

        # Load subdirectories
        for dirname, filestruct in filepath_tree.items():
            if filestruct.is_file:
                continue

            subdir_tree = filepath_tree[dirname]  # type: ignore
            subdir_search_path = os.path.join(current_dir, dirname)
            subdir_loaders = self.convert_filepath_tree_to_loader_tree(
                filepath_tree=subdir_tree, current_dir=subdir_search_path
            )
            loaders[dirname] = subdir_loaders

        logger.debug(loaders)
        return loaders

    @abstractmethod
    def get_loader(self, filestruct: FileStruct) -> Loader:
        pass


def list_files(found, current_dir=""):
    items = []
    for k, v in found.items():
        full_dir = os.path.join(current_dir, k)
        items.append((full_dir, v))
        if isinstance(v, dict):
            items += list_files(v, current_dir=full_dir)
    return items
