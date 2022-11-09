###################################################################################################
#                              MIT Licence (C) 2022 Cubicpath@Github                              #
###################################################################################################
"""Version checking and validation."""
from __future__ import annotations

__all__ = (
    'is_greater_version',
    'VersionChecker',
)

import json
from datetime import datetime
from importlib.metadata import version
# noinspection PyProtectedMember, PyUnresolvedReferences
from setuptools._vendor.packaging.version import Version
from typing import Any

from PySide6.QtCore import *
from PySide6.QtNetwork import *

from .._version import __version__
from ..constants import *
from ..utils.network import guess_json_utf
from ..utils.package import has_package
from .manager import NetworkSession


def get_version(package_name: str) -> Version | None:
    """Return the :py:class:`Version` of the given package if it is installed. Else return None."""
    if has_package(package_name):
        return Version(version(package_name))


def is_greater_version(version1: str, version2: str) -> bool:
    """Return whether ``version1`` is greater than ``version2``."""
    if not isinstance(version1, Version):
        version1 = Version(version1)
    if not isinstance(version2, Version):
        version2 = Version(version2)

    return version1 > version2


class VersionChecker(QObject):
    """Checks for the latest versions of packages."""
    checked = Signal(str, name='finished')
    newerVersion = Signal(str, str, name='versionChecked')

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)

        self.session: NetworkSession = NetworkSession(self)

    def check_version(self, package_name: str = HI_PACKAGE_NAME) -> None:
        """Check the latest version of the given package on PyPI.

        If the latest version is greater than the current version,
        emit the ``newerVersion`` signal with the given name and the latest version as arguments.

        Emit the ``checked`` signal after a successful call.

        :param package_name: The package to look up on PyPI.
        """
        def handle_reply(reply: QNetworkReply):
            # Get PyPI data from reply
            data_bytes: bytes = reply.readAll().data()
            data: dict[str, Any] = json.loads(data_bytes.decode(guess_json_utf(data_bytes)))
            date_format: str = '%Y-%m-%dT%H:%M:%S.%fZ'

            # Sort versions on date released
            versions: list[str] = sorted(
                releases := data['releases'],
                key=lambda v: datetime.strptime(releases[v][0]['upload_time_iso_8601'], date_format)
            )

            # Get local version of given package. Use __version__ attribute for own package.
            local_version: str | None = get_version(package_name) if package_name != HI_PACKAGE_NAME else __version__

            # Get the latest version and compare to current version. Emit newerVersion if greater.
            latest: str = versions[-1]
            if is_greater_version(latest, local_version):
                self.newerVersion.emit(package_name, latest)
            self.checked.emit(package_name)

            reply.deleteLater()

        self.session.get(f'https://pypi.org/pypi/{package_name.replace("_", "-").strip()}/json', finished=handle_reply)
