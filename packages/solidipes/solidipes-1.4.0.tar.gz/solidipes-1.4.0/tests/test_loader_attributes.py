import os

import pytest
from PIL import Image
from solidipes_core_plugin.loaders.image_sequence import ImageSequence
from solidipes_core_plugin.loaders.text import Text
from solidipes_core_plugin.viewers.image import Image as ImageViewer
from solidipes_core_plugin.viewers.text import Text as TextViewer

import solidipes as sp
from solidipes.loaders.cached_metadata import ObservableDict
from solidipes.loaders.file import File
from solidipes.loaders.file_sequence import FileSequence


@pytest.fixture
def temp_file(study_dir):
    """Create a temporary file in a directory with solidipes initialized."""
    file_name = "test_file.txt"
    file_path = os.path.join(study_dir, file_name)

    # Create empty file
    with open(file_path, "w") as f:
        f.write("")

    return file_path


@pytest.fixture
def temp_file_sequence(study_dir):
    """Create a temporary file sequence in a directory with solidipes initialized."""
    file_count = 3
    file_names = [f"test_file_{i}.txt" for i in range(file_count)]
    file_paths = [os.path.join(study_dir, file_name) for file_name in file_names]

    # Create empty files
    for file_path in file_paths:
        with open(file_path, "w") as f:
            f.write("")

    return file_paths


@pytest.fixture
def temp_image_sequence(study_dir):
    """Create a temporary image sequence in a directory with solidipes initialized."""
    file_name = "image_sequence.tiff"
    file_path = os.path.join(study_dir, file_name)

    frame_count = 3
    width = 1
    height = 1

    images = []

    for i in range(frame_count):
        images.append(Image.new("RGB", (width, height)))

    images[0].save(
        file_path,
        save_all=True,
        append_images=images[1:],
        format="TIFF",
    )

    return file_path


def test_file_attributes(temp_file) -> None:
    """Check File attributes."""
    # Create File object
    file = File(temp_file)

    # Check attributes
    file_info = file.file_info
    assert isinstance(file_info, ObservableDict)
    assert file_info.size is not None
    assert file.unique_identifier == "test_file.txt"


def test_cached_metadata(temp_file) -> None:
    """Test cached metadata saving and loading."""
    # Load file and check that metadata is empty
    file = File(temp_file)
    metadata_key = "test_metadata"
    with pytest.raises(KeyError):
        file.get(metadata_key)

    # Write metadata
    metadata_value = "test_value"
    file.set_cached_metadata_entry(metadata_key, metadata_value)
    assert file.get(metadata_key) == metadata_value

    # Load file again and check that metadata is still there
    file_2 = File(temp_file)
    assert file_2.get(metadata_key) == metadata_value

    # Close metadata cache and check that metadata is still there
    sp.close_cached_metadata()
    file_3 = File(temp_file)
    assert file_3.get(metadata_key) == metadata_value


def test_cached_metadata_dict(temp_file) -> None:
    """Test cached metadata saving and loading with a dictionary attribute."""
    # Load file and check that metadata is empty
    file = File(temp_file)
    metadata_key = "test_metadata"
    with pytest.raises(KeyError):
        file.get(metadata_key)

    # Write metadata
    metadata_value = {"key": "value"}
    file.set_cached_metadata_entry(metadata_key, metadata_value.copy())
    assert file.get(metadata_key) == metadata_value

    # Modify metadata dictionary
    metadata_value["key"] = "updated_value"
    metadata_value["new_key"] = "new_value"
    file.get(metadata_key)["key"] = "updated_value"
    file.get(metadata_key)["new_key"] = "new_value"
    assert file.get(metadata_key) == metadata_value

    # Load file again and check that metadata is still there
    file_2 = File(temp_file)
    assert file_2.get(metadata_key) == metadata_value

    # Close metadata cache and check that metadata is still there
    sp.close_cached_metadata()
    file_3 = File(temp_file)
    assert file_3.get(metadata_key) == metadata_value


def test_cached_attributes(temp_file, temp_file_sequence) -> None:
    """Tests that cached_metadata_fileds are correctly set in CachedMetadata daughter classes."""
    file = File(temp_file)
    assert file.cached_attributes.issuperset({
        "archived_discussions",
        "discussions",
        "file_info",
        "modified_time",
        "preferred_loader_name",
        "preferred_viewer_name",
        "validator_enabled",
    })

    file_sequence = FileSequence("test_file_*.txt", temp_file_sequence)
    assert file_sequence.cached_attributes.issuperset({
        "modified_time",
        "validator_enabled",
    })


def test_change_preferred_viewer(temp_file) -> None:
    """Test changing the preferred viewer of a file."""
    file = Text(path=temp_file)
    assert file.preferred_viewer_name == "solidipes_core_plugin.viewers.text.Text"
    assert file.preferred_viewer == TextViewer

    # Change preferred viewer
    file.preferred_viewer = ImageViewer
    assert file.preferred_viewer_name == "solidipes_core_plugin.viewers.image.Image"
    assert file.preferred_viewer == ImageViewer

    # Close metadata cache and check that preferred viewer is still changed
    sp.close_cached_metadata()
    file_2 = Text(path=temp_file)
    assert file.preferred_viewer_name == "solidipes_core_plugin.viewers.image.Image"
    assert file_2.preferred_viewer == ImageViewer

    # Change preferred viewer by name
    file_2.preferred_viewer_name = "solidipes_core_plugin.viewers.text.Text"
    assert file_2.preferred_viewer_name == "solidipes_core_plugin.viewers.text.Text"
    assert file_2.preferred_viewer == TextViewer

    # Close metadata cache and check that preferred viewer is still changed
    sp.close_cached_metadata()
    file_3 = Text(path=temp_file)
    assert file_3.preferred_viewer_name == "solidipes_core_plugin.viewers.text.Text"
    assert file_3.preferred_viewer == TextViewer


def test_file_sequence_attributes(temp_file_sequence) -> None:
    """Test FileSequence attributes."""
    file_names = [os.path.basename(file_path) for file_path in temp_file_sequence]
    pattern = file_names[0].replace("0", "*")

    # Create FileSequence object
    file_sequence = FileSequence(pattern, temp_file_sequence)

    # Check attributes of FileSequence
    assert file_sequence._element_count == len(temp_file_sequence)
    assert file_sequence.unique_identifier == "test_file_*.txt"

    # Check attributes of first file
    assert file_sequence.preferred_viewer is not None  # Should be default viewer of first file
    assert file_names[0] in file_sequence.file_info.path

    # Check switching file
    file_sequence.select_file(1)
    assert file_names[1] in file_sequence.file_info.path


def test_image_sequence_attributes(temp_image_sequence) -> None:
    """Test ImageSequence attributes."""
    # Create ImageSequence object
    image_sequence = ImageSequence(path=temp_image_sequence)

    # Check attributes of ImageSequence
    assert image_sequence.n_frames > 0
    assert image_sequence.preferred_viewer == ImageViewer
    assert image_sequence.unique_identifier == "image_sequence.tiff"

    # Check load of first image
    image_0 = image_sequence.image
    assert isinstance(image_0, Image.Image)

    # Check switching image
    image_sequence.select_frame(1)
    image_1 = image_sequence.image
    assert isinstance(image_1, Image.Image)
    assert image_0 is not image_1
