"""API exceptions."""


class ObjectNotFoundException(Exception):
    """Raised when no api object found."""

    def __init__(self, object_class, **kwargs):
        """
        Initialize a new ObjectNotFoundException.

        Args:
            object_class: API Objet class.
            kwargs: lookup param
        """
        # Remove kwargs with None value to avoid get user confused
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().__init__(f"{object_class.__name__} that match '{kwargs}' not found.")
        self.object_class = object_class
        self.kwargs = kwargs


class NotUniqueObjectException(Exception):
    """Raised when more than one object found."""

    def __init__(self, object_class, pagination, **kwargs):
        """
        Initialize a new NotUniqueObjectException.

        Args:
            object_class: API Objet class.
            pagination: A pagination object that contains all items found
            kwargs: lookup param
        """
        # Remove kwargs with None value to avoid get user confused
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        super().__init__(f"{len(pagination)} {object_class.__name__} that match '{kwargs}' were found.")
        self.object_class = object_class
        self.pagination = pagination
        self.kwargs = kwargs
