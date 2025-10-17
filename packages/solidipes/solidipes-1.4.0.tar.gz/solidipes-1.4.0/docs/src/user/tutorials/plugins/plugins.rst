.. _user-plugins:

Solidipes plugins
=================

Finding plugins
---------------

Solidipes relies on plugins to extend its support for various data formats and types of curation reports.
A list of official plugins created by the Solidipes developers can be found on `GitLab <https://gitlab.com/solidipes?filter=plugin>`_.
All the plugins, including those created by the community, are also listed on `PyPI <https://pypi.org/search/?q=solidipes+plugin>`_. By default, only the `core plugin <https://pypi.org/project/solidipes-core-plugin/>`_ is installed, providing support for the most common file types and essential curation reports.


Plugin management
-----------------

To install, update, or remove a plugin, you can use the ``pip`` command in the terminal.
Alternatively, you can manage plugins directly from the Solidipes :ref:`web interface <starting-the-webreport>` by clicking the "Manage plugins" button, located at the top left of the welcome screen, or in the sidebar.

.. image:: plugin_management_button.png
    :width: 700

.. image:: plugin_management_button_sidebar.png
    :width: 400


Plugin development
------------------

If you don't find a plugin that meets your needs, you can create your own plugin. Head over to the :ref:`developer guide <developer-guide>` section to learn how to :ref:`create your own plugin <create-plugin>`.
