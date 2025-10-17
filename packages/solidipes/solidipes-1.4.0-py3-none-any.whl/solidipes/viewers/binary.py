import streamlit as st
from IPython.display import display

from ..loaders.data_container import DataContainer
from ..utils import solidipes_logging as logging
from . import backends as viewer_backends
from .viewer import Viewer

print = logging.invalidPrint
logger = logging.getLogger()


class Binary(Viewer):
    """Viewer for (unknown) binary."""

    def __init__(self, data=None) -> None:
        self.data = []
        super().__init__(data)

    def add(self, data_container) -> None:
        """Append text to the viewer."""
        self.check_data_compatibility(data_container)

        if isinstance(data_container, DataContainer):
            self.data.append(data_container.file_info)
        else:
            raise RuntimeError("can only handle binary types")

    def show(self) -> None:
        if viewer_backends.current_backend == "jupyter notebook":
            for d in self.data:
                for k, v in d.data.items():
                    display(k, v)

        elif viewer_backends.current_backend == "streamlit":
            with st.container():
                logger.info(self.data)
                for d in self.data:
                    for k, v in d.data.items():
                        st.markdown(f"- {k} : {v}")
        else:  # python
            for d in self.data:
                for k, v in d.data:
                    logger.info(k, k)
