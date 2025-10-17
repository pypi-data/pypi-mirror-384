.. _ref-curation:

Data Curation
=============

To share data with the community, we need to make sure that the data is sain.
This means that the data must be saved in the correct format, and should then conform to that format.

For this, solidipes compares the MIME type to the file extension. If the types do not correspond, an error will be raised.

.. attention::
  Currently the command ``solidipes report curation`` does not work. Instead use the webreport to curate your data.


The supported loader formats are:

.. list-table:: supported loader extensions
   :header-rows: 1

   * - Data type
     - Extension
     - Comments
   * - DataContainer
     -
     -
   * - Binary
     -
     - **Default Loader**
   * - Code Snippet
     - ``.py``, ``.cc``, ``.hh``, ``.inp``, ``.m``
     -
   * - File
     -
     -
   * - :ref:`Image<ref-curation-images>`
     - ``.png``, ``.jpeg``, ``.jpg``
     -
   * - Markdown
     - ``.md``
     -
   * - Meshio
     - ``.meshio``
     -
   * - :ref:`PyvistaMesh<ref-curation-pyvistamesh>`
     -
     - ``.vtk``, ``.vtu``, ``.vtp``, ``.ply``, ``.obj``, ``.stl``, ``.gltf``, ``.glb``, ``.3ds``, ``.3d``, ``.xml``, ``.xml.gz``, ``.pvsm``, ``.pvtp``, ``.pvtu``, ``.vtm``, ``.vtmb``, ``.vti``, ``.vtic``, ``.vti.gz``, ``.vtic.gz``, ``.vtu.gz``, ``.vts``, ``.vts.gz``, ``.vtu.gz``, ``.vtp.gz``, ``.vtr``, ``.vtr.gz``
   * - :ref:`Table<ref-curation-tables>`
     - ``.csv``, ``.xlsx``
     -
   * - Text
     - ``.txt``
     -
   * - Video
     - ``.mp4``, ``.avi``, ``.mov``
     - ``.gif`` will be treated as a sequence of images and not as a video

The following types are not supported. This means that they will be loaded as **binary**.

.. list-table:: Unsupported loader extensions examples
   :header-rows: 1

   * - Data Type
     - Extension
   * - Sound
     - `.mp3`, `.wav`, `.ogg`


.. note::
    **Using the command line interface directly:** `(This is not recommended, instead it is recommended to use the webreport)`

    If you give the path for your data directory the command ``solidipes report curation`` will scan all the files in the directory and check the sanity of each file.
    This means that if the file has a wrong extension (i.e. a text file with a .png extension) the program will warn you in the terminal.
    It will also check if the file is empty and if it is not, it will check if the file is a valid file.

    ::

        solidipes report curation /path/to/data/directory

    If you are unsure on how to use the command you can always use the help command::

            solidipes report curation -h

.. _ref-curation-features:
Features
~~~~~~~~
.. list-table:: Features
   :header-rows: 1

   * - Sequence of names of supported data type
     - All data with consecutive names will be grouped together. The group is separated by a missing dataset in the sequence (i.e. ``img1``, ``img2``, ``img10``).
   * - When mime-type and .extension do not match
     - Raises error


.. _ref-curation-tables:

Tables
~~~~~~
.. list-table:: Tables
   :header-rows: 1

   * - Case
     - Comments
   * - Missing Header
     - Incorrect plotting, but no error raised
   * - Missing Data
     - Incorrect plotting, but no error raised
..
  TO DO: add curation tables reference



.. _ref-curation-images:

Images
~~~~~~
.. list-table:: Images
   :header-rows: 1

   * - Case
     - Comments
   * - Single image of supported type
     - The image will be displayed normally
   * - ``.gif``, ``.tiff``
     - Are loaded as consecutive images

..
  TO DO: add curation images reference

.. _ref-curation-pyvistamesh:

PyvistaMesh
~~~~~~~~~~~~~~
.. list-table:: PyvistaMesh
   :header-rows: 1

   * - Case
     - Comments
   * - Cells
     -
   * - Points
     -
..
  TO DO: in construction
