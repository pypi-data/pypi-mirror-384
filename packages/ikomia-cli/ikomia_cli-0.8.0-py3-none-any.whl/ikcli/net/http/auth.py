"""Manage HTTP authentication methods."""

from typing import Optional

import requests
from yarl import URL


class HTTPBasicAuth(requests.auth.AuthBase):
    """Basic HTTP authentication."""

    def __init__(self, url: URL, username: Optional[str], password: Optional[str]):
        """
        Initialize authentication.

        Args:
            url: URL to authenticate
            username: A username
            password: A password
        """
        super().__init__()
        self.url = url
        self.username = username
        self.password = password

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        """
        Modify a request to set authentication headers.

        Args:
            r: a Prepared Request

        Returns:
            An authenticated and prepared request
        """
        if self.username is None or self.password is None:
            return r

        # Add header
        r.headers["Authorization"] = requests.auth._basic_auth_str(self.username, self.password)
        return r


class HTTPTokenAuth(requests.auth.AuthBase):
    """Token in HTTP Header authentication."""

    def __init__(self, url: URL, token: str, schema: str = "Token"):
        """
        Initialize authentication.

        Args:
            url: URL to authenticate
            token: Token to authenticate
            schema: Authentication schema
        """
        super().__init__()
        self.url = url
        if token is None:
            self.token = None
        else:
            self.token = f"{schema} {token}"

    def __call__(self, r: requests.PreparedRequest) -> requests.PreparedRequest:
        """
        Modify a request to set authentication headers.

        Args:
            r: a Prepared Request

        Returns:
            An authenticated and prepared request
        """
        if self.token is None:
            return r

        # Add header
        r.headers["Authorization"] = self.token
        return r


class HTTPAuthContextManager:
    """Switch authentication in a context."""

    def __init__(self, http_request, auth: requests.auth.AuthBase):
        """
        Initialize a new http auth context manager.

        Args:
            http_request: An HTTPRequest object
            auth: A new auth to using within context
        """
        self.http_request = http_request
        self.auth = auth
        self.actual_auth = None

    def __enter__(self):
        """Enter to the context by replacing current authentication method with new one."""
        assert self.actual_auth is None, f"{self.__class__.__name__} was already initialized"

        self.actual_auth = self.http_request.auth
        self.http_request.auth = self.auth

    def __exit__(self, *exc):
        """
        Exit from context by restoring actual authentication.

        Args:
            *exc: Information related to stack trace
        """
        self.http_request.auth = self.actual_auth
        self.actual_auth = None
