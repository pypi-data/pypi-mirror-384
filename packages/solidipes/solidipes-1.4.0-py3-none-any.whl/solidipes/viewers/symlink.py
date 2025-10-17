import streamlit as st

from ..utils import solidipes_logging as logging
from . import backends as viewer_backends
from .viewer import Viewer

logger = logging.getLogger()


class SymLink(Viewer):
    """Viewer for symlinks."""

    def add(self, data, **kwargs) -> None:
        """Add a symlink to the viewer."""
        self.check_data_compatibility(data)

    def show(self) -> None:
        linked_path = (
            self.data_container.linked_file
            if isinstance(self.data_container.linked_file, str)
            else self.data_container.linked_file.unique_identifier
        )

        if viewer_backends.current_backend == "jupyter notebook":
            print(f"Symbolic link to {linked_path}")

        elif viewer_backends.current_backend == "streamlit":
            with st.container():
                if isinstance(self.data_container.linked_file, str):
                    st.markdown(f"Broken symbolic link to '{linked_path}' (file doesn't exist)")
                else:
                    st.markdown(
                        f"Symbolic link to <a href='?page=display_page&file={linked_path}'"
                        f" target='_parent'>{linked_path}</a>",
                        unsafe_allow_html=True,
                    )

        else:  # python
            logger.info(f"Symbolic link to {linked_path}")
