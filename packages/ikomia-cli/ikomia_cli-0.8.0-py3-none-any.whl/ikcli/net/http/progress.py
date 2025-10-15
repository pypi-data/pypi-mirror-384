"""Monitor HTTP transfer progress."""

from .core import HTTPRequest


class ProgressObserver:
    """Observes http transfer progress."""

    def __init__(self, http_request: HTTPRequest):
        """
        Create a new progress transfer observer.

        Args:
            http_request: An http request object to observe.
        """
        self.http_request = http_request

    def __enter__(self):
        """Enable observer."""
        self.http_request.append_observer(self)

    def __exit__(self, *args):
        """
        Disable observer.

        Args:
            *args: stuff given to ContextManager exit function.
        """
        self.http_request.remove_observer(self)

    def downloading(self, total: int, completed: int):
        """
        Call download action on observer.

        Args:
            total: Total bytes to transfer
            completed: Already transfered bytes
        """
        pass

    def uploading(self, total: int, completed: int):
        """
        Call upload action on observer.

        Args:
            total: Total bytes to transfer
            completed: Already transfered bytes
        """
        pass
