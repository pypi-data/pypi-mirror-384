Creating a Virtual Environment
==============================

Using virtual environments is a great choice for managing Python environments. It allows you to create isolated Python environments for your projects, keeping dependencies separate and avoiding conflicts between packages.

.. _venv-env:
Using venv
----------

Step 1 : Creating a Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Open your Linux terminal and navigate to the root directory of your project. Then, create a new virtual environment by running the following command:

.. code-block:: bash

   python3 -m venv .venv

This will create a new directory named ``.venv`` in your project folder, containing the isolated Python environment.

Step 2: Activating the Virtual Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To activate the virtual environment, run the appropriate activation script depending on your shell. For bash, use:

.. code-block:: bash

   source .venv/bin/activate

After activation, your prompt will change to indicate that the virtual environment is active.

Go back to the :ref:`getting-started` section to carry on with installing `solidipes`!

Step 3 : Deactivating the Virtual Environment (once you are done)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To deactivate the virtual environment and return to your regular system Python, use the ``deactivate`` command:

.. code-block:: bash

   deactivate

After deactivation, your prompt will return to its normal state.

.. _create-conda-environment:
Installing Anaconda and Creating a Conda Environment
----------------------------------------------------

If you encounter any issues, please refer to the `Anaconda documentation <https://docs.anaconda.com/free/anaconda/install/linux/>`_.

Step 1: Install Conda (Linux)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1. Open the terminal. (make sure you are in the home directory by running the ``cd`` command)

2. Download the Anaconda installer for Linux from the Anaconda website::

      wget https://repo.anaconda.com/archive/Anaconda3-2021.05-Linux-x86_64.sh

3. Run the Anaconda installer script::

      bash Anaconda3-2021.05-Linux-x86_64.sh

4. Follow the installer prompts to accept the license agreement and specify the installation location (e.g., ``/home/your_username/anaconda3``).

5. Restart the terminal to apply the changes to your PATH.

Step 2: Create a Conda Environment
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
1. Open the terminal.

2. Create a new Conda environment named ``solidipes-env``::

      conda create --name solidipes-env

3. Activate the newly created environment::

      conda activate solidipes-env

Go back to the :ref:`getting-started` section to carry on with installing `solidipes`!

Step 3 : Deactivating the conda Environment (once you are done)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

To deactivate the conda environment and return to the base environment, use the following command:

.. code-block:: bash

   conda deactivate solidipes-env
