"""Group HTTP Exceptions."""

import requests.structures
import yarl

from .serializer import load


class HTTPBadCodeError(Exception):
    """Raised when request status code <200 or >299."""

    def __init__(self, url: yarl.URL, code: int, headers: requests.structures.CaseInsensitiveDict = None, content=None):
        """
        Init a new HTTP error.

        Args:
            url: URL
            code: HTTP code
            headers: Response header
            content: Response content
        """
        super().__init__(f"Bad return code {code} on '{url}'")
        self.url = url
        self.code = code
        self.headers = headers
        self.content = content

    def data(self):
        """
        Return parsed content as valid python data.

        Returns:
            Parsed content as python data
        """
        return load(self.content, self.headers)
