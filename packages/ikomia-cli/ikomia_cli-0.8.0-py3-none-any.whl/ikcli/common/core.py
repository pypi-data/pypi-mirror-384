"""ikcli common core objects."""

from yarl import URL

from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest
from ikcli.users.core import User


class Member(Object):
    """Member API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Member object.

        Returns:
            Member object representation
        """
        return f"{self['username']} as {self['role']}"


class Members(List):
    """Member API List."""

    def __init__(self, http: HTTPRequest, url: URL):
        """
        Initialize a new Members object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Members
        """
        super().__init__(http, url, Member)

    def create(self, user: User = None, **kwargs) -> Member:
        """
        Add a new member.

        Args:
            user: A user to add ad member
            **kwargs: Membership data

        Returns:
            New member
        """
        return super().create(user=user["url"], **kwargs)
