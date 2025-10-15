"""Algo API Object."""

from pathlib import Path
from typing import Generator

from yarl import URL

import ikcli.hub.core
from ikcli.common.core import Members
from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest
from ikcli.utils.version import Version
from ikcli.workflows.archive import Archive
from ikcli.workflows.core import WorkflowBase

# Available licenses on ikscale.
# Format is { IDENTIFIER: (IKSCALE_ENUM_NAME, FULL_NAME)}
# https://spdx.org/licenses/
LICENCES = {
    "CUSTOM": ("CUSTOM", "A custom license can be found on algo repository"),
    "AGPL-3.0": ("AGPL_30", "GNU Affero General Public License v3.0"),
    "Apache-2.0": ("APACHE_20", "Apache License 2.0"),
    "BSD-3-Clause": ("BSD_3_CLAUSE", "BSD 3-Clause 'New' or 'Revised' License"),
    "CC0-1.0": ("CC0_10", "Creative Commons Zero v1.0 Universal"),
    "GPL-3.0": ("GPL_30", "GNU General Public License v3.0"),
    "LGPL-3.0": ("LGPL_30", "GNU Lesser General Public License v3.0"),
    "MIT": ("MIT", "MIT License"),
    "BSD-2-Clause": ("BSD_2_CLAUSE", "BSD-2-Clause: BSD 2-Clause 'Simplified' License"),
    "CC-BY-NC-4.0": ("CC_BY_NC_40", "Creative Commons Attribution Non Commercial 4.0 International"),
}


class Package(Object):
    """Algo package contains algo implementation for a platform."""

    def __repr__(self) -> str:
        """
        Return a representation of Package object.

        Returns:
            Object representation
        """
        return f"{self['language']} package ({', '.join(key + str(self['platform'][key]) for key in self['platform'])})"


class Packages(List):
    """Algo package list."""

    def __init__(self, http: HTTPRequest, url: URL):
        """
        Initialize a new Packages object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Packages
        """
        super().__init__(http, url, Package)

    def create(self, filename: Path = None, **kwargs) -> Package:
        """
        Create a new package on remote algo.

        Args:
            filename: Path to archive to upload
            **kwargs: Extra kwargs to give to package creation

        Returns:
            New created package
        """
        data = self._http.post(self._url, data=kwargs, files={"file": filename})
        return self._object_class(self._http, URL(data["url"]), data=data)


class Workflows(List):
    """Workflow API List."""

    def __init__(self, http: HTTPRequest, url: URL):
        """
        Initialize a new Workflows object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Workflows
        """
        super().__init__(http, url, WorkflowBase)

    def create(self, filename: Path = None, **_) -> WorkflowBase:
        """
        Create a new workflow from filename.

        Args:
            filename: Workflow json file name
            **_: Extra kwargs to give to package creation (not used)

        Returns:
            A new workflow
        """
        with Archive(filename) as zfh:
            data = self._http.post(self._url, None, files={"archive": zfh})
            return WorkflowBase(self._http, URL(data["url"]), data=data)


