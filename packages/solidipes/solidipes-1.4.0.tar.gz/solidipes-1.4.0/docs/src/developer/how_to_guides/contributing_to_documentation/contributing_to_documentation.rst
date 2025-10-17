.. _docu-guidelines:
Documentation guidelines
~~~~~~~~~~~~~~~~~~~~~~~~

All new code should be clearly documented. For this, new functions and classes should contain docstrings. The API reference will be automatically generated when building the documentation. From the ``docs`` directory, run::

    make html

which will generate the documentation in the ``build/html`` directory.

.. note::
    In case the documentation does not generate paths correctly you may remove the ``build`` folder
    ::

        rm -rf build

    Then run the following command again to generate a new build
    ::

        make html
