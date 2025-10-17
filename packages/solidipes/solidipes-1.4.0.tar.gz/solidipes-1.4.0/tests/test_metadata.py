import os

import pytest

from solidipes.scripts.init import main as init
from solidipes.utils import generate_readme, get_study_metadata, set_study_metadata

host = "sandbox.zenodo.org"
study_id = 123456
test_file_name = "test.txt"
test_zip_name = "test.zip"


@pytest.fixture
def study_dir(tmp_path):
    """Setup a temporary directory with solidipes initialized."""

    class Args:
        directory = str(tmp_path)
        force = None

    args = Args()
    init(args)
    os.chdir(tmp_path)

    return tmp_path


def test_metadata_description(study_dir) -> None:
    metadata = get_study_metadata(study_dir)
    assert metadata["description"] == ""

    # Modify description in DESCRIPTION.md
    description = "test description"
    description_path = study_dir / "DESCRIPTION.md"
    description_path.write_text(description)
    # Test if metadata is updated
    metadata = get_study_metadata()
    assert metadata["description"] == description
    # Same with md to html conversion
    metadata = get_study_metadata(md_to_html=True)
    assert metadata["description"] == f"<p>{description}</p>"

    # Modify DESCRIPTION.md using set_metadata
    description = "test description 2"
    # Test if DESCRIPTION.md is updated
    metadata["description"] = description
    set_study_metadata(metadata)
    assert description_path.read_text() == description
    # Same with html to md conversion
    metadata["description"] = f"<p>{description}</p>"
    set_study_metadata(metadata, html_to_md=True)
    assert description in description_path.read_text()


def test_readme_generation(study_dir) -> None:
    generate_readme()
