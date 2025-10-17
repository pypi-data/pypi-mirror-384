.. _faq:
Frequently Asked Questions
==========================

Below are some of the frequently asked questions about Solidipes. If you have any other question that is not answered here, please raise an issue on `GitLab <https://gitlab.com/solidipes/solidipes/-/issues>`_ and tag it with the label "question".


What is Solidipes for?
-----------------------

It is a user interface that allows to visualize and upload large data sets for researchers by creating a web interface.

Solidipes curates the data and signals errors in extension incompatibilities, missing headers etc.

The project can then be uploaded onto Zenodo, where other researchers can download the data with the relevant information associated to the data collection.


Is solidipes only available for Linux?
--------------------------------------

It is recommended to use Linux, as other OS have not yet been tested.

In later stages it might get tested for Windows and MacOS.


Is there an upload size limit?
-----------------------------

`Zenodo <https://zenodo.org/>`_ limits the dataset size to 50GB. For larger uploads, you can contact Zenodo directly.


One of my files is loaded as binary
-----------------------------------

When a file format is not recognized by Solidipes, it is loaded as a binary file by default, and displayed as such.
The list of existing Loaders and their associated supported file types are listed in the :ref:`developer <developer-guide>` section. If you wish to write custom Loaders and Viewers for your own file types, please refer to the :ref:`developer <developer-guide>` section.
