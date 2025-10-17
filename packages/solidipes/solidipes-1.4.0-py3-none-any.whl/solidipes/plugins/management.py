import importlib
import site
import subprocess
import sys
from typing import Optional

if sys.version_info < (3, 10):
    from importlib_metadata import distribution, version
else:
    from importlib.metadata import distribution, version

from ..utils import logging
from .discovery import loader_list, plugin_package_names, viewer_list

print = logging.invalidPrint
logger = logging.getLogger()


def clear_preferred_cache() -> None:
    """Clear preferred loader and viewer names from cache for all files."""
    from solidipes.loaders.cached_metadata import CachedMetadata

    global_cached_metadata = CachedMetadata.get_global_cached_metadata()

    for unique_identifier in CachedMetadata.get_global_cached_metadata().keys():
        for field in ["preferred_loader_name", "preferred_viewer_name"]:
            if field in global_cached_metadata[unique_identifier]:
                del global_cached_metadata[unique_identifier][field]

        CachedMetadata.update_global_cached_metadata(unique_identifier)


def reset_plugins():
    module_to_refresh = []

    for module_name in sys.modules:
        for plugin_package_name in plugin_package_names:
            if module_name.startswith(plugin_package_name):
                module_to_refresh.append(module_name)
                break

    reloaded_versions = {}
    for module_name in module_to_refresh:
        try:
            importlib.reload(sys.modules[module_name])
            if hasattr(sys.modules[module_name], "__version__"):
                reloaded_versions[module_name] = sys.modules[module_name].__version__
        except ModuleNotFoundError:
            pass

    for module_name in module_to_refresh:
        del sys.modules[module_name]

    clear_preferred_cache()

    site.main()  # Update sys.path for plugins installed in editable mode
    plugin_package_names.reset()
    site.main()  # Update sys.path for plugins installed in editable mode
    loader_list.reset()
    viewer_list.reset()
    logger.debug("Plugins reset")
    return reloaded_versions


def install_plugin(
    plugin_url: str, index_url: Optional[str] = None, editable: bool = False, update: bool = False
) -> None:
    logger.debug(f"Installing plugin {plugin_url}{f' from {index_url}' if index_url else ''}")

    command = [
        sys.executable,
        "-m",
        "pip",
        "install",
    ]

    if index_url:
        command.extend(["--index-url", index_url])

    if editable:
        command.append("-e")

    if update:
        command.append("-U")

    command.append(plugin_url)

    try:
        logger.debug(f"Running command: {' '.join(command)}")
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.debug(f"Plugin {plugin_url} installed successfully")
        reset_plugins()

    except subprocess.CalledProcessError as e:
        message = f"Error installing plugin {plugin_url}"
        if e.stderr:
            message += f"\n{e.stderr.decode()}"

        raise RuntimeError(message) from e


def remove_plugin(package_name: str) -> None:
    if package_name == "solidipes-core-plugin" or package_name == "solidipes_core_plugin":
        raise RuntimeError("Cannot remove the core plugin")

    logger.debug(f"Removing plugin {package_name}")

    command = [
        sys.executable,
        "-m",
        "pip",
        "uninstall",
        "-y",
        package_name,
    ]

    try:
        logger.debug(f"Running command: {' '.join(command)}")
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        logger.debug(f"Plugin {package_name} removed successfully")
        reset_plugins()

    except subprocess.CalledProcessError as e:
        message = f"Error removing plugin {package_name}"
        if e.stderr:
            message += f"\n{e.stderr.decode()}"

        raise RuntimeError(message) from e


def get_installed_plugins_info() -> list[dict]:
    infos = []

    for p in plugin_package_names:
        info = {"name": p, "version": version(p)}
        if p in sys.modules:
            info["loaded"] = sys.modules[p].__version__
        info.update(get_distribution_info(p))
        infos.append(info)

    return infos


def get_distribution_info(plugin_name: str) -> dict:
    dist = distribution(plugin_name)
    origin = getattr(dist, "origin", None)

    if origin is None:
        return {
            "url": dist.name,
            "package": dist.name,
            "editable": False,
        }

    return {
        "url": f"git+{origin.url}" if origin.url.startswith("https://") else origin.url,
        "package": dist.name,
        "editable": getattr(getattr(origin, "dir_info", {}), "editable", False),
    }
