.. _remotes-rclone:

##########################
 Remote data repositories
##########################

********************
 Rclone integration
********************

Solidipes integrates `Rclone <https://rclone.org/>`_ possibilities to download/upload and even mount remote data repository content.
To install Rclone, follow the instructions on the `Rclone website <https://rclone.org/install/>`_.

#. Listing protocols

      .. code::

         solidipes mount -h
         solidipes download -h
         solidipes upload -h
         rclone config providers

It shows the list of protocols inherited from `rclone`.

.. attention::

   The protocols listed follow the capacities of rclone installed on
   your system.

The examples below are showing the syntax for a webdav server.

2. Downloading from a remote

   .. code::

      solidipes download rclone-webdav --remote tmp-origin https://server/path --user username --password XXXX destination_path

This populates the `destination_path` with the remote content, ready to
be curated. The remote credentials are saved in the rclone config
(`~/.config/rclone/rclone.conf`) under the provided remote name (here
`tmp-origin`), for later use.

2. Upload to a remote

   .. code::

      solidipes upload rclone --remote tmp-origin

This sends back the content to the remote `tmp-origin` (if protocol and
remote allow writing).

3. Mounting

If one wants a subdirectory to live mirrored from a remote, a mount can
be created.

   .. code::

      cd study_dir
      solidipes mount rclone-webdav https://server/path --user username --password XXXX data

will poputate the subdir `data` with the remote content of the webdav
repository. Anytime you can unmount.

   .. code::

      solidipes unmount

which will close the active connection to the remote. To suppress such a

The mount endpoints are kept in the config of Solidipes. You can list
them with:

   .. code::

      solidipes mount --list-existing

to remove definitely an endpoint, and forget the credentials you can do:

   .. code::

      solidipes unmount --forget data
