Code Overview
=============

Solidipes curation process relies on the following classes:

- :class:`Report <solidipes.reports.report.Report>`
    Defines a script that is callable from the command ``solidipes report``. It would typically use one or several :class:`Validator <solidipes.validators.validator.Validator>` for the curation process. Web based reports rely on :mod:`widgets <solidipes_core_plugin.reports.widgets>`.

    .. inheritance-diagram:: solidipes.reports.report solidipes.reports.curation solidipes_core_plugin.reports.jtcam solidipes_core_plugin.reports.web_report
       :top-classes: solidipes.reports.report.Report
       :parts: 1

- :class:`Validator <solidipes.validators.validator.Validator>`
    Defines series of checks performed on a :class:`Scanner <solidipes.scanners.scanner.Scanner>` or a :class:`DataContainer <solidipes.loaders.data_container.DataContainer>`. Validators can be defined at the dataset level by extending the base class, or at the DataContainer level by using the :func:`@validator <solidipes.validators.validator.validator>` decorator.

    .. inheritance-diagram:: solidipes.validators.validator.Validator solidipes.validators.curation
       :top-classes: solidipes.validators.validator.Validator
       :parts: 1

- :class:`Scanner <solidipes.scanners.scanner.Scanner>`
    Defines a set of methods that scan directories, build a tree of files (or group of files), and allow the application of functions on the elements of the tree. One typical use case it to try to load each element of the tree using one of the :class:`DataContainer <solidipes.loaders.data_container.DataContainer>` classes.

- :class:`DataContainer <solidipes.loaders.data_container.DataContainer>`
    Also referred as ``Loader``. Defines a container for data that allows loading it on demand and applies checks to validate the data in the curation process. One important subclass is the :class:`File <solidipes.loaders.file.File>` class, that is used to load files from disk (specified by their mime-type and extension), and allows caching computed information about the files. The :class:`DataContainer <solidipes.loaders.data_container.DataContainer>` also lists a set of compatible :class:`Viewer <solidipes.viewers.viewer.Viewer>` classes.

    .. inheritance-diagram:: solidipes.loaders.file solidipes.loaders.file_sequence solidipes.loaders.binary solidipes_core_plugin.loaders.code_snippet solidipes_core_plugin.loaders.gnuplot solidipes_core_plugin.loaders.hdf5 solidipes_core_plugin.loaders.image.Image solidipes_core_plugin.loaders.image_sequence solidipes_core_plugin.loaders.matlab solidipes_core_plugin.loaders.notebook solidipes_core_plugin.loaders.pdf solidipes_core_plugin.loaders.python_pickle solidipes.loaders.symlink solidipes_core_plugin.loaders.table solidipes_core_plugin.loaders.text solidipes_core_plugin.loaders.tikz solidipes_core_plugin.loaders.video solidipes_core_plugin.loaders.xml
       :top-classes: solidipes.loaders.group.Group
       :parts: 1

- :class:`Viewer <solidipes.viewers.viewer.Viewer>`
    Defines a viewer for compatible :class:`DataContainer <solidipes.loaders.data_container.DataContainer>` classes. It is used to display data in various :mod:`backends <solidipes.viewers.backends>` (*e.g.* terminal, Jupyter notebook, Streamlit).

    .. inheritance-diagram:: solidipes.viewers.viewer solidipes.viewers.binary solidipes_core_plugin.viewers.code_snippet solidipes_core_plugin.viewers.hdf5 solidipes_core_plugin.viewers.image solidipes_core_plugin.viewers.image_source solidipes_core_plugin.viewers.matlab solidipes_core_plugin.viewers.notebook solidipes_core_plugin.viewers.pdf solidipes_core_plugin.viewers.python_pickle solidipes.viewers.symlink solidipes_core_plugin.viewers.table solidipes_core_plugin.viewers.text solidipes_core_plugin.viewers.video solidipes_core_plugin.viewers.xml
       :top-classes: solidipes.viewers.viewer.Viewer
       :parts: 1


Other dataset management features of Solidipes rely on the following classes:

- :class:`Downloader <solidipes.downloaders.downloader.Downloader>`
    Defines a script that is callable from the command ``solidipes download``.

    .. inheritance-diagram:: solidipes.downloaders.downloader solidipes_core_plugin.downloaders.zenodo
       :top-classes: solidipes.downloaders.downloader.Downloader
       :parts: 1

- :class:`Uploader <solidipes.uploaders.uploader.Uploader>`
    Defines a script that is callable from the command ``solidipes upload``.

    .. inheritance-diagram:: solidipes.uploaders.uploader solidipes_core_plugin.uploaders.renku solidipes_core_plugin.uploaders.zenodo
       :top-classes: solidipes.uploaders.uploader.Uploader
       :parts: 1
