import os
import tempfile
import uuid
from typing import NoReturn

################################################################
from ..utils import solidipes_logging as logging
from ..utils.config import cloud_connection_timeout
from ..utils.utils import (
    Parsable,
    get_config,
    get_config_path,
    get_path_relative_to_root,
    get_path_relative_to_workdir,
    last_parameter,
    optional_parameter,
    parameter,
    run_and_check_return,
    set_config,
)

################################################################
print = logging.invalidPrint
logger = logging.getLogger()
################################################################


class Mounter(Parsable):
    """Mounter Base class."""

    # list of credential names to remove from public configuration
    credential_names = []

    @property
    def mount_id(self):
        """Create new unique mount_id if not already set."""
        if "mount_id" not in self.mount_info:
            _mount_id = str(uuid.uuid4())
            self.mount_info["mount_id"] = _mount_id
        else:
            _mount_id = self.mount_info["mount_id"]

        return _mount_id

    @mount_id.setter
    def mount_id(self, value):
        """Create new unique mount_id if not already set."""
        self._mount_id = value

    @property
    def mount_info(self):
        if self._mount_info is not None:
            return self._mount_info
        self._mount_info = get_cloud_info(path=self.path)
        self._mount_info["type"] = self.parser_key
        if isinstance(self.parser_key, list):
            self._mount_info["type"] = self.parser_key[0]
        self._mount_info["path"] = self.path

        for k, v in self.__class__.__dict__.items():
            if not isinstance(v, parameter):
                continue

            try:
                val = getattr(self, v.key)
            except ValueError as e:
                info = get_cloud_info(path=self.path)
                val = e
                if k in info:
                    val = info[k]

            if k not in self._mount_info and not isinstance(val, ValueError):
                self._mount_info[k] = val
            elif k not in self._mount_info and isinstance(val, ValueError):
                raise val
            elif self._mount_info[k] != val and not isinstance(val, ValueError):
                self._mount_info[k] = val
            else:
                pass  # the case where the entry is in the mount_info already
        return self._mount_info

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        if self.path is None:
            raise ValueError(f"path is incorrect {self.path}")
        self.path = get_path_relative_to_root(self.path)
        for k, v in kwargs.items():
            if v is not None:
                setattr(self, k, v)
        self._mount_info = None

    @classmethod
    def remove_config(cls, path, config) -> None:
        pass

    def save_config(self) -> None:
        config = get_cloud_info()
        logger.info(f'Saving cloud info for "{self.path}" {self.mount_info}')

        # Save config info if mount is successful
        if self.path not in config:
            config[self.path] = {
                "type": self.mount_info["type"],
                "mount_id": self.mount_id,
            }

            set_cloud_info(config)

        from copy import copy

        mount_info = copy(self.mount_info)
        if not self.store_keys_publicly:
            self.remove_keys_from_info(mount_info)

        remote_fname = os.path.join(self.path, "cloud_info.yaml")
        if not os.path.exists(remote_fname) or self.force:
            # Create directory if it does not exist
            if not os.path.exists(self.path):
                os.makedirs(self.path)

            from ..utils.utils import save_yaml

            logger.debug(remote_fname)
            logger.debug(self.mount_info)
            logger.debug(mount_info)
            save_yaml(remote_fname, mount_info)

    def wait_mount(self) -> None:
        """Wait until the mount is effective."""
        import time

        wait = 0
        while not os.path.ismount(self.path):
            time.sleep(1)
            wait += 1
            if wait > cloud_connection_timeout:
                raise RuntimeError(f'"{self.path}" may not be mounted.')

    @last_parameter
    def path() -> str:
        """Path where to mount. If the directory has already been mounted before,
        there is no need to indicate other mounting parameters."""
        pass

    @optional_parameter
    def store_keys_publicly() -> bool:
        """Save all access keys publicly in local .solidipes directory."""
        "WARNING: when published, everyone will be able to see your "
        "keys and will have full access (possibly write access) to "
        "your mounted directory."

        return False

    @optional_parameter
    def allow_root() -> bool:
        """Allow root to access the fuse mounting."""
        return False

    @optional_parameter
    def force() -> bool:
        """Replace the currently saved configuration for this directory."""
        return False

    def remove_keys_from_info(self, mount_info) -> None:
        """Remove keys from info and generate mount_id if necessary."""
        credential_names = self.credential_names
        if not credential_names:
            return

        # Retrieve user info
        mount_id = self.mount_id
        user_config = get_cloud_info(user=True)

        # Remove keys from current config, and add "removed_keys" entry
        removed_keys = {}

        for key_name in credential_names:
            if key_name in mount_info:
                removed_keys[key_name] = mount_info.pop(key_name)
                if "removed_keys" not in mount_info:
                    mount_info["removed_keys"] = []
                mount_info["removed_keys"].append(key_name)

        # Save keys in user config (if does not already exist)
        if mount_id not in user_config and len(removed_keys) > 0:
            user_config[mount_id] = removed_keys
            set_cloud_info(user_config, user=True)


