"""Make HTTP interactions easier."""

import functools

from yarl import URL

from .auth import HTTPTokenAuth
from .core import HTTPRequest


@functools.lru_cache(maxsize=None)
def http(url: str, token: str = None) -> HTTPRequest:
    """
    Return driver to talk with ikscale API.

    Args:
        url: Ikomia scale api url
        token: API token for authentication

    Returns:
        A fully loaded HTTPRequest object.
    """
    # Parse url from str as yarl URL
    parsed_url = URL(url)

    # Get auth
    auth = HTTPTokenAuth(parsed_url, token)

    # Return HTTPRequest object
    return HTTPRequest(parsed_url, auth=auth)
