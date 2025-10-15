"""Map data to REST urls."""

from typing import Any, Optional, Type

from yarl import URL

from ikcli.net.http.core import HTTPRequest

from .exceptions import NotUniqueObjectException, ObjectNotFoundException
from .pagination import PageNumberPagination, Pagination


class Object:
    """
    Base object to map data from REST url.

    This can be use as python dict.
    """

    def __init__(self, http: HTTPRequest, url: URL, data: dict = None):
        """
        Initialize a new api object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Relative or absolute URL to object
            data: Object data
        """
        self._http = http
        self._url = url
        if data is None:
            self._data = {}
        else:
            self._data = data

    def get_http_request(self) -> HTTPRequest:
        """
        Return internal HTTP request object.

        Returns:
            Internal HTTPRequest
        """
        return self._http

    def get(self, key: Any, default: Any = None) -> Optional[Any]:
        """
        Get object item.

        Args:
            key: Item key
            default: Default value if key not found

        Returns:
            Object item value
        """
        return self._data.get(key, default=default)

    def __getitem__(self, key: str):
        """
        Get object item.

        Args:
            key: Item key

        Returns:
            Object item value

        Example:
            name = organisation['name']
        """
        return self._data.get(key)

    def __setitem__(self, key: str, value):
        """
        Set object item value.

        Args:
            key: Object item key
            value: Object item value
        """
        self._data[key] = value

    def __contains__(self, key: str) -> bool:
        """
        Return if object contains item.

        Args:
            key: Object item key

        Returns:
            True if item exists, False otherwise
        """
        return key in self._data

    def clear(self):
        """Clear object data."""
        self._data.clear()

    def reload(self) -> object:
        """
        Reload object data.

        Returns:
            Self object
        """
        self.clear()
        self._data = self._http.get(self._url)
        return self

    def update(self):
        """Update object on remote server."""
        # Remove 'None' values from data before PUT on server
        data = {k: v for k, v in self._data.items() if v is not None}
        self._data = self._http.put(self._url, data)

    def delete(self):
        """
        Delete object on remote server.

        Returns:
            Raw server response
        """
        return self._http.delete(self._url)


class List:
    """A list of API objects."""

    def __init__(
        self,
        http: HTTPRequest,
        url: URL,
        object_class: Type[Object],
        pagination: Type[Pagination] = PageNumberPagination,
    ):
        """
        Initialize a new api object list.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to list
            object_class: A class to map api object in list
            pagination: A pagination class
        """
        self._http = http
        self._url = url
        assert isinstance(url, URL)
        self._object_class = object_class
        self._pagination = pagination

    def get_http_request(self) -> HTTPRequest:
        """
        Return internal HTTP request object.

        Returns:
            Internal HTTPRequest
        """
        return self._http

    def list(self, **kwargs) -> Pagination:
        """
        Return a generator to object list.

        Args:
            kwargs: lookup param

        Returns:
            A pagination generator
        """
        # Remove 'None' values from kwargs (not supported by yarl as query)
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        return self._pagination(self._http, self._url % kwargs, self._object_class)

    def get(self, **kwargs) -> Object:
        """
        Return an object.

        Args:
            kwargs: lookup param

        Returns:
            An API object

        Raises:
            ObjectNotFoundException: If no object found
            NotUniqueObjectException: If more than one object found
        """
        pagination = iter(self.list(**kwargs))
        if len(pagination) == 0:
            raise ObjectNotFoundException(self._object_class, **kwargs)
        if len(pagination) > 1:
            raise NotUniqueObjectException(self._object_class, pagination, **kwargs)
        return pagination.get(0)

    def create(self, **kwargs) -> Object:
        """
        Create a new object in list.

        Args:
            **kwargs: Object data

        Returns:
            New API Object
        """
        # Remove 'None' values from kwargs
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        data = self._http.post(self._url, data=kwargs)
        return self._object_class(self._http, URL(data["url"]), data=data)
