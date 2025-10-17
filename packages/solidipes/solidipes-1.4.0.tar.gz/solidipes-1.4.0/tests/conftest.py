import os
import sys
from pathlib import Path
from typing import Generator

import pytest

import solidipes as sp
from solidipes.scripts.init import main as init

sys.path.append(os.path.join(os.path.dirname(__file__), "helpers"))


@pytest.fixture(scope="function")
def study_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Setup a temporary directory with solidipes initialized."""

    class Args:
        directory = str(tmp_path)
        force = None

    args = Args()
    init(args)
    os.chdir(tmp_path)

    yield tmp_path

    sp.close_cached_metadata()


@pytest.fixture
def study_tree(study_dir: Path) -> Path:
    """Create a data directory structure in the study directory.

    data
    ├── subdir1
    │   ├── file1.txt
    │   ├── file2.txt
    │   ├── file4.txt
    │   └── other.txt
    ├── subdir2
    │   ├── subdir3
    │   │   └── file5.txt
    │   └── file6.txt
    └── file7.txt
    """
    data_dir = study_dir / "data"
    data_dir.mkdir()

    subdir1 = data_dir / "subdir1"
    subdir1.mkdir()
    for filename in ["file1.txt", "file2.txt", "file4.txt", "other.txt"]:
        (subdir1 / filename).touch()

    subdir2 = data_dir / "subdir2"
    subdir2.mkdir()
    subdir3 = subdir2 / "subdir3"
    subdir3.mkdir()
    (subdir3 / "file5.txt").touch()
    (subdir2 / "file6.txt").touch()

    (data_dir / "file7.txt").touch()

    return study_dir


@pytest.fixture
def user_path(tmp_path: Path, monkeypatch) -> None:
    """Mock os.path.expanduser."""
    home = tmp_path / "HOME"
    home.mkdir()

    monkeypatch.setattr("os.path.expanduser", lambda path: path.replace("~", str(home)))