class Algo(Object):
    """Algo API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Algo object.

        Returns:
            Algo object representation
        """
        return f"Algo {self['path']}: {self['short_description']}"

    @property
    def members(self) -> Members:
        """
        Return member list.

        Returns:
            Member list
        """
        return Members(self._http, self._url / "members/")

    @property
    def packages(self) -> Packages:
        """
        Get algo package list.

        Returns:
            Algo package list.
        """
        return Packages(self._http, self._url / "packages/")

    @property
    def workflows(self) -> Workflows:
        """
        Get algo workflow list.

        Returns:
            workflow list
        """
        return Workflows(self._http, self._url / "demo-workflows/")

    def update(self):
        """Override update object on remote server by processing icon file."""
        # Remove 'None' values from data before PUT on server
        data = {k: v for k, v in self._data.items() if v is not None}

        # If icon is defined, remove from data and process as file
        files = None
        if "icon" in data:
            files = {
                "icon": data.pop("icon"),
            }

        self._data = self._http.put(self._url, data, files=files)

    def upload(self) -> Package:
        """
        Upload a package for algo.

        Returns:
            Uploaded package
        """
        from . import local  # pylint: disable=C0415

        local_info = local.get_platform_information()
        ik_algo = local.Algo(self["name"])
        min_python = ik_algo.info["python_min_version"]

        data = {
            "ikomia_min_version": ik_algo.info["ikomia_min_version"],
            "python_min_version": min_python if min_python else local_info["python_version"],
            "os": ik_algo.info["os"] if len(ik_algo.info["os"]) > 0 else local_info["os"],
            "architecture": local_info["architecture"],
        }

        if ik_algo.info["python_max_version"]:
            data["python_max_version"] = repr(Version(ik_algo.info["python_max_version"]).next_minor())

        with local.Package(ik_algo) as zf:
            return self.packages.create(zf, **data)

    def upload_workflow(self) -> WorkflowBase:
        """
        Upload a demo workflow for algo.

        Returns:
            Uploaded workflow package
        """
        from . import local  # pylint: disable=C0415

        ik_algo = local.Algo(self["name"])
        wf_file = ik_algo.create_workflow()
        return self.workflows.create(wf_file)

    def get_next_publish_information(self) -> dict:
        """
        Return next publish information as license or probable next versions.

        Returns:
            A dict with next publish information
        """
        return self._http.get(self._url / "publish/")

    def publish(self, license_name: str, version: Version) -> ikcli.hub.core.Algo:
        """
        Publish an algo to public hub.

        Args:
            license_name: A ikscale license enum name
            version: A version to publish

        Returns:
            An published algo object
        """
        data = self._http.put(self._url / "publish/", data={"license": license_name, "version": format(version)})
        return ikcli.hub.core.Algo(self._http, URL(data["url"])).reload()


class Algos(List):
    """Algo API List."""

    def __init__(self, http: HTTPRequest, url: URL = None):
        """
        Initialize a new Algos object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Algos
        """
        if url is None:
            url = URL("/v1/algos/")

        super().__init__(http, url, Algo)

    def create(self, icon: Path = None, **kwargs) -> Algo:
        """
        Create a new algo.

        Args:
            icon: Path to icon to upload
            **kwargs: Extra kwargs to give to package creation

        Returns:
            New created algo
        """
        # Remove 'None' values from kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if icon is not None:
            data = self._http.post(self._url, data=kwargs, files={"icon": icon})
        else:
            data = self._http.post(self._url, data=kwargs)

        return self._object_class(self._http, URL(data["url"]), data=data)

    @classmethod
    def create_local(cls, name: str, base_class: str, widget_class: str, qt_framework: str):
        """
        Create a new empty algo on local ikomia install path.

        Args:
            name: New algo name
            base_class: Class new algo inherits
            widget_class: Class new widget class inherits
            qt_framework: QT framework to use. Can be pyqt or pyside

        Returns:
            New created algo
        """
        from . import local  # pylint: disable=C0415

        return local.Algo.create(name, base_class, widget_class, qt_framework)

    @classmethod
    def get_local(cls, name: str):
        """
        Get local algo object.

        Args:
            name: Local algo name

        Returns:
            Local algo object

        Raises:
            ValueError: when algo name not found
        """
        from . import local  # pylint: disable=C0415

        # Try to get local algo
        try:
            return local.Algo(name)
        except ValueError as e:
            # If algo not found, enhance exception with available algo list
            message = "Valid local algos are:\n "
            message += ", ".join(local.Algo.list())
            if not hasattr(e, "add_note"):
                e.__notes__ = [message]
            else:
                e.add_note(message)  # pylint: disable=E1101
            raise

    @classmethod
    def list_local(cls) -> Generator[object, None, None]:
        """
        Return a generator of local algos.

        Yields:
            A local algo object
        """
        from . import local  # pylint: disable=C0415

        for name in local.Algo.list():
            yield local.Algo(name)
