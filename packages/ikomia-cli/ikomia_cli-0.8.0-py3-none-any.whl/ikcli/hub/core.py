"""Hub API Object."""

from yarl import URL

from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest


class Package(Object):
    """Algo package."""

    pass


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


class Algo(Object):
    """Hub Algo API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Algo object.

        Returns:
            Algo object representation
        """
        return f"Algo {self['name']} v{self['version']}"

    @property
    def packages(self) -> Packages:
        """
        Get algo package list.

        Returns:
            Algo package list.
        """
        return Packages(self._http, self._url / "packages/")


class Hub(List):
    """Hub API."""

    def __init__(self, http: HTTPRequest, url: URL = None):
        """
        Initialize a new Hub object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Hub
        """
        if url is None:
            url = URL("/v1/hub/")
        super().__init__(http, url, Algo)
