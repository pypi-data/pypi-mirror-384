"""Namespace API Object."""

from yarl import URL

from ikcli.algos.core import Algos
from ikcli.common.core import Members
from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest
from ikcli.projects.core import Projects


class Namespace(Object):
    """Namespace API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Namespace object.

        Returns:
            Namespace object representation
        """
        return f"Namespace {self['path']}"

    @property
    def members(self) -> Members:
        """
        Return member list.

        Returns:
            Member list
        """
        return Members(self._http, self._url / "members/")

    @property
    def projects(self) -> Projects:
        """
        Return a namespace project list.

        Returns:
            Namespace project list
        """
        return Projects(self._http, self._url / "projects/")

    @property
    def algos(self) -> Algos:
        """
        Return namespace algo list.

        Returns:
            Namespace algo list
        """
        return Algos(self._http, self._url / "algos/")

    @property
    def namespaces(self) -> "Namespace":
        """
        Return sub namespace list.

        Returns:
            Sub namespace list
        """
        return Namespaces(self._http, self._url / "namespaces/")


class Namespaces(List):
    """Namespace API List."""

    def __init__(self, http: HTTPRequest, url: URL = None):
        """
        Initialize a new Namespaces object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Namespaces
        """
        if url is None:
            url = URL("/v1/namespaces/")
        super().__init__(http, url, Namespace)
