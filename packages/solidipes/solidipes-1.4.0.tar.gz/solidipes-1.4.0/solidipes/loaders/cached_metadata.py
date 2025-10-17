import os
import sched
import time
from typing import Union, NoReturn

import transaction
import ZODB
import ZODB.FileStorage
from BTrees.OOBTree import BTree
from zc.lockfile import LockError

from ..utils import solidipes_logging as logging
from ..utils.config import (
    cached_metadata_polling_interval,
    cached_metadata_polling_tries,
    cached_metadata_save_every,
)
from ..utils.utils import (
    get_config,
    get_config_path,
    set_config,
    transform_data_containers_to_dict,
    transform_dict_to_data_containers,
)
from .data_container import DataContainer

print = logging.invalidPrint
logger = logging.getLogger()


class ObservableDict:
    def __init__(self, data: dict | DataContainer, callback=callable) -> None:
        """Proxy dictionary to trigger a callback (e.g. write cache) on changes."""
        self._data = data
        self._callback = callback

    def __getattr__(self, key):
        return getattr(self._data, key)

    def __getitem__(self, key):
        return self._data[key]

    def __setitem__(self, key, value) -> None:
        self._data[key] = value
        self._callback()

    def __delitem__(self, key) -> None:
        del self._data[key]
        self._callback()

    def __contains__(self, key) -> bool:
        return key in self._data

    def clear(self) -> None:
        self._data.clear()
        self._callback()

    def update(self, data) -> None:
        deleted_keys = set(self._data.keys()) - set(data.keys())

        for key in deleted_keys:
            del self._data[key]

        self._data.update(data)
        self._callback()

    def replace(self, data) -> None:
        """Replace the dictionary with a new one."""
        self._data.clear()
        self._data.update(data)
        self._callback()

    def pop(self, key):
        value = self._data.pop(key)
        self._callback()
        return value

    def items(self):
        return self._data.items()

    def __repr__(self) -> str:
        return repr(self._data)

    def __eq__(self, other):
        return self._data == other


class cached_loadable(DataContainer.loadable):
    """Decorator for loadables that are saved to cache."""

    def wrapped_fset(self, obj, value) -> None:
        super().wrapped_fset(obj, value)
        obj.save_field_to_cache(self.key)


_default_cached_attributes = {}
"List of @cached_loadable in the class"


