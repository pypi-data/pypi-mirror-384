.. _getting-started:

Getting Started
===============

This page will help you quickly get started with the Solidipes package. The steps are the following:

1. :ref:`install-n-setup` of the package,

2. :ref:`getting-started-init`,

3. :ref:`getting-started-report`.

For a more in-depth overview of the capabilities of Solidipes, take a look at the :ref:`Tutorials<tutorial>`.


.. _install-n-setup:

Installation and Setup
----------------------

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-installation.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|

Solidipes is currently only tested on Linux. Installation is possible on other platforms, but not all features have been fully tested. For Windows users, we recommend using `WSL <https://learn.microsoft.com/en-us/windows/wsl/install>`_. The installation instructions below are only for Linux.

You need to have **Python** installed on your system to install and uses Solidipes (minimum Python 3.10).


Installation using uv
"""""""""""""""""""""

The easiest way to install Solidipes in an isolated environment is to use the Python package and project manager `uv <https://docs.astral.sh/uv/>`_. After `installing uv <https://docs.astral.sh/uv/getting-started/installation/>`_, simply run the following command:
::

    uv tool install solidipes


Manually creating a Virtual Environment
"""""""""""""""""""""""""""""""""""""""

If you are not installing Solidipes using uv, we strongly recommend creating a virtual environment to avoid conflicts with Python packages already present on your system.

- :ref:`Using venv <venv-env>` (all Python installations)

- :ref:`With Anaconda <create-conda-environment>`

Once you have created and activated your environment, you can proceed to install your Solidipes package.

Installing Solidipes using pip
""""""""""""""""""""""""""""""

Run the following command to install Solidipes in the current Python environment:
::

    pip install solidipes


Enabling command auto-completion (Optional)
-------------------------------------------

If you plan on using the Solidipes command in a terminal, we recommend enabling auto-completion. If you are using *bash* or *zsh* as your shell, you can enable <Tab> completion for the ``solidipes`` command by running::

    solidipes install-completion

You may need to run this command with the ``--user`` or the ``--sudo`` flag.
::

    solidieps install-completion --user
    # or
    solidipes install-completion --sudo

.. _getting-started-init:

Initializing a Solidipes project
--------------------------------

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-initialise.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|

To prepare a new Solidipes project, run the following command in the root of your project directory::

    solidipes init

This will create some files and directories in the root of your project directory:

- a ``.solidipes`` directory, which contains metadata about your project and files

- a ``DESCRIPTION.md`` file, which contains a description of your project

- an automatically generated ``README.md`` file, filled with the metadata and description of your project

The easiest way to edit your project's metadata and curate your data is to use the web interface. If you wish to do so manually using the command line, refer to the :ref:`User reference<reference>`.

.. _getting-started-report:

Launching the web interface
---------------------------

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-web-overview.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|

Run the command::

    solidipes report web-report

and click on the displayed link to open a web interface in your Browser. There, you can edit your project's metadata, curate your data, and publish your project to Zenodo.
