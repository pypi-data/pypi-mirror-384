"""Manage data extract or given to HTTPRequest."""

import functools
import json
import re
from abc import ABC, abstractmethod


class Mime:
    """A mime type : https://en.wikipedia.org/wiki/Media_type."""

    def __init__(self, mime_type: str, subtype: str, suffix: str = None, parameters: dict = None):
        """
        Initialize a new mime type.

        Args:
            mime_type: A mime type
            subtype: Mime sub type
            suffix: Mime suffix
            parameters: Mime parameters
        """
        self.type = mime_type
        self.subtype = subtype
        self.suffix = suffix
        self.parameters = parameters

    def __repr__(self) -> str:
        """
        Mime type representation.

        Returns:
            Mime type representation
        """
        message = f"{self.type}/{self.subtype}"
        if self.suffix is not None:
            message += f"+{self.suffix}"
        if self.parameters is not None:
            message += "; ".join([f"{k}={v}" for k, v in sorted(self.parameters.items())])
        return message

    @classmethod
    def parse(cls, mime: str) -> "Mime":
        """
        Parse textual mime and return Mime object.

        Args:
            mime: A textual mime type

        Returns:
            A Mime object

        Raises:
            ValueError: If can't parse mime
        """
        # Parse mime
        m = re.match(r"^(?P<type>[a-z]+)\/(?P<subtype>[a-z-\.]+)(?P<suffix>\+[a-z\.]+)?(; (?P<parameters>.+))?", mime)
        if m is None:
            raise ValueError(f"Can't parse mime type '{mime}'")

        # Split parameter to dict
        parameters = None
        if m.group("parameters"):
            parameters = {}
            for parameter in m.group("parameters").split(";"):
                (k, v) = parameter.split("=")
                parameters[k] = v

        return cls(m.group("type"), m.group("subtype"), suffix=m.group("suffix"), parameters=parameters)


class Serializer(ABC):
    """Convert data from or to python data."""

    @abstractmethod
    def __init__(self, mime: Mime):
        """
        Initialize a new Serializer.

        Args:
            mime: Supported Mime
        """
        self.mime = mime

    @abstractmethod
    def load(self, data):
        """
        Convert to python data.

        Args:
            data: Native data

        Returns:
            Python data
        """
        pass

    @abstractmethod
    def dump(self, data):
        """
        Convert from python data.

        Args:
            data: Python data

        Returns:
            Native data
        """
        pass


class JsonSerializer(Serializer):
    """Serialize json data."""

    def __init__(self):
        """Initialize a new json serializer."""
        super().__init__(Mime("application", "json"))

    def load(self, data):
        """
        Convert to python data.

        Args:
            data: Native data

        Returns:
            Python data
        """
        return json.loads(data)

    def dump(self, data):
        """
        Convert from python data.

        Args:
            data: Python data

        Returns:
            Native data
        """
        return json.dumps(data)


class TextSerializer(Serializer):
    """Serialize Text data."""

    def __init__(self):
        """Initialize a new text serializer."""
        super().__init__(Mime("text", "plain"))

    def load(self, data):
        """
        Convert to python data.

        Args:
            data: Native data

        Returns:
            Python data
        """
        if isinstance(data, bytes):
            return data.decode("utf-8")
        return data

    def dump(self, data):
        """
        Convert from python data.

        Args:
            data: Python data

        Returns:
            Native data
        """
        return data


class PythonSerializer(Serializer):
    """Serialize python data (mean no-op)."""

    def __init__(self):
        """Initialize a new python serializer."""
        super().__init__(Mime("x-python", "data"))

    def load(self, data):
        """
        Convert to python data.

        Args:
            data: Native data

        Returns:
            Python data
        """
        if isinstance(data, bytes):
            return data.decode("UTF-8")
        return data

    def dump(self, data):
        """
        Convert from python data.

        Args:
            data: Python data

        Returns:
            Native data
        """
        return data


class FormURLEncoded(Serializer):
    """Serialize Form urlencoded data."""

    def __init__(self):
        """Initialize a new for urlencoded serializer."""
        super().__init__(Mime("application", "x-www-form-urlencoded"))

    def load(self, data):
        """
        Convert to python data.

        Args:
            data: Native data

        Returns:
            Python data
        """
        if isinstance(data, bytes):
            return data.decode("UTF-8")
        return data

    def dump(self, data):
        """
        Convert from python data.

        Args:
            data: Python data

        Returns:
            Native data
        """
        return data


@functools.lru_cache(maxsize=None)
def get(name: str) -> Serializer:
    """
    Get a serializer from mime type or subtype.

    Args:
        name: A mime type or subtype name

    Returns:
        Serializer

    Raises:
        TypeError: If data type not supported.
    """
    if name == "json":
        return JsonSerializer()
    if name == "text":
        return TextSerializer()
    if name == "x-python":
        return PythonSerializer()

    raise TypeError(f"Can't find a serializer to process '{name}' type")


def load(data, metadata=None):
    """
    Convert heterogeneous data to python.

    Args:
        data: HTTPRequest data
        metadata: HTTPRequest metadata

    Returns:
        Python data

    Raises:
        TypeError: If raw data can't be converted to python
    """
    # If no data, return python serializer
    if data is None:
        return get("x-python").load(data)

    # Extract mime type if available
    if metadata is not None and "Content-Type" in metadata:
        mime = Mime.parse(metadata["Content-Type"])
        # first test subtype
        try:
            serializer = get(mime.subtype)
        except TypeError:
            # then test type
            serializer = get(mime.type)
        return serializer.load(data)

    # If no content, nothing to convert so return python serializer
    if "Content-Length" in metadata and metadata["Content-Length"] == "0":
        return get("x-python").load(data)

    raise TypeError(f"Can't convert data '{data}' with metadata '{metadata}'")