class CachedMetadata(DataContainer):
    _storage = None
    _transaction_manager = transaction.TransactionManager()
    _global_cached_metadata = None
    _scheduler = sched.scheduler()
    _scheduled_commit = None
    cached_loadable = cached_loadable

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cached_attributes = self._get_default_cached_attributes().copy()
        self.load_cached_metadata()

        for validator_ in self.validators:
            # Set enabled status for new validators missing from cache
            if validator_.name not in self.validator_enabled:
                self.enable_validator(validator_.name)

        self.save_field_to_cache("validator_enabled")

    @cached_loadable
    def validator_enabled(self) -> Union[dict[str, bool], DataContainer]:
        return super().validator_enabled

    def enable_validator(self, name: str) -> None:
        """Enable a specific validator."""
        super().enable_validator(name)
        self.save_field_to_cache("validator_enabled")

    def disable_validator(self, name: str) -> None:
        """Disable a specific validator."""
        super().disable_validator(name)
        self.save_field_to_cache("validator_enabled")

    def _get_default_cached_attributes(self) -> set:
        """Build the list of cached fields from the class description."""
        # Cannot be done on the instance because checking the loadable fields would trigger loading
        cls = self.__class__
        cls_name = self.class_path

        if cls_name in _default_cached_attributes:
            return _default_cached_attributes[cls_name]

        _default_cached_attributes[cls_name] = set()

        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)

            if isinstance(attribute, cached_loadable):
                _default_cached_attributes[cls_name].add(attribute_name)

        return _default_cached_attributes[cls_name]

    def clear_cached_metadata(self, fields=[]) -> None:
        if self.unique_identifier not in self.global_cached_metadata:
            return

        if fields:
            for field in fields:
                if field in self.global_cached_metadata[self.unique_identifier]:
                    del self.global_cached_metadata[self.unique_identifier][field]
            self.update_global_cached_metadata(self.unique_identifier)

        else:
            del self.global_cached_metadata[self.unique_identifier]

    def get_cached_metadata(self):
        if self.unique_identifier not in self.global_cached_metadata:
            self.global_cached_metadata[self.unique_identifier] = {}

        return self.global_cached_metadata[self.unique_identifier]

    @cached_loadable
    def modified_time(self) -> NoReturn:
        raise NotImplementedError

    def is_cache_invalid(self):
        cached_metadata = self.get_cached_metadata()

        # Check if update is necessary
        cache_modified_time = cached_metadata.get("modified_time", 0)
        from .file_sequence import FileSequence

        if isinstance(self, FileSequence):
            modified_time = self.file_info.modified_time
        else:
            modified_time = os.lstat(self.path).st_mtime

        return cache_modified_time < modified_time

    def load_cached_metadata(self):
        """Load cached metadata and put in _data_collection (as attributes)."""
        if self.is_cache_invalid():
            self.update_cached_metadata()

        cached_metadata = self.get_cached_metadata()
        # Update _data_collection
        for key, value in cached_metadata.items():
            value = transform_dict_to_data_containers(value)
            if isinstance(value, dict) or isinstance(value, DataContainer):
                value = ObservableDict(value, callback=lambda: self.save_field_to_cache(key))
            self.add(key, value)
            self.cached_attributes.add(key)

        return cached_metadata

    def update_cached_metadata(self) -> None:
        """Update cached metadata with instance's fields listed in cached_attributes."""
        cached_metadata = self.get_cached_metadata()
        for key in self.cached_attributes:
            try:
                value = getattr(self, key)
                if isinstance(value, ObservableDict):
                    value = value._data
                value = transform_data_containers_to_dict(value)
                cached_metadata[key] = value
            except AttributeError:
                pass

        self.update_global_cached_metadata(self.unique_identifier)

    def set_cached_metadata_entry(self, key, value) -> None:
        cached_metadata = self.get_cached_metadata()
        try:
            cached_metadata[key] = transform_data_containers_to_dict(value)
            value = transform_dict_to_data_containers(value)
        except Exception as e:
            logger.error(e)
            raise e
        if isinstance(value, dict) or isinstance(value, DataContainer):
            value = ObservableDict(value, callback=lambda: self.save_field_to_cache(key))
        self.add(key, value)
        self.cached_attributes.add(key)
        self.update_global_cached_metadata(self.unique_identifier)

    def save_field_to_cache(self, key) -> None:
        cached_metadata = self.get_cached_metadata()
        value = getattr(self, key)
        if isinstance(value, ObservableDict):
            value = value._data
        value = transform_data_containers_to_dict(value)
        cached_metadata[key] = value
        self.cached_attributes.add(key)
        self.update_global_cached_metadata(self.unique_identifier)

    @property
    def global_cached_metadata(self) -> BTree:
        return self.get_global_cached_metadata()

    @staticmethod
    def is_cache_database_locked() -> bool:
        if CachedMetadata._global_cached_metadata is not None:
            return False
        path = get_config_path("cached_metadata_filename")
        if not os.path.exists(path + ".lock"):
            return False

        try:
            return ZODB.FileStorage.FileStorage(path)
        except LockError:
            return True
        return False

    @staticmethod
    def force_unlock() -> None:
        path = get_config_path("cached_metadata_filename")
        if os.path.exists(path + ".lock"):
            os.remove(path + ".lock")

    @staticmethod
    def get_global_cached_metadata() -> BTree:
        if CachedMetadata._global_cached_metadata is None:
            CachedMetadata._init_cached_metadata()

        return CachedMetadata._global_cached_metadata

    @classmethod
    def update_global_cached_metadata(cls, unique_identifier=None) -> None:
        """Update cached metadata dictionary."""
        try:
            if CachedMetadata._global_cached_metadata is None:
                cls._init_cached_metadata()

            if unique_identifier is not None:
                # Indicate to ZODB that dictionnay has been updated
                CachedMetadata._global_cached_metadata[unique_identifier] = cls._global_cached_metadata[
                    unique_identifier
                ]

            cls._schedule_commit()
            CachedMetadata._scheduler.run(blocking=False)

        except transaction.interfaces.TransactionFailedError as err:
            logger.error(err)
            transaction.abort()

    @classmethod
    def _init_cached_metadata(cls, initial_path=".") -> None:
        logger.debug("Loading cached metadata")

        path = get_config_path("cached_metadata_filename", initial_path=initial_path)
        db_file_exists = os.path.exists(path)
        CachedMetadata._storage = cls._get_zodb_file_storage(path)
        db = ZODB.DB(CachedMetadata._storage)
        connection = db.open(CachedMetadata._transaction_manager)
        root = connection.root()

        if "metadata" not in root:
            root["metadata"] = BTree()

        CachedMetadata._global_cached_metadata = root["metadata"]

        if not db_file_exists:
            cls._populate_cached_metadata_from_yaml(initial_path=initial_path)

    @classmethod
    def clear_cache(cls, exclude=[]) -> None:
        if isinstance(exclude, str):
            exclude = [exclude]

        deleted_files = []
        _global_cached_metadata = cls.get_global_cached_metadata()

        for _file, _meta in _global_cached_metadata.items():
            if not os.path.exists(_file):
                deleted_files.append(_file)
            keys = [k for k in _meta if k not in exclude + ["modified_time"]]
            for k in keys:
                del _meta[k]

        logger.info(f"deleted files {deleted_files}")

        for f in deleted_files:
            del _global_cached_metadata[f]
        cls._commit()
        cls.close_cached_metadata()

    @classmethod
    def close_cached_metadata(cls) -> None:
        cls._cancel_scheduled_commit()
        cls._commit()
        if CachedMetadata._storage is None:
            return

        try:
            cls._write_cached_metadata_to_yaml(initial_path=".")
        except Exception as e:
            logger.error(f"Closed cached metadata after exception {e}")
        finally:
            CachedMetadata._storage.close()
            try:
                cls.force_unlock()  # .lock is not removed automatically by _storage.close()
            except Exception:
                pass
            CachedMetadata._storage = None
            CachedMetadata._global_cached_metadata = None

        logger.debug("Closed cached metadata")

    @classmethod
    def _get_zodb_file_storage(cls, path: str) -> ZODB.FileStorage.FileStorage:
        for i in range(cached_metadata_polling_tries):
            try:
                return ZODB.FileStorage.FileStorage(path)
            except LockError:
                logger.debug(f"Could not open cached metadata at {path} ({i + 1} attempts)")
            time.sleep(cached_metadata_polling_interval)

            # import signal
            # import subprocess
            #
            # p = subprocess.Popen(f"lsof {path}", shell=True, stdout=subprocess.PIPE)
            # p.wait()
            # pids = p.stdout.read().decode()
            # pids = pids.split('\n')[1:]
            # pids = [p for p in pids if p != '']
            # for pid in pids[1:]:
            #     pid = pid.split()[1]
            #     os.kill(int(pid), signal.SIGTERM)
        raise LockError(f"Could not open {path}")

    @classmethod
    def _commit(cls) -> None:
        """Update cached metadata database."""
        if CachedMetadata._global_cached_metadata is None:
            return

        logger.debug("Committing cached metadata")
        CachedMetadata._transaction_manager.commit()
        CachedMetadata._scheduled_commit = None

    @classmethod
    def _schedule_commit(cls) -> None:
        """Schedule later update of metadata database."""
        if CachedMetadata._scheduled_commit is not None:
            return

        CachedMetadata._scheduled_commit = CachedMetadata._scheduler.enter(
            cached_metadata_save_every,
            1,
            cls._commit,
        )

    @classmethod
    def _cancel_scheduled_commit(cls) -> None:
        """Cancel scheduled commit."""
        if CachedMetadata._scheduled_commit is not None:
            CachedMetadata._scheduler.cancel(CachedMetadata._scheduled_commit)
            CachedMetadata._scheduled_commit = None

    @classmethod
    def _populate_cached_metadata_from_yaml(cls, initial_path=".") -> None:
        """Populate cached metadata from YAML file."""
        metadata_all_files = get_config("cached_metadata_yaml_filename", initial_path=initial_path)
        if metadata_all_files == {}:
            return

        logger.info("Populating cached metadata from YAML file. YAML file will no longer be updated!")
        for unique_identifier, metadata in metadata_all_files.items():
            CachedMetadata._global_cached_metadata[unique_identifier] = metadata

        cls.update_global_cached_metadata()

    @classmethod
    def _write_cached_metadata_to_yaml(cls, initial_path=".") -> None:
        """Write cached metadata to YAML file."""
        logger.info("Writing cached metadata to YAML file")
        metadata_all_files = {}

        for unique_identifier, metadata in CachedMetadata._global_cached_metadata.items():
            metadata_all_files[unique_identifier] = metadata

        logger.debug(metadata_all_files)
        set_config(
            "cached_metadata_yaml_filename",
            metadata_all_files,
            initial_path=initial_path,
        )
