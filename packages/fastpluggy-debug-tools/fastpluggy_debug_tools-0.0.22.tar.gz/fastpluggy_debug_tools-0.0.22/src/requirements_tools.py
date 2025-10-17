import os
from importlib.metadata import distributions
from typing import List

from loguru import logger
from packaging.requirements import Requirement
from packaging.version import Version

from fastpluggy.core.plugin_state import PluginState


def get_requirements_files(plugins_state: dict[str, PluginState]) -> List[str]:
    """
    Returns a list of requirements.txt file paths for enabled and loaded plugins.
    """
    requirements_files = []
    for plugin in plugins_state.values():
        if plugin.initialized :#and plugin.loaded:
            req_path = os.path.join(plugin.path, "requirements.txt")
            if os.path.isfile(req_path):
                requirements_files.append(req_path)
    return requirements_files


def get_installed_packages():
    """
    Returns a dictionary of installed packages with their metadata.
    Safely skips distributions with missing or invalid names.
    """
    packages = {}
    for dist in distributions():
        # Some distributions may have missing/None Name metadata; skip those safely
        try:
            name = dist.metadata.get("Name") if hasattr(dist, "metadata") else None
        except Exception:
            name = None
        if not name:
            # If name is missing, try a best-effort fallback and continue only if valid
            try:
                fallback = getattr(dist, "name", None)
            except Exception:
                fallback = None
            name = fallback
        if not name:
            continue
        key = name.lower()
        packages[key] = {
            "name": name,
            "version": getattr(dist, "version", None),
            "summary": (dist.metadata.get("Summary", "") if hasattr(dist, "metadata") else ""),
            "author": (dist.metadata.get("Author", "") if hasattr(dist, "metadata") else ""),
            "home_page": (dist.metadata.get("Home-page", "") if hasattr(dist, "metadata") else ""),
        }
    return packages


def get_installed_packages_simple():
    """
    Returns a simple dictionary of installed packages (name: version).
    Used for compatibility with existing code.
    """
    # Guard against missing or None names in metadata
    return {
        name.lower(): getattr(dist, "version", None)
        for dist in distributions()
        for name in [(dist.metadata.get("Name") if hasattr(dist, "metadata") else None)]
        if name
    }


def check_requirements_file(requirements_file: str) -> list[tuple[str, str | None, str]]:
    """
    Checks a requirements.txt file and returns a list of missing or incompatible packages.
    Returns a list of (package_name, installed_version, required_specifier).
    """
    if not os.path.exists(requirements_file):
        logger.warning(f"Requirements file not found: {requirements_file}")
        return []

    missing = []
    installed = get_installed_packages_simple()

    with open(requirements_file) as f:
        lines = [line.strip() for line in f if line.strip() and not line.startswith("#")]

    for line in lines:
        try:
            req = Requirement(line)
            name = req.name.lower()
            installed_version = installed.get(name)
            if not installed_version:
                missing.append((req.name, None, str(req.specifier)))
            else:
                if not req.specifier.contains(Version(installed_version), prereleases=True):
                    missing.append((req.name, installed_version, str(req.specifier)))
        except Exception as e:
            logger.error(f"Error parsing requirement line '{line}': {e}")
            missing.append((line, "ERROR", "PARSE"))

    return missing

def check_multiple_requirements_files(files: list[str]) -> dict[str, list[tuple[str, str | None, str]]]:
    report = {}

    for file in files:
        issues = check_requirements_file(file)
        if issues:
            report[file] = issues

    return report
