Cloud mount
===========

Solidipes can help you work with files stored in the cloud seamlessly, as if they were on your computer.

Setup a directory linked to cloud storage
------------------------------------------

To setup a directory linked to cloud storage, use the ``solidipes mount`` command. For example, to mount a remote directory using SSH, run::

    solidipes mount -p <local-path> ssh <user@host:path>

All types of cloud storage currently supported are listed in :ref:`supported_cloud_storage`.

To unmount a directory, run::

    solidipes unmount -p <local-path>

Mounting information is saved in ``.solidipes/cloud.yaml``. To mount again a directory that has already been mounted before, just run::

    solidipes mount -p <local-path>

without providing any additional information.

Listing current mounts
----------------------

To list all the directories that are mounted or have been mounted at some point and show their mounting status, run::

    solidipes mount -l

Mounting all saved directories
------------------------------

To mount all the directories that have been mounted at some point, run::

    solidipes mount -a

Keys and passwords
------------------

Private connection information, such as keys or passwords, is stored in the user's home directory, in ``~/.solidipes/cloud.yaml``. To save this information in the project directory instead, run the ``mount`` command with the ``-k`` option (or ``--public-keys``). **WARNING**: If you publish your study, the keys will be visible to anyone, and everybody will be able to access you cloud directory (potentially with write access).

Converting a local directory to cloud storage
---------------------------------------------

To move the content of a local directory to cloud storage, insert the ``--convert`` or ``-c`` option in the mount command. For example::

    solidipes mount -p <local-path> -c s3 <endpoint-url...

.. _supported_cloud_storage:

Supported cloud storage
-----------------------

S3
^^

The general command to mount S3 storage is::

    solidipes mount -p <local-path> s3 <endpoint-url> <bucket-name> <access-key-id> <secret-access-key>

By default, mounting S3 storage requires `JuiceFS <https://juicefs.com/docs/community/installation>`_, which must be installed manually. To use `S3FS <https://github.com/s3fs-fuse/s3fs-fuse>`_ instead, run the same command as above with the additional option::

-s s3fs

Unless specified, a directory with a unique random name is created in the cloud storage, and its content is mounted. Private credentials are saved in the user's home directory, in ``~/.solidipes/cloud.yaml``.

SSH
^^^

The general command to mount a remote directory over SSH is::

    solidipes mount -p <local-path> ssh <user@host:path>

The only system implemented to mount SSH storage is SSHFS, which may need to be installed. For example, using ``apt``::

    sudo apt install sshfs

We recommend setting up the SSH connection so that it happens using SSH keys rather than passwords.

NFS
^^^

The general command to mount a remote directory over NFS is::

    solidipes mount -p <local-path> nfs <host:path>

Solidipes uses the ``mount`` command to mount NFS storage. You may need to install the NFS client package. For example, using ``apt``::

    sudo apt install nfs-common

Since the ``mount`` command requires ``sudo`` privileges, you will be asked for your local password for mounting and when unmounting with the ``solidipes unmount`` command.

SMB
^^^

The general command to mount a remote directory over SMB is::

    solidipes mount -p <local-path> smb <//host/path>

If you enter the remote target with backslashes, they will probably need to be escaped as ``\\\\host\\path``. To specify a username, add the option::

-u <username>

Solidipes uses the ``mount`` command to mount SMB storage. On Linux, it uses the LinuxCIFS utils, which may need to be installed, using for example::

    sudo apt install cifs-utils psmisc

As for the NFS type mount, the ``mount`` command requires ``sudo`` privileges. Therefore, you will be asked for your local password for mounting and when unmounting with the ``solidipes unmount`` command.
