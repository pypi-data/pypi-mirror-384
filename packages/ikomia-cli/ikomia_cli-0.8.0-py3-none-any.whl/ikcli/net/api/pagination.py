"""Object to manage pagination."""

from abc import ABC, abstractmethod

from yarl import URL

from ikcli.net.http import HTTPRequest


class Pagination(ABC):
    """Abstract class to manage pagination."""

    def __init__(self, http: HTTPRequest, url: URL, object_class):
        """
        Initialize a new pagination class.

        Args:
            http: HTTP Request object
            url: Absolute or relative URL
            object_class: Object API class
        """
        self._http = http
        self._url = url
        self._object_class = object_class
        self._data = None
        self._index = 0

    def __iter__(self):
        """
        Initialize iterator.

        Returns:
            Itself as iterator
        """
        self._data = self._http.get(self._url)
        self._index = 0
        return self

    @abstractmethod
    def __next__(self):
        """
        Return next item.

        Returns:
            Next item

        Raises:
            StopIteration: When loop is over
        """

    @abstractmethod
    def __len__(self) -> int:
        """
        Return paginator total length.

        Returns:
            Paginator length
        """

    @abstractmethod
    def get(self, index: int):
        """
        Get object at index, for internal purpose only.

        Args:
            index: Index

        Returns:
            API Object instance
        """

    def limit(self, limit: int):
        """
        Limit pagination results.

        Args:
            limit: How many objects return at max

        Returns:
            A LimitPagination generator.
        """
        # First check if iterator was started
        assert self._data is None, "Can't set limit if paginator was already started"
        return LimitedPagination(self, limit)


class PageNumberPagination(Pagination):
    """Manage django PageNumberPagination."""

    def __len__(self) -> int:
        """
        Return paginator total length.

        Returns:
            Paginator length
        """
        return self._data["count"]

    def __next__(self):
        """
        Return next item.

        Returns:
            Next item

        Raises:
            StopIteration: When loop is over
        """
        # If reach end of page, load next one
        if self._index >= len(self._data["results"]):
            if self._data["next"] is None:
                raise StopIteration()
            self._data = self._http.get(URL(self._data["next"]))
            self._index = 0

        # Get object, increment index and return
        next_object = self.get(self._index)
        self._index += 1
        return next_object

    def get(self, index):
        """
        Get object at index, for internal purpose only.

        Args:
            index: Index

        Returns:
            API Object instance
        """
        data = self._data["results"][index]
        return self._object_class(self._http, URL(data["url"]), data=data)


class LimitedPagination:
    """Limited pagination returned results."""

    def __init__(self, pagination: Pagination, limit: int):
        """
        Initialize a new limited pagination.

        Args:
            pagination: A pagination object to limit
            limit: How many results to return
        """
        self._pagination = pagination
        self._limit = limit
        self._index = 0

    def __len__(self):
        """
        Return pagination total length.

        Returns:
            Pagination length
        """
        return len(self._pagination)

    def __iter__(self):
        """
        Initialize iterator.

        Returns:
            Itself as iterator
        """
        iter(self._pagination)
        self._index = 0
        return self

    def __next__(self):
        """
        Return next api object.

        Returns:
            Next api object

        Raises:
            StopIteration: If reach limit of reach end of pagination
        """
        # Check if reach limit
        if self._index >= self._limit:
            raise StopIteration()

        # Get next object, increment index and return
        next_object = next(self._pagination)
        self._index += 1
        return next_object

    def remaining(self) -> int:
        """
        Return how many object remain on pagination.

        Returns:
            How many objects remaining.
        """
        return len(self._pagination) - self._index
