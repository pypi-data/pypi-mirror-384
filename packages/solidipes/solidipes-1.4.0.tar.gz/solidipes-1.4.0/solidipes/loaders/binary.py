import os

from datasize import DataSize

from ..validators.validator import add_validation_error, validator
from .file import File


class Binary(File):
    """File of unsupported type."""

    from ..viewers.binary import Binary as BinaryViewer

    _compatible_viewers = [BinaryViewer]

    @File.cached_loadable
    def text(self):
        text = ""
        if self.file_info.type:
            text += f"File type: {self.file_info.type}\n"

        text += f"File size: {DataSize(self.file_info.size):.2a}"
        return text

    @validator(description="File type supported", mandatory=False)
    def _has_valid_extension(self) -> bool:
        add_validation_error([
            f"Unknown extension '{os.path.splitext(self.file_info.path)[1]}' (detected filetype is"
            f" '{self.file_info.type}')"
        ])
        return False
