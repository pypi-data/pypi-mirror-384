Publishing Research Data
~~~~~~~~~~~~~~~~~~~~~~~~

`Zenodo <https://zenodo.org/>`_ is a research data sharing platform that allows you to publish and share your research outputs.

..  note::
    if path/to/study is not specified, the root directory of the project will be used

    Since publications on Zenodo are immutable after hitting the "publish" button, you can test the upload by uploading onto Zenodo Sandbox (if you want to upload on Zenodo directly, remove the ``--sandbox`` option).

    Uploads are either made onto a `new deposition` or an `existing deposition` (i.e. a deposition that has already been uploaded onto Zenodo and still in the "draft" state).

.. note::
    Uploading to Zenodo or Zenodo Sandbox require personal token (see: :ref:`zenodo-token`).


With :ref:`solidipes init<solidipes-init>` the ``.solidipes/study_metadata.yaml`` and the ``DESCRIPTION.md`` file are created.


Using ``solidipes upload``
--------------------------

Make sure that you modified the ``.solidipes/study_metadata.yaml`` and the ``DESCRIPTION.md`` file to correspond to your data.

The ``solidipes upload zenodo`` command uploads your project onto `Zenodo <https://zenodo.org/>`_.

For example::

    solidipes upload zenodo path/to/study --sandbox --access_token <your access token> --existing_deposition <your doi>

..  note::
    if path/to/study is not specified, the root directory of the project will be used

    Since publications on Zenodo are immutable after hitting the "publish" button, you can test the upload by uploading onto Zenodo Sandbox (if you want to upload on Zenodo directly, remove the ``--sandbox`` option).

    You can either upload onto a `new deposition` or an `existing deposition` (i.e. a deposition that has already been uploaded onto Zenodo and still in the "draft" state).

.. note::
    Uploading to Zenodo or Zenodo Sandbox requires a personal token (see: :ref:`zenodo-token`).
