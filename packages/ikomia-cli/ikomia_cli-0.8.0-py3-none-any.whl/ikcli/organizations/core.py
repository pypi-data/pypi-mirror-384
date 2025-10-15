"""Organization API Objects."""

from yarl import URL

from ikcli.common.core import Members
from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest


class Organization(Object):
    """Organization API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Organization object.

        Returns:
            Organization object representation
        """
        return f"Organization {self['name']}"

    @property
    def members(self) -> Members:
        """
        Return member list.

        Returns:
            Member list
        """
        return Members(self._http, self._url / "members/")


class Organizations(List):
    """Organization API List."""

    def __init__(self, http: HTTPRequest, url: URL = None):
        """
        Initialize a new Organizations object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Organizations
        """
        if url is None:
            url = URL("/v1/organizations/")
        super().__init__(http, url, Organization)
