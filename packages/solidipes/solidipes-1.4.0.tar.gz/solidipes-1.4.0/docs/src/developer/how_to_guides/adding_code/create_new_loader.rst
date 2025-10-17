.. _create-new-loader:

Create a Loader
===============

Introduction
------------

To write your custom Loader, you will typically subclass the :class:`File <solidipes.loaders.file.File>` class, or one of the already existing subclasses that exist in the `solidipes-core-plugin <https://gitlab.com/solidipes/solidipes-core-plugin>`_ package. If the files yous want to load are sequences (*e.g.* a ``.gif`` image sequence), you will also subclass the :class:`Sequence` class. That will allow you to access sequence specific methods when visualizing the file. If you want to write a loader for data that is not present in the file system, you may directly subclass :class:`DataContainer <solidipes.loaders.data_container.DataContainer>`. Here is a diagram that show the hierarchy for some Loaders:

.. inheritance-diagram:: solidipes_core_plugin.loaders.image.Image solidipes_core_plugin.loaders.image_sequence
   :parts: 1

Your custom Loader would typically live in a separate :ref:`Solidipes plugin <create-plugin>` package. If the Loader is generic enough (not specific to a particular field), it might be added to the `solidipes-core-plugin <https://gitlab.com/solidipes/solidipes-core-plugin>`_ package. Furthermore, if the Loader enhances the inner workings of Solidipes (*e.g.* by extending or subclassing :class:`DataContainer <solidipes.loaders.data_container.DataContainer>`), it might be added directly in Solidipes to the :mod:`solidipes.loaders <solidipes.loaders>` module.


Example
-------

Here is a minimal example of a text Loader that reads the content of a text file on demand:

.. code-block:: python

    # Loader class or subclasses can be imported from solidipes or from other plugins
    from solidipes.loaders.file import File


    class Text(File):
        """Text file"""

        #: List of supported mime types.
        #: The key is the mime type and the value is one or more file extensions (string or list of strings)
        supported_mime_types = {"text/plain": "txt"}

        def __init__(self, **kwargs):
            # Keep the Viewer imports here to avoid circular imports
            from ..viewers.text import Text as TextViewer

            super().__init__(**kwargs)
            # Specify the compatible viewers for this Loader
            self.compatible_viewers[:0] = [TextViewer]

        # Define attributes loaded on demand with the @File.loadable decorator
        # For attributes that must also be cached by solidipes, use the @File.cached_loadable decorator
        @File.loadable
        def text(self):
            text = ""
            with open(self.file_info.path, "r") as f:
                text = f.read()
            return text
