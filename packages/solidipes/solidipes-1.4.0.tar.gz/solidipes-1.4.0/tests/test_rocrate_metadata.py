import json
import os
import shutil

import pytest
import utils

import solidipes as sp
from solidipes.utils.utils import get_study_root_path

# Imported fixtures
# - study_dir


@pytest.fixture(scope="function")
def text_file(study_dir):
    asset_path = utils.get_asset_path("text.txt")
    file_path = study_dir / "data" / "text.txt"

    os.makedirs(file_path.parent, exist_ok=True)
    shutil.copy(asset_path, file_path)
    return sp.load_file(str(file_path))


def test_get_metadata(text_file) -> None:
    metadata = text_file.additional_metadata
    expected_metadata = {
        "@id": "data/text.txt",
        "@type": "File",
    }
    for key, value in expected_metadata.items():
        assert key in metadata
        assert metadata[key] == value

    # Check written json
    root_path = get_study_root_path()
    rocrate_metadata_path = os.path.join(root_path, "ro-crate-metadata.json")
    text_file._commit()  # Ensure RO-Crate metadata is written
    assert os.path.exists(rocrate_metadata_path)

    with open(rocrate_metadata_path, "r") as f:
        written_metadata = json.load(f)
    assert "@graph" in written_metadata
    assert metadata in written_metadata["@graph"]


def test_new_metadata(text_file) -> None:
    metadata = text_file.additional_metadata
    metadata["hello"] = "world"
    expected_metadata = {
        "@id": "data/text.txt",
        "@type": "File",
        "hello": "world",
    }
    for key, value in expected_metadata.items():
        assert key in metadata
        assert metadata[key] == value

    # Check written json
    root_path = get_study_root_path()
    rocrate_metadata_path = os.path.join(root_path, "ro-crate-metadata.json")
    text_file._commit()  # Ensure RO-Crate metadata is written
    with open(rocrate_metadata_path, "r") as f:
        written_metadata = json.load(f)
    assert metadata in written_metadata["@graph"]

    # Check reloading the file
    sp.close_cached_metadata()
    text_file = sp.load_file("data/text.txt")
    metadata = text_file.additional_metadata
    for key, value in expected_metadata.items():
        assert key in metadata
        assert metadata[key] == value


def test_metadata_modification(text_file) -> None:
    metadata = text_file.additional_metadata
    metadata["hello"] = "world"

    # Reload the file and modify metadata
    sp.close_cached_metadata()
    text_file = sp.load_file("data/text.txt")
    metadata = text_file.additional_metadata
    metadata["hello"] = "modified"

    # Check written json
    root_path = get_study_root_path()
    rocrate_metadata_path = os.path.join(root_path, "ro-crate-metadata.json")
    text_file._commit()  # Ensure RO-Crate metadata is written
    with open(rocrate_metadata_path, "r") as f:
        written_metadata = json.load(f)
    assert metadata in written_metadata["@graph"]

    # Check reloading the file
    sp.close_cached_metadata()
    text_file = sp.load_file("data/text.txt")
    metadata = text_file.additional_metadata
    assert metadata["hello"] == "modified"


def test_existing_rocrate_metadata_retrieval(text_file) -> None:
    # Create RO-Crate metadata file
    text_file.additional_metadata["existing_metadata"] = "value"
    sp.close_cached_metadata()

    # Delete existing cache
    root_path = get_study_root_path()
    for extension in ["fs", "fs.index", "fs.tmp", "yaml"]:
        cache_file = os.path.join(root_path, f".solidipes/metadata.{extension}")
        if os.path.exists(cache_file):
            os.remove(cache_file)

    # Reload the file
    text_file = sp.load_file("data/text.txt")
    metadata = text_file.additional_metadata
    assert "existing_metadata" in metadata
    assert metadata["existing_metadata"] == "value"


def test_discussions(text_file) -> None:
    assert text_file.is_valid
    text_file.add_message("John", "Hello World!")
    assert not text_file.is_valid
    text_file.archive_discussions()
    assert text_file.is_valid

    # Check discussions in RO-Crate metadata
    metadata = text_file.additional_metadata
    assert "discussions" in metadata
    assert metadata["discussions"] == [("John", "Hello World!")]
