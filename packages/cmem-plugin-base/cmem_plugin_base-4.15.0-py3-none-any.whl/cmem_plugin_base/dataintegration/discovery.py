"""Package and plugin discovery module."""

import importlib
import importlib.util
import json
import pkgutil
import sys
import traceback
from subprocess import check_output  # nosec
from types import ModuleType

from cmem_plugin_base.dataintegration.description import (
    Plugin,
    PluginDescription,
    PluginDiscoveryError,
    PluginDiscoveryResult,
)


def get_packages() -> object:
    """Get installed python packages.

    Returns a list of dict with the following keys:
     - name - package name
     - version - package version
    """
    return json.loads(
        check_output(["pip", "list", "--format", "json"], shell=False)  # noqa: S607
    )


def delete_modules(module_name: str = "cmem") -> None:
    """Find and delete all plugins within a base package.

    :param module_name: The base package. Will recurse into all submodules
        of this package.
    """
    if module_name in sys.modules:
        module = sys.modules[module_name]
        if hasattr(module, "__path__"):
            for _loader, name, _ in pkgutil.walk_packages(module.__path__):
                delete_modules(module.__name__ + "." + name)
        del sys.modules[module.__name__]


def import_modules(
    package_name: str = "cmem",
) -> list[PluginDescription]:
    """Find and import all plugins within a base package.

    :param package_name: The base package. Will recurse into all submodules
        of this package.
    """

    def import_submodules(module: ModuleType) -> list[ModuleType]:
        modules = []
        for _loader, name, is_pkg in pkgutil.walk_packages(module.__path__):
            sub_module = importlib.import_module(module.__name__ + "." + name)
            modules.append(sub_module)
            if is_pkg:
                modules.extend(import_submodules(sub_module))
        return modules

    Plugin.plugins = []

    root_module = importlib.import_module(package_name)
    modules = [root_module]
    modules.extend(import_submodules(root_module))

    return Plugin.plugins


def discover_plugins(package_name: str = "cmem_plugin") -> PluginDiscoveryResult:
    """Discover plugin descriptions in packages.

    This is the main discovery method which is executed by DataIntegration.
    It will go through all modules which base names starts with
    package_name.

    :param package_name: The package prefix.
    """
    # pylint: disable=broad-except

    target_packages = []
    plugin_descriptions = PluginDiscoveryResult()
    # select prefixed packages
    for module in pkgutil.iter_modules():
        name = module.name
        if name.startswith(package_name) and name != "cmem_plugin_base":
            target_packages.append(name)
    # delete all modules in the packages to make sure they will be re-imported freshly
    for name in target_packages:
        delete_modules(module_name=name)
    # import all packages
    for name in target_packages:
        try:
            for plugin in import_modules(package_name=name):
                plugin_descriptions.plugins.append(plugin)
        except BaseException as ex:  # noqa: BLE001
            error = PluginDiscoveryError(
                package_name=name,
                error_message=str(ex),
                error_type=type(ex).__name__,
                stack_trace=traceback.format_exc(),
            )
            plugin_descriptions.errors.append(error)

    return plugin_descriptions
