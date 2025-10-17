import atexit
from typing import Literal, Optional, TypeVar, Union

from rocrate.model.dataset import Dataset as ROCrateDataset
from rocrate.model.file import File as ROCrateFile
from rocrate.rocrate import ROCrate

from .data_container import DataContainer
from .cached_metadata import CachedMetadata, ObservableDict, cached_loadable
from ..utils import logging
from ..utils.utils import compute_checksum, get_study_root_path, transform_data_containers_to_dict

print = logging.invalidPrint
logger = logging.getLogger()


class ROCrateProxy:
    def __init__(self) -> None:
        """RO-Crate crate object proxy."""
        self._crate: Optional[ROCrate] = None

    @property
    def crate(self) -> ROCrate:
        if self._crate is not None:
            return self._crate

        try:
            self._crate = ROCrate(get_study_root_path())
        except ValueError:  # Not a valid RO-Crate: missing ro-crate-metadata.json
            logger.info("RO-Crate metadata file missing or invalid, creating a new one")
            self._crate = ROCrate()

        return self._crate

    def write_json(self) -> None:
        import os

        try:
            study_root_path = get_study_root_path()
        except FileNotFoundError:
            return

        logger.debug(f"Writing RO-Crate metadata {study_root_path}")

        previous_checksum = None
        previous_access_time = None
        previous_modification_time = None
        metadata_filepath = os.path.join(study_root_path, "ro-crate-metadata.json")
        if os.path.exists(metadata_filepath) and os.path.isfile(metadata_filepath):
            previous_checksum = compute_checksum(metadata_filepath)
            stats = os.lstat(metadata_filepath)
            previous_access_time = stats.st_atime
            previous_modification_time = stats.st_mtime

        not_ok = True
        while not_ok:
            try:
                self.crate.write(study_root_path)
                not_ok = False
                if previous_checksum is None:
                    logger.debug(f"Saved RO-Crate metadata {study_root_path}")
                    return
                checksum = compute_checksum(metadata_filepath)
                if checksum != previous_checksum:
                    logger.debug(f"Saved RO-Crate metadata {study_root_path}")
                    return
                os.utime(metadata_filepath, (previous_access_time, previous_modification_time))
            except FileNotFoundError as e:
                logger.error(e)
                import os

                fname = os.path.relpath(e.filename, self.crate.source)
                self.crate.delete(fname)

    def close_crate(self) -> None:
        """Close the RO-Crate crate."""
        self._crate = None

    def __getattr__(self, key: str):
        return getattr(self.crate, key)


rocrate = ROCrateProxy()


class ROCrateMetadataProperty(property):
    """Marker class for RO-Crate metadata properties."""


T = TypeVar("T")


class rocrate_metadata(cached_loadable):
    """Decorator for loadables that are saved as RO-Crate metadata."""

    def wrapped_fget(self, obj):
        data = super().wrapped_fget(obj)

        value = data

        if isinstance(value, ObservableDict):
            value = value._data

            def callback():
                value = getattr(obj, self.key, None)
                if isinstance(value, ObservableDict):
                    value = value._data
                value = transform_data_containers_to_dict(value)
                obj.additional_metadata[self.key] = value
                obj.save_field_to_cache(self.key)

            data = ObservableDict(value, callback=callback)

        value = transform_data_containers_to_dict(value)
        obj.additional_metadata[self.key] = value

        return data

    def wrapped_fset(self, obj, value) -> None:
        super().wrapped_fset(obj, value)
        obj.additional_metadata[self.key] = value


class ROCrateMetadata(CachedMetadata):
    """RO-Crate metadata."""

    rocrate_metadata = rocrate_metadata

    def __init__(self, *args, **kwargs) -> None:
        self._rocrate_type: Literal["dataset", "directory", "file"] = "file"
        self._rocrate_entity: Optional[Union[ROCrateDataset, ROCrateFile]] = None
        super().__init__(*args, **kwargs)

    def update_cached_metadata(self) -> None:
        self._load_rocrate_metadata()
        super().update_cached_metadata()

    def _load_rocrate_metadata(self) -> None:
        """Load field from RO-Crate metadata file if not already loaded from cache."""

        cls = self.__class__
        rocrate_metadata_from_file = self.get_rocrate_entity().properties()

        for attribute_name in dir(cls):
            attribute = getattr(cls, attribute_name)

            if not isinstance(attribute, rocrate_metadata):
                continue

            value = self._data_collection.get(attribute_name, None)

            if value is None:
                # Try to get value from RO-Crate metadata file
                value = rocrate_metadata_from_file.get(attribute_name, None)

            if value is None:
                continue

            if isinstance(value, ObservableDict):
                value = value._data

            if isinstance(value, dict) or isinstance(value, DataContainer):

                def callback():
                    value = getattr(self, attribute_name, None)
                    if isinstance(value, ObservableDict):
                        value = value._data
                    value = transform_data_containers_to_dict(value)
                    self.additional_metadata[attribute_name] = value
                    self.save_field_to_cache(attribute_name)

                value = ObservableDict(value, callback=callback)

            self.add(attribute_name, value)

    def get_rocrate_entity(self) -> Union[ROCrateDataset, ROCrateFile]:
        if self._rocrate_entity is None:
            self._rocrate_entity = rocrate.get(self.unique_identifier.replace("\\", "/"))

        if self._rocrate_entity is None:
            rocrate_add_method = getattr(rocrate, f"add_{self._rocrate_type}")
            self._rocrate_entity = rocrate_add_method(self.path, dest_path=self.unique_identifier)

            for attr in dir(self.__class__):
                if isinstance(getattr(self.__class__, attr), ROCrateMetadataProperty):
                    _ = getattr(self, attr)  # Trigger adding default value

        return self._rocrate_entity

    @property
    def additional_metadata(self) -> ObservableDict:
        return ObservableDict(self.get_rocrate_entity().properties(), lambda: self._schedule_commit())

    @classmethod
    def _commit(cls) -> None:
        """Update RO-Crate metadata file."""
        rocrate.write_json()
        super()._commit()

    @classmethod
    def close_cached_metadata(cls) -> None:
        """Close cached metadata and RO-Crate."""
        super().close_cached_metadata()
        rocrate.close_crate()


atexit.register(ROCrateMetadata.close_cached_metadata)
