.. _create-new-viewer:

Create a Viewer
===============

Introduction
------------

To write your custom Viewer, you will subclass the :class:`Viewer <solidipes.viewers.viewer.Viewer>` class, or one of the already existing subclasses that exist in the `solidipes-core-plugin <https://gitlab.com/solidipes/solidipes-core-plugin>`_ package.

Your custom Viewer would typically live in a separate :ref:`Solidipes plugin <create-plugin>` package. If the Viewer is generic enough (not specific to a particular field), it might be added to the `solidipes-core-plugin <https://gitlab.com/solidipes/solidipes-core-plugin>`_ package.

Viewers define different routines depending on the platform Solidipes is running on (Python, Jupyter notebook, or Streamlit web interface). See the example below.


Example
-------

Here is a minimal example of a text Viewer that reads the content of a text file on demand:

.. code-block:: python

    import streamlit as st
    from IPython.display import display
    from solidipes.loaders.data_container import DataContainer
    from solidipes.viewers import backends as viewer_backends
    # Viewer class or subclasses can be imported from solidipes or from other plugins
    from solidipes.viewers.viewer import Viewer


    class Text(Viewer):
        """Viewer for text

        If instanced with data, it will directly display it.
        """

        def __init__(self, data=None):
            #: List of data types (apart from DataContainers) that are compatible with the viewer
            #: DataContainers themselves already declare their compatible Viewers
            self.compatible_data_types = [str]
            #: Text to display
            self.text = ""
            super().__init__(data)

        def add(self, data):
            """Append text to the viewer"""
            self.check_data_compatibility(data)

            if isinstance(data, DataContainer):
                self.text += data.text

            elif isinstance(data, str):
                self.text += data

        def show(self):
            if viewer_backends.current_backend == "jupyter notebook":
                display(self.text)

            elif viewer_backends.current_backend == "streamlit":
                st.text(self.text)

            else:  # python
                print(self.text)
