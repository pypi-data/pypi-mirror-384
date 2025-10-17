import importlib
import inspect
import pkgutil

from ..utils import logging
from .lazy_lists import (
    DownloaderList,
    LoaderList,
    PluginPackageNames,
    ReportList,
    ScannerList,
    UploaderList,
    ValidatorList,
    ViewerList,
)

print = logging.invalidPrint
logger = logging.getLogger()


PLUGINS_GROUP_NAME = "solidipes.plugins"


def get_subclasses_from_plugins(
    plugin_package_names: PluginPackageNames,
    subpackage_name: str,
    BaseClass: type,
) -> set[type]:
    """Get all subclasses of a base class in all plugins."""
    subclasses = set()

    for package_name in plugin_package_names + [
        "solidipes"
    ]:  # Include the main package to also search for non-plugin classes
        try:
            package = importlib.import_module(f"{package_name}.{subpackage_name}")
        except ModuleNotFoundError:
            continue

        subclasses.update(get_subclasses_from_package(package, BaseClass))

    return subclasses


def get_subclasses_from_package(
    package,
    BaseClass: type,
) -> set[type]:
    """Get all subclasses of a base class in a package."""

    module_names = [module.name for module in pkgutil.iter_modules(package.__path__) if module.ispkg is False]

    modules = [importlib.import_module(f"{package.__name__}.{module_name}") for module_name in module_names]

    subclasses_set = set()
    for module in modules:
        subclasses_set.update(_get_subclasses_from_module(module, BaseClass))

    return subclasses_set


def _get_subclasses_from_module(module, BaseClass: type) -> set[type]:
    subclasses = {
        obj
        for name, obj in inspect.getmembers(module)
        if inspect.isclass(obj) and BaseClass in obj.__mro__[1:] and obj != BaseClass
    }

    if len(subclasses) == 0:
        logger.debug(f"Could not find subclass of {BaseClass.__name__} in module {module}")

    return subclasses


def apply_to_object_parent_classes(cls, functor) -> None:
    clss = set([cls])
    while clss:
        new_clss = set()
        for cls in clss:
            functor(cls)
            for c in cls.__bases__:
                new_clss.add(c)
        clss = new_clss


def get_all_subclasses(cls):
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


plugin_package_names = PluginPackageNames(PLUGINS_GROUP_NAME)
downloader_list = DownloaderList(plugin_package_names)
loader_list = LoaderList(plugin_package_names)
report_list = ReportList(plugin_package_names)
scanner_list = ScannerList(plugin_package_names)
uploader_list = UploaderList(plugin_package_names)
validator_list = ValidatorList(plugin_package_names)
viewer_list = ViewerList(plugin_package_names)
