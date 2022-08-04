###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Package-related utility functions."""
from __future__ import annotations

__all__ = (
    'current_requirement_licenses',
    'current_requirement_names',
    'current_requirement_versions',
    'has_package',
)

from pathlib import Path


def current_requirement_licenses(package: str, include_extras: bool = False) -> dict[str, tuple[str, str]]:
    """Return the current licenses for the requirements of the given package.

    CANNOT get license file from a package with an editable installation.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: dict mapping a package nams to a tuple containing the license name and contents.
    """
    from importlib.metadata import metadata
    from pkg_resources import get_distribution

    result = {}
    for requirement in ([package] + current_requirement_names(package, include_extras)):
        dist = get_distribution(requirement)
        name = dist.project_name.replace("-", "_")
        license_text = None

        info_path = Path(dist.location) / f'{name}-{dist.version}.dist-info'
        if not info_path.is_dir():
            egg_path = info_path.with_name(f'{name}.egg-info')
            if egg_path.is_dir():
                info_path = egg_path

        for file in info_path.iterdir():
            f_name = file.name.lower()
            if 'license' in f_name:
                license_text = file.read_text(encoding='utf8')

        result[name] = (metadata(name).get('License', 'UNKNOWN'), license_text)

    return result


def current_requirement_names(package: str, include_extras: bool = False) -> list[str]:
    """Return the current requirement names for the given package.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: list of package names.
    """
    from importlib.metadata import requires

    req_names = []
    for requirement in requires(package):
        if not include_extras and '; extra' in requirement:
            continue
        # Don't include testing extras
        if include_extras and requirement.split('extra ==')[-1].strip().strip('"') in ('dev', 'develop', 'development', 'test', 'testing'):
            continue

        split_char = 0
        for char in requirement:
            if not char.isalnum() and char not in ('-', '_'):
                break
            split_char += 1

        req_names.append(requirement[:split_char])

    return req_names


def current_requirement_versions(package: str, include_extras: bool = False) -> dict[str, str]:
    """Return the current versions of the installed requirements for the given package.

    :param package: Package name to search
    :param include_extras: Whether to include packages installed with extras
    :return: dict mapping package names to their version string.
    """
    from importlib.metadata import version

    return {name: version(name) for name in current_requirement_names(package, include_extras) if has_package(name)}


def has_package(package: str) -> bool:
    """Check if the given package is available.

    :param package: Package name to search; hyphen-insensitive
    :return: Whether the given package name is installed to the current environment.
    """
    from pkg_resources import WorkingSet

    for pkg in WorkingSet():
        if package.replace('-', '_') == pkg.project_name.replace('-', '_'):
            return True
    return False
