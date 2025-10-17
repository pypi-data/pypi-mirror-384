.. _publishing-onto-zenodo:
Publishing Project
==================

.. raw:: html

	 <video width="100%" controls>
	 <source src="https://gitlab.renkulab.io/guillaume.anciaux/solidipes-documentation-videos/-/raw/master/data/final_videos/solidipes-web-export.mp4?ref_type=heads&inline=false" type="video/mp4"> Your browser does not support the video tag.</video>

|


Publishing onto Zenodo
^^^^^^^^^^^^^^^^^^^^^^^

`Zenodo <https://zenodo.org/>`_ is a research data sharing platform that allows you to publish and share your research outputs, while associating it with a DOI (Digital Object Identifier). This tutorial will guide you through the process of creating a personal token on Zenodo and uploading your files.

.. attention::
    After upload, the project is still in a **draft state**. Here, both the data and metadata can still be modified.
    However, a **published** project on Zenodo is **immutable** (data cannot be modified nor deleted). Only the metadata can still be modified. If needed, a supplementary version can be uploaded under the same DOI.

    Therefore, for testing, we recommend you publish onto Sandbox Zenodo first. The published project will look the same as on Zenodo (but it will not be permanent).


1. To publish your data from the web interface, go to the **Export** step.

.. image:: select_publish_option.png
    :align: center
    :width: 400

2. Upload onto (Sandbox) Zenodo

.. image:: select_sandbox_option.png
    :width: 800

.. note::
    Since publications on Zenodo are immutable, you can test the upload by uploading onto Zenodo Sandbox.

    The Zenodo Sandbox is a test environment that requires a **separate token**. See here on how to :ref:`create a token<zenodo-token>`.


If you want to use a **new disposition**, you can create a new one by clicking on the *Dont use existing disposition* button.

.. note::
    You can either upload onto a `new deposition` or an `existing deposition` (i.e. a deposition that has already been uploaded onto Zenodo).

3. Submit as draft onto (Sandbox) Zenodo

.. image:: save_draft.png
    :width: 800

4. Review the metadata of the draft on `Zenodo <https://zenodo.org/>`_ (or `Sandbox Zenodo <https://sandbox.zenodo.org/>`_)

To access all of your drafts and publications on Zenodo, click the Uploads menu.

.. image:: zenodo_upload_button.png
    :width: 800

Then select the draft you want to review.

.. image:: select_draft_to_review.png
    :width: 800

.. note::

    You can create as many different drafts as necessary

.. _zenodo-token:
Create a Personal Token
^^^^^^^^^^^^^^^^^^^^^^^

1. **Log in**: Go to the Zenodo website (https://zenodo.org/) or Sandbox Zenodo (https://sandbox.zenodo.org/) for testing and log in to your account (you must create an account if you do not already have one).

2. **Access Settings**: Click on your profile icon in the top right corner and select "Settings" from the dropdown menu.

3. **Personal Tokens**: In the left sidebar, click on "Applications" and then on "Personal access tokens."

4. **Create Token**: Click the "New Token" button.

.. image:: ZenodoTutorial_1new.png
   :width: 800

5. **Token Information**: Provide a name for your token (e.g., "Zenodo Upload Token") and select the desired scopes (permissions to your personal access token). For this tutorial, we will select "Deposit: Write."

.. image:: ZenodoTutorial_2.png
   :width: 800

6. **Generate Token**: Click the "Create Token" button. Your token will be generated. Make sure to copy and store it in a secure place, as you won't be able to see it again.


Congratulations! You've successfully uploaded your research data to Zenodo.

For more information and advanced features, explore the Zenodo documentation at https://help.zenodo.org/.
