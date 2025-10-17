import os
from pathlib import Path

import pytest
import utils

import solidipes as sp
from solidipes.scanners.scanner import FileStruct

# Imported fixtures
# - study_dir


@pytest.fixture
def text_file(study_dir):
    file_path = utils.get_asset_path("text.txt")
    return sp.load_file(file_path)


def test_load_invalid_path(study_dir) -> None:
    file_path = "invalid_path"

    with pytest.raises(FileNotFoundError):
        sp.load_file(file_path)

    with pytest.raises(RuntimeError):
        sp.loader.File()


def test_load_without_extension(study_dir) -> None:
    file_path = utils.get_asset_path("image")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.Image)
    assert file.file_info.type == "image/jpeg"
    assert not file.is_valid


def test_load_binary(study_dir) -> None:
    file_path = utils.get_asset_path("binary.bin")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.Binary)
    assert file.file_info.size == 100
    assert type(file.text) is str
    assert len(file.text) != 0
    assert not file.is_valid


def test_load_code_snippet(study_dir) -> None:
    file_path = utils.get_asset_path("code.py")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.CodeSnippet)
    assert "Hello World!" in file.text
    assert file.is_valid


def test_load_image_with_exif(study_dir) -> None:
    file_path = utils.get_asset_path("image_with_exif.jpg")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.Image)
    assert file.file_info.type == "image/jpeg"
    assert "ExifVersion" in file.exif_data._data_collection
    assert file.is_valid


def test_load_pdf(study_dir) -> None:
    file_path = utils.get_asset_path("document.pdf")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.PDF)
    assert file.file_info.type == "application/pdf"
    assert file.pdf is not None
    assert file.is_valid


class TestLoadTable:
    def test_csv(self, study_dir) -> None:
        file_path = utils.get_asset_path("table.csv")
        file = sp.load_file(file_path)
        assert isinstance(file, sp.loader.Table)
        assert file.header == "a, b, c"
        assert file.table is not None
        assert file.is_valid

    def test_excel(self, study_dir) -> None:
        file_path = utils.get_asset_path("table.xlsx")
        file = sp.load_file(file_path)
        assert isinstance(file, sp.loader.Table)
        assert file.header == "a, b, c"
        assert file.table is not None
        assert file.is_valid


def test_load_symlink(study_dir) -> None:
    if os.name == "nt":
        pytest.skip("Symlinks are not supported on Windows.")
    file_path = utils.get_asset_path("symlink.txt")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.SymLink)
    assert isinstance(file.linked_file, sp.loader.Text)
    assert file.linked_file.text == "Hello World!\n"
    assert file.is_valid


def test_load_text(text_file) -> None:
    assert isinstance(text_file, sp.loader.Text)
    assert text_file.text == "Hello World!\n"
    assert text_file.is_valid


def test_load_video(study_dir) -> None:
    file_path = utils.get_asset_path("video.mp4")
    file = sp.load_file(file_path)
    assert isinstance(file, sp.loader.Video)
    assert file.file_info.type == "video/mp4"
    assert file.video is not None
    assert file.is_valid


class TestDataContainerMethods:
    def test_data_info(self, text_file) -> None:
        """Test data_info method."""
        data_info = text_file.data_info
        assert type(data_info) is str
        assert len(data_info) != 0
        assert text_file.is_valid

    def test_data(self, text_file) -> None:
        """Test data method."""
        data = text_file.data
        assert type(data) is dict
        # Test that accessing ".data" loads loadables
        assert data["text"] == "Hello World!\n"
        assert text_file.is_valid


def test_file_sequence_detection() -> None:
    # Test node without sequence
    is_dir_path_dict = {
        "file1.txt": False,
        "other1.txt": False,
        "directory1": True,
        "directory2": True,
    }
    groups = sp.loader.FileSequence._find_groups(is_dir_path_dict)
    assert groups == {}

    # Test node with sequences
    is_dir_path_dict = {
        "file1.txt": False,
        "file2.txt": False,
        "file3.txt": False,
        "other1.txt": False,
        "other2.txt": False,
        "other10.txt": False,
        "directory1": True,
        "directory2": True,
    }
    groups = sp.loader.FileSequence._find_groups(is_dir_path_dict)
    assert groups == {
        "file*.txt": ["file1.txt", "file2.txt", "file3.txt"],
        "other*.txt": ["other1.txt", "other2.txt", "other10.txt"],
    }


def test_load_file_sequence(study_tree: Path) -> None:
    # Test node without sequence
    node = study_tree / "data"
    names = os.listdir(study_tree)
    filepath_tree = dict([
        (
            name,
            FileStruct(
                filepath=name,
                dirpath="./data",
                full_filepath=os.path.join(node, name),
                is_file=os.path.isfile(os.path.join(node, name)),
            ),
        )
        for name in names
    ])
    root_path = str(node)

    loaded_groups, remaining_is_dir_path_dict = sp.load_groups(filepath_tree, root_path)

    assert loaded_groups == {}
    assert remaining_is_dir_path_dict == [e for e in filepath_tree]

    # Test node with sequence
    node = study_tree / "data" / "subdir1"
    names = os.listdir(node)

    filepath_tree = dict([
        (
            name,
            FileStruct(
                filepath=name,
                dirpath="./data/subdir1",
                full_filepath=os.path.join(node, name),
                is_file=os.path.isfile(os.path.join(node, name)),
            ),
        )
        for name in names
    ])

    root_path = str(node)

    loaded_groups, remaining_is_dir_path_dict = sp.load_groups(filepath_tree, root_path)

    assert len(loaded_groups) == 1
    assert "file*.txt" in loaded_groups
    assert isinstance(loaded_groups["file*.txt"], sp.loader.FileSequence)
    assert remaining_is_dir_path_dict == ["other.txt"]