################################################################


def mount(**kwargs) -> None:
    _type = kwargs["type"]
    mounted = list_mounts(only_mounted=True)
    if "path" not in kwargs:
        logger.error("Path to mount not specified: ignore")
        return

    if kwargs["path"] in mounted:
        logger.warning("Already mounted: ignore")
        return

    if _type is None:
        raise RuntimeError("In order to mount a remote filesystem you need to provide the type")

    logger.info(f"Mounting {kwargs['path']} ({_type})...")
    from solidipes.utils.utils import get_key_to_parsables

    key_to_mounter = get_key_to_parsables("mounters", Mounter)
    mount_type = key_to_mounter[_type]
    mounter = mount_type(**kwargs)
    mounter.save_config()
    mounter.mount()
    mounter.wait_mount()
    logger.info("Mount: Done!")


################################################################


def unmount(path=None, **kwargs) -> None:
    command = ["umount", path]

    if os.path.ismount(path):
        run_and_check_return(command, fail_message="Unmounting failed")
        logger.info(f'Unmounted "{path}"')

    if "forget" in kwargs and kwargs["forget"] is True:
        forget_config(path)


################################################################


def forget_config(path) -> None:
    config = get_cloud_info()
    if path not in config:
        return
    logger.info(f'Forgeting cloud info for "{path}"')
    logger.info(f'Config was "{config[path]}"')
    from solidipes.utils.utils import get_key_to_parsables

    key_to_mounter = get_key_to_parsables("mounters", Mounter)
    mount_type = key_to_mounter[config[path]["type"]]
    mount_type.remove_config(path, config[path])

    del config[path]
    set_cloud_info(config)

    remote_fname = os.path.join(path, "cloud_info.yaml")
    if os.path.exists(remote_fname):
        os.remove(remote_fname)


################################################################


def add_global_mount_info(mount_info) -> None:
    """Use mount_id to retrieve keys from user home's .solidipes directory.

    Keys already present in mount_info are not replaced.
    If one key is not found, no error is raised. Error should happen later when trying to mount.
    """
    if "mount_id" not in mount_info:
        return

    # Retrieve user info
    mount_id = mount_info["mount_id"]
    user_config = get_cloud_info(user=True)

    if mount_id not in user_config:  # and len(missing_keys) > 0:
        logger.debug(f'Mount information for "{mount_id}" not found in user\'s .solidipes directory.')
        return
    user_mount_info = user_config[mount_id].copy()

    user_mount_info.update(mount_info)
    mount_info.update(user_mount_info)
    logger.debug(mount_info)


################################################################


