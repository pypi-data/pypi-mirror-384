import pytest

from solidipes.scripts.main import main_PYTHON_ARGCOMPLETE_OK


def test_main_empty() -> None:
    """Test main with no arguments."""
    with pytest.raises(SystemExit):
        main_PYTHON_ARGCOMPLETE_OK()
