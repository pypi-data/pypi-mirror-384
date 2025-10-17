.. _sharing-with-renku:
Sharing with Renku
===================

Uploading to Renku
-------------------

Renku is a platform for reproducible and collaborative data science projects.
See their `documentation <https://renku.readthedocs.io/en/stable/index.html>`_ for more information.

You can use Solidipes to easily share your project using a Renku platform, such as `renkulab.io <https://renkulab.io>`_.
Fellow researchers will have access to an online version of the web interface, usually started locally using ``solidipes report``.
Follow the steps below to publish an existing study.

1. Log into the Renku platform of your choice, such as `renkulab.io <https://renkulab.io>`_.

2. Go to the GitLab instance linked to the Renku platform (button on the top right of the screen).

.. image:: gitlab_renku.png
    :width: 400

3. Create a new project by clicking on the "New project" button, and then "Create blank project".
   Put the project name, description, and visibility to your liking.
   In the **Project configuration** section, untick the "Initialize repository with a README", as your Solidipes project already contains one.
   Then, click on "Create project".

.. image:: gitlab_project_conf.png
    :width: 800

4. Retrieve the URL of the project by clicking on the "Clone" button, and copy the URL to the clipboard. You can choose either the ``https`` or the ``ssh`` link. If you choose ``ssh``, you must `add and SSH key <https://docs.gitlab.com/ee/user/ssh.html>`_ to the GitLab configuration.

.. image:: gitlab_url.png
    :width: 400

5. Open a terminal and go to the repository of your project. If not done already, initialize the directory with

.. code-block:: bash

    solidipes init

6. To upload your project to the Renku platform, run

.. code-block:: bash

    solidipes upload renku <URL> solidipes

where ``<URL>`` is the URL you copied in step 4. A few files will be added to your project to allow Renku to run it. You may accept to replace some files existing locally.

A link will be printed in the terminal to access your project on the Renku platform.


Updating a Renku project
-------------------------

You can allow fellow researchers to help you curate your project by `adding them <https://docs.gitlab.com/ee/user/project/members/#add-users-to-a-project>`_ to the list of members of the GitLab repository (at least "Developer" role). They will be able to add comments to your files.


Saving online changes
~~~~~~~~~~~~~~~~~~~~~

To save changes made in the online interface, such as adding comments to a file or changing its type, do the following:

1. In the online web interface, click on the "View/Edit in Jupyterlab" link in the sidebar.

2. In the Jupyterlab interface, open a "Terminal" tab.

3. Commit and push your changes using ``git`` commands:

.. code-block:: bash

    git add .
    git commit -m "message"
    git push


Retrieving changes made online
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To retrieve changes made in the online interface to your local repository, run the following command:

.. code-block:: bash

    git pull renku main


Updating online interface with local changes
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To update the online interface with changes made locally, simply run

.. code-block:: bash

    solidipes upload renku

If other changes were made online, you need to first retrieve them (see above).
