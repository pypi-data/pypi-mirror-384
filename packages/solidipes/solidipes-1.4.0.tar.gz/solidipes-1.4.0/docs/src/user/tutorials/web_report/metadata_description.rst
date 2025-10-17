Metadata and Description
========================

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-web-metadata.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|

Modify the metadata
^^^^^^^^^^^^^^^^^^^


.. image:: tutorials_metadata.png
    :width: 800


.. note::
    You can add as many creators and keywords as you deem necessary.

- **Title**: The title of your project.

- **Creators**: The contributors to the project.

    Give their name and their affiliation. The ``orcid`` is optional.

    For example, if you have two creators, you can write:

    .. code::

        - affiliation: EPFL
          name: Toto
          orcid: 0000-0003-3451-7297
        - affiliation: LSMS
          name: Toto Dodo


    .. note::
        - The ``orcid`` is optional. It is a unique identifier for researchers. You can create one here: https://orcid.org/
        - The ``affiliation`` is optional but (highly) recommended.

    .. warning::
        An error will be raised if the indentation is not respected.

- **Keywords**: Should describe your project.

    Adding keywords must respect the following format:

    .. code::

        keyword1, keyword2, keyword3


- **description**: The description of your project. This will be used to generate the ``README.md`` file.
- **upload_type**: The type of upload. For example, ``dataset``.
- **license**: The license under which your data is published. For example, ``cc-by-4.0``.
- **DOI**: If you have already published your project you can add the DOI here. Else a DOI will be generated when you upload your project onto Zenodo.

    .. image:: tutorials_general_metadata.png
        :width: 800

For more information on how to modify the metadata, see here: :ref:`ref-metadata`.

- **additional relations**: You can add additional relations to your project. For example, if you have a paper related to your project, you can add the DOI of the paper here. For more information, see here: :ref:`ref-additional-relations`.

    .. image:: tutorials_additional_relations.png
        :width: 800

    .. warning::
        If you have incomplete relations, the following error will be raised:

        ::
            upload errorError updating deposition metadata: 400 Validation error.

            metadata.related_identifiers.0.identifier: Not a valid persistent identifier. Identifier is required.


Write project description
^^^^^^^^^^^^^^^^^^^^^^^^^

You can directly add the project description. The description should be similar to an abstract.  This will be used to generate the ``README.md`` file when running ``solidipes report`` using the information from your description and the meta data.

.. image:: tutorials_description.png
    :width: 800

For more information on how to write the project description, see here: :ref:`ref-description`.

Additional features of the metadata
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

You can add additional features to your metadata. Check out the reference page for more information: :ref:`ref-additional-features`.
