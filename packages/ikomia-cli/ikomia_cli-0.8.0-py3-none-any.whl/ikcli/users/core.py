"""User API object."""

from yarl import URL

from ikcli.net.api import List, Object
from ikcli.net.http.auth import HTTPAuthContextManager, HTTPBasicAuth
from ikcli.net.http.core import HTTPRequest


class User(Object):
    """User API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of User object.

        Returns:
            User object representation
        """
        return f"User {self['username']}"


class Users(List):
    """User API List."""

    def __init__(self, http: HTTPRequest, url: URL = None):
        """
        Initialize a new Users object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Users
        """
        if url is None:
            url = URL("/v1/users/")
        super().__init__(http, url, User)


class Account(Object):
    """Manage personal account."""

    def __init__(self, http: HTTPRequest):
        """
        Initialize a new Account object.

        Args:
            http: A HTTPRequest object to talk with api
        """
        super().__init__(http, URL("/v1/users/"))

    def create_token(self, username: str, password: str, name: str = "Token from ikcli", ttl: int = 3600) -> str:
        """
        Log user to platform.

        Args:
            username: Username
            password: User password
            name: Token name
            ttl: Token time to live

        Returns:
            A clear and valid token
        """
        with HTTPAuthContextManager(self._http, HTTPBasicAuth(self._http.url, username, password)):
            response = self._http.post(self._url / "me/tokens/", data={"name": name, "ttl": ttl})
        return response["clear_token"]

    def me(self) -> User:
        """
        Return logged user.

        Returns:
            Logged user
        """
        url = self._url / "me/"
        return User(self._http, url, data=self._http.get(url))

    def signup(self, username, email, password) -> User:
        """
        Signup a new user.

        Args:
            username: Username
            email: User email
            password: User password

        Returns:
            Newly created user
        """
        data = {
            "username": username,
            "email": email,
            "password": password,
        }
        response = self._http.post(URL("/v1/accounts/signup/"), data)
        return User(self._http, URL(response["url"]), data=response)