def list_mounts(only_mounted=False):
    """Get config expressed relative to working directory, with mount status."""
    config = get_cloud_info()
    mounts = {}

    mount_point_to_remove = []
    for path in config:
        path_relative_to_workdir = get_path_relative_to_workdir(path)
        is_mounted = os.path.ismount(path_relative_to_workdir)
        mount_info = get_cloud_info(path=path)

        if (not mount_info) and (not is_mounted):
            logger.warning(f"mount point '{path}' lost its config")
            mount_point_to_remove.append(path)
            continue

        mount_info["mounted"] = is_mounted
        if "type" not in mount_info:
            mount_info["type"] = config[path]

        if only_mounted and not is_mounted:
            continue

        mounts[path_relative_to_workdir] = mount_info

    if mount_point_to_remove:
        for path in mount_point_to_remove:
            del config[path]
            set_cloud_info(config)

    return mounts


################################################################


def mount_all(**kwargs) -> None:
    """Mount all mounts that are not already mounted."""
    mounts = list_mounts()
    for path, mount_info in mounts.items():
        if mount_info["mounted"]:
            continue
        logger.info(f"Mounting {path}...")
        try:
            add_global_mount_info(mount_info)
            logger.debug(mount_info)
            mount(**mount_info)
        except Exception as e:
            logger.error(f"Abort after raising {type(e)} {e}")
            raise e

    logger.info("Mount All: Done!")


################################################################


def unmount_all(**kwargs) -> None:
    """Unmount all mounted mounts."""
    mounts = list_mounts(only_mounted=True)
    for local_path in mounts.keys():
        logger.info(f"Unmounting {local_path}...")
        try:
            unmount(path=local_path, **kwargs)
        except Exception as e:
            logger.error(f"{e}")


################################################################


def get_cloud_info(*args, path=None, **kwargs):
    if path is None:
        return get_config("cloud_info_filename", *args, **kwargs)
    from ..utils.utils import load_yaml

    config_fname = os.path.join(path, "cloud_info.yaml")
    if os.path.exists(config_fname):
        return load_yaml(config_fname)
    else:
        return {}


################################################################


def set_cloud_info(config, path=None, *args, **kwargs) -> None:
    set_config("cloud_info_filename", config, *args, **kwargs)


################################################################


def get_cloud_dir_path(*args, **kwargs):
    cloud_dir_path = get_config_path("cloud_dir_name", *args, **kwargs)

    if not os.path.isdir(cloud_dir_path):
        os.makedirs(cloud_dir_path)

    return cloud_dir_path


################################################################
# code to review
################################################################


def convert_cloud_to_cloud(local_path, mount_info_prev, mount_info_new) -> NoReturn:
    raise NotImplementedError("Not implemented. Please convert to local first.")


################################################################


def convert_local_to_cloud(local_path, mount_info) -> NoReturn:
    raise RuntimeError("To be checked")

    """Copy local content to cloud, unmount temp cloud and mount at final location"""

    temp_path = tempfile.mkdtemp()
    logger.info("Mounting to temporary location...")
    mount(temp_path, mount_info)

    logger.info("Copying local content to cloud...")
    rsync(local_path, temp_path)
    os.system(f"rm -rf {local_path}")

    logger.info("Unmounting temporary cloud...")
    unmount(path=temp_path)
    os.rmdir(temp_path)

    logger.info("Mounting cloud at final location...")
    mount(local_path, mount_info)


################################################################


def rsync(source_dir, target_dir, delete=False) -> NoReturn:
    raise RuntimeError("TO REVIEW")
    # args = [
    #     "rsync",
    #     "-rlv",  # recursive, links, verbose, cannot use -a with juicefs
    #     source_dir.rstrip("/") + "/",
    #     target_dir,
    # ]
    #
    # if delete:
    #     args.append("--delete")
    #
    # rsync_process = subprocess.run(
    #     args,
    #     stdout=subprocess.PIPE,
    #     stderr=subprocess.PIPE,
    # )
    # Mounter.check_process_return(rsync_process, "Rsync failed")


################################################################
