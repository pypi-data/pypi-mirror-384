import os
import subprocess
from typing import Optional

import filetype
import mimetypes

from ..plugins.discovery import loader_list
from ..utils import get_mimes
from ..utils import solidipes_logging as logging

################################################################


logger = logging.getLogger()


################################################################


def get_mime_type2extensions():
    return loader_list.get_mime_type2extensions()


################################################################


def get_extension2mime_types():
    return loader_list.get_extension2mime_types()


################################################################


def get_possible_extensions(mime):
    mime = mime.split(";")[0]
    try:
        extensions = get_mime_type2extensions()[mime]
    except KeyError:
        return []
    return extensions


################################################################


def get_possible_mimes(ext):
    try:
        mimes = get_extension2mime_types()[ext]
    except KeyError:
        return []
    return mimes


################################################################


def get_extension(path) -> str:
    """Get extension of a file from its path.

    Only returns the last part of the extension. E.g.: "file.tar.gz" -> "gz".
    If the file has no extension, returns an empty string.
    """
    ext = os.path.splitext(path)[1].lower()
    if ext.startswith("."):
        ext = ext[1:]
    return ext


################################################################


def is_valid_extension(path, mime) -> bool:
    mime = mime.split(";")[0]
    for possible_ext in get_possible_extensions(mime):
        # Cannot use get_extension because some possible_ext have multiple
        # parts
        if path.lower().endswith(possible_ext):
            return True

    return False


################################################################


def get_mime_type(path: str) -> tuple[Optional[str], str]:
    """Get mime type of a file.

    Args:
        path (str): path of the file

    Returns:
        str | None: detected mime type
        str: detected charset

    """
    # Get user-defined mime type
    mimes_user_defined = get_mimes()
    if path in mimes_user_defined:
        return mimes_user_defined[path], ""

    # Get mime type from file header
    return guess_mime_type(path)


################################################################


def guess_mime_type(path: str) -> tuple[Optional[str], str]:
    """Guess mime type of a file using its header.

    Args:
        path (str): path of the file

    Returns:
        str | None: detected mime type
        str: detected charset

    """
    try:
        guess = filetype.guess(path)
        mime_type = guess.mime if guess is not None else None

    except FileNotFoundError:  # May happen for broken symlink
        mime_type = None

    except PermissionError:  # Happens on Windaube
        mime_type = None

    if mime_type is None:
        p = subprocess.Popen(f"file --mime --brief {path}", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return_code = p.wait()
        if return_code == 0:
            mime_type = p.stdout.read().decode()

    try:
        mime_type, charset = mime_type.split(";")
        return mime_type, charset
    except Exception:
        pass

    if mime_type is None:
        mime_type, charset = mimetypes.guess_type(path)
        return mime_type, charset or ""

    return mime_type, ""


################################################################


def make_from_text(txt):
    res = {}
    for line in txt.split("\n"):
        if line == "":
            continue
        s = line.split()
        _type = s[0].strip()
        _exts = [e.strip() for e in s[1:]]
        if _type not in res:
            res[_type] = []
        res[_type] += _exts
    return res
