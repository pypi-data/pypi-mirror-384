.. data-curation:

Data curation
=============

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-web-curation.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|

In this tutorial only the most common data types will be shown. For more information, see :ref:`ref-curation`.

..
    TO DO: LINK TO REFERENCE SECTION

With a running web report you can see the status of your data.

The most common types of errors reported by solidipes will be illustrated below.

Solidipes checks whether the mime-type corresponds to the extension of the file. (i.e. an image file with a .dat extension will be flagged as an error).

.. image:: curation_overview.png
  :width: 800


Since different file types use different loaders. You must tell solidipes with which loader it should interpret the file when the extension does not match the mime-type.

You can do this by either specifying which extension it should be interpreted as

.. image:: curation_overview2.png
  :width: 800


or by specifying which mime-type it should be interpreted as.

.. image:: curation_overview3.png
    :width: 800

.. attention::
    Changing the actual file extension must be made manually. In the web report you only inform of which loader should be used, but the local filename will remain unmodified.

    After local changes, refresh the webpage, click on the `Force folder scan` button, or run the `web-report` command again.

Aside from the extension and mime-type, solidipes also allows more type-dependent checks.

See here:

    - For :ref:`images<tutorials-image-curation>`

    - For :ref:`tables<tutorials-tables-curation>`

    - For :ref:`pyvista meshes<tutorials-pyvista-curation>`

Data grouping
#############
If you have a set of data with a similar name (i.e. `img1.png`, `img2.png`, `img3.png`, etc.) solidipes will group them together (i.e. `img*.png`).
This is useful, for example, if you have a set of images that are related to each other.
For example, if you have a set of images or tables that are the result of a simulation, you can group them together, so you can use the cursor to visualize your data.

.. attention::
    If one of one dataset of the sequence is missing, solidipes will not warn you, instead it will create two separate groups (i.e. `img1.png`, `img2.png` together and `img10.png` separately).


If you want to see the status of each dataset individually, you can click on the group and it will show you the status for each.

.. image:: img_curation_grouped.png

Here you can see images grouped together, if you do not want this, you must change the names locally.


.. _tutorials-image-curation:

Image curation
##############

The webreport allows you to visualize your images. If the image is corrupted, you will not be able to see it.

.. attention::
    `.gif` and `.tiff` files are shown as individual images grouped together and not as a gifs or tiffs.




.. _tutorials-tables-curation:

Tables curation
###############

When visualizing the tables (`.csv` and `.xlsx` files) you can check for the following:

    - If the file is empty
    - If the file is a valid file
    - If the file is a valid table (i.e. if it has a header and a body)


The table will be visualized in the web report, so you can check if the table is correct.

.. image:: csv_correct.png
    :width: 800

In the following, you can see the same file but with missing headers.

.. image:: csv_corrupt.png
    :width: 800

If you are missing data in your table, the plotting will also be incorrect. You can see this in the following image.

.. image:: csv_missing_data.png
    :width: 800

.. _tutorials-pyvista-curation:

Pyvista mesh curation
#####################

The mesh is visualized in the web report, so you can check if the mesh is correct.

The mesh is composed of the following important parameters:

- *Cells*: The volume within the points. Cells cannot be warped.
- *Points*: Located on the corner of the cells faces. Points can be warped (make sure that the warping is done with the appropriate scale).

.. image:: mesh_params.png
    :width: 800

You can chose an active field (i.e. apply a force to the mesh) and see how the mesh is distorted.

.. image:: mesh_active_fields.png
    :width: 800
