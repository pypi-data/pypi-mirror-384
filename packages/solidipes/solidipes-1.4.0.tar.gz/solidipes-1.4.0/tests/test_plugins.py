import os
import shutil
from pathlib import Path
from typing import Literal

import pytest
import utils
from solidipes_core_plugin.loaders.text import Text

import solidipes as sp
from solidipes.loaders.binary import Binary
from solidipes.loaders.file import load_file
from solidipes.plugins.discovery import plugin_package_names
from solidipes.plugins.management import install_plugin, loader_list, remove_plugin, reset_plugins


def test_core_loaders() -> None:
    """Test that the core loaders are lazy-loaded."""
    assert Text in loader_list
    assert sp.loader.Text is Text


@pytest.mark.parametrize("editable", ["editable", "site-packages"])
def test_install(study_dir: Path, editable: Literal["editable", "site-packages"]) -> None:
    """Test installation and removal of plugin."""
    plugin_path = utils.get_asset_path("plugin")
    data_path = study_dir / "data"
    file_path = data_path / "text.dat"

    os.makedirs(data_path, exist_ok=True)
    shutil.copy(utils.get_asset_path("text.dat"), file_path)

    # Ensure plugin is not installed
    remove_plugin("solidipes-test-plugin")
    assert "solidipes_test_plugin" not in plugin_package_names

    # Try to load file without plugin
    file = load_file(file_path)
    assert isinstance(file, Binary)

    # Install plugin and try to load file
    install_plugin(plugin_path, editable=True if editable == "editable" else False)
    assert "solidipes_test_plugin" in plugin_package_names
    file = load_file(file_path)
    assert isinstance(file, sp.loader.TestData)

    # Remove plugin. Custom loader is no longer accessible
    remove_plugin("solidipes-test-plugin")
    assert "solidipes_test_plugin" not in plugin_package_names
    file = load_file(file_path)
    assert isinstance(file, Binary)


def test_reference_reload() -> None:
    """Test that lazy loader lists are updated after a plugin reset, while old references ARE NOT."""
    from solidipes_core_plugin.loaders.text import Text as Text1

    assert sp.loader.Text is Text1

    reset_plugins()
    from solidipes_core_plugin.loaders.text import Text as Text2

    assert sp.loader.Text is Text2
    assert Text1 is not Text2
