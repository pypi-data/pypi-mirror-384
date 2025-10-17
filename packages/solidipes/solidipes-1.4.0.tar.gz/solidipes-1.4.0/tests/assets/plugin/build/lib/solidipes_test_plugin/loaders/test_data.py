from solidipes_core_plugin.loaders.text import Text


class TestData(Text):
    """Test file with custom extension."""

    supported_mime_types = {"text/plain": "dat"}
