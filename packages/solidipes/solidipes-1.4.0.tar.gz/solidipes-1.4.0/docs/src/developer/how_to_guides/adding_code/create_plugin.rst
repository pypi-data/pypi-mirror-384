.. _create-plugin:

Create a Solidipes plugin
=========================

To create a new plugin, you can use the `Solidipes plugin template <https://gitlab.com/solidipes/solidipes-plugin-template>`_ repository as a starting point, and follow the instructions in the README. It is possible to implement :ref:`custom Loaders <create-new-loader>`, :ref:`Viewers <create-new-viewer>`, :class:`Uploaders <solidipes.uploaders.uploader.Uploader>`, :class:`Downloaders <solidipes.downloaders.downloader.Downloader>`, and :class:`Reports <solidipes.reports.report.Report>`, that will all be automatically integrated into the Solidipes workflow when the plugin is installed.


Install a plugin
----------------

To install and use a plugin that is on your local machine, you can use the following command::

  pip install -e <path-to-plugin>

The package will be automatically detected by Solidipes as a plugin.

For plugins that are published on a git repository::

  pip install git+<https-url>

To install a plugin from a specific branch::

  pip install git+<https-url>@<branch-name>

Finally, to install a plugin that is published on PyPI::

  pip install <plugin-name>

All of these actions can also be done from the web interface.


Add a plugin as a Solidipes submodule
-------------------------------------

To integrate a plugin to the test suite of Solidipes, run the following command from the root of the Solidipes repository::

  git submodule add <https-url> plugins/<plugin-short-name>
