import os
from typing import Union

from solidipes.loaders.mime_types import is_valid_extension

from ..validators.validator import add_validation_error, validator
from .file import File, load_file


class SymLink(File):
    """Symbolic link (special file)."""

    from ..viewers.symlink import SymLink as SymLinkViewer

    _compatible_viewers = [SymLinkViewer]  # TODO: to binary or file info

    # TODO: as sequence, if path does not exist, treat as separate file with some infos
    @File.loadable
    def linked_file(self) -> Union[str, File]:
        from pathlib import Path

        _path = str(Path(self.file_info.path).resolve())
        if os.path.exists(_path):
            return load_file(_path)

        return _path

    @validator(description="File's extension matches linked file's mime type")
    def _has_valid_extension(self) -> bool:
        if isinstance(self.linked_file, str):
            add_validation_error(f"Linked file '{self.linked_file}' does not exist")
            return False

        if is_valid_extension(self.file_info.path, self.linked_file.file_info.type):
            return True

        else:
            add_validation_error([
                f"Mime type of linked file '{self.linked_file.file_info.type}' does not match extension"
                f" '{os.path.splitext(self.file_info.path)[1]}'"
            ])
            return False

    @validator(description="Linked file is valid")
    def _is_linked_file_valid(self) -> bool:
        if isinstance(self.linked_file, File):
            return self.linked_file.is_valid

        add_validation_error(f"Linked file '{self.linked_file}' does not exist")
        return False
