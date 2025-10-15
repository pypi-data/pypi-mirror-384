"""Core HTTP object."""

import io
import logging
from pathlib import Path

import requests
import requests.auth
import requests_toolbelt.multipart
from yarl import URL

from .exceptions import HTTPBadCodeError
from .serializer import JsonSerializer, Serializer, load

logger = logging.getLogger(__name__)


# Default request timeout
DEFAULT_TIMEOUT = 15 * 60 * 60


class HTTPRequest:  # pylint: disable=R0902
    """An object to make requests usage easier."""

    def __init__(self, url: URL, auth=None, timeout: int = DEFAULT_TIMEOUT, serializer: Serializer = None):
        """
        Initialize HTTPRequest object.

        Args:
            url: IKScale service url
            auth: Authentication class
            timeout: HTTP request timeout
            serializer: A Serializer to format data before request. If None, use JsonSerializer
        """
        self.url = url
        self.timeout = timeout
        self.connect_timeout = 5
        self.auth = auth
        self.session = requests.Session()
        self.headers = {"User-Agent": "IkomiaCli"}
        if serializer is None:
            self.serializer = JsonSerializer()
        else:
            self.serializer = serializer
        self._observers = []

    def append_observer(self, observer: object):
        """
        Append observer to observer list.

        Args:
            observer: Observer to append
        """
        self._observers.append(observer)

    def remove_observer(self, observer: object):
        """
        Remove observer from observer list.

        Args:
            observer: Observer to remove
        """
        self._observers.remove(observer)

    def _download_monitor(self, total: int, completed: int):
        """
        Call observers to notify download progress.

        Args:
            total: Total bytes to read
            completed: Bytes already read
        """
        for observer in self._observers:
            observer.downloading(total, completed)

    def _upload_monitor(self, monitor: requests_toolbelt.multipart.encoder.MultipartEncoderMonitor):
        """
        Call observers to notify upload progress.

        Args:
            monitor: A MultipartEncoderMonitor
        """
        for observer in self._observers:
            observer.uploading(monitor.len, monitor.bytes_read)

    def request(
        self, method: str, path: URL, query: dict = None, data=None, files: dict = None
    ):  # pylint: disable=R0912,R0913,R0914,R0915
        """
        Send an HTTP request.

        Args:
            method: HTTP method
            path: Query path as URL
            query: URL query params
            data: Data to send
            files: A dict that contains (filename, fh) pair

        Returns:
            A tuple with raw content and headers

        Raises:
            HTTPBadCodeError: If server return a code <200 or >299
            requests.exceptions.ReadTimeout: If request timeout
        """
        # Prepare headers
        headers = self.headers.copy()

        # Check if url is absolute
        if path.is_absolute():
            # Assert then address same origin
            assert path.origin() == self.url, f"Given URL '{path}' is not relative with '{self.url}'"
            url = path
        else:
            url = self.url.join(path)

        # If files are given, use requests_toolbelt.multipart.encoder to monitor upload
        if files is not None:
            # As requests_toolbelt.multipart.encoder doesn't support list or dict as value,
            #   convert data and set content-type
            # https://github.com/requests/toolbelt/issues/205
            fields = []
            if data is not None:
                for k, v in data.items():
                    if isinstance(v, (list, dict)):
                        fields.append((k, (None, self.serializer.dump(v), format(self.serializer.mime))))
                    else:
                        fields.append((k, v))

            # Append files
            for key in files:
                filename = files[key] if isinstance(files[key], Path) else Path(files[key])
                fields.append(
                    (
                        key,
                        (filename.name, filename.open("rb"), "application/octet-stream"),
                    )
                )

            # Create MultipartEncoderMonitor as request data
            m_encoder = requests_toolbelt.multipart.encoder.MultipartEncoder(fields=fields)
            data = requests_toolbelt.multipart.encoder.MultipartEncoderMonitor(m_encoder, callback=self._upload_monitor)
            headers["Content-Type"] = data.content_type

        elif data is not None:
            # Otherwise dump data on right format
            data = self.serializer.dump(data)
            headers["Content-Type"] = format(self.serializer.mime)

        # Create request object
        request = requests.Request(
            method=method,
            url=url,
            headers=headers,
            params=query,
            data=data,
            auth=self.auth,
        )
        prepared_request = self.session.prepare_request(request)

        # Produce some debug logs
        logger.debug("Will %s '%s'", prepared_request.method, prepared_request.url)
        if prepared_request.headers:
            logger.debug(" with headers : %s", prepared_request.headers)
        if prepared_request.body:
            if isinstance(prepared_request.body, requests_toolbelt.multipart.encoder.MultipartEncoderMonitor):
                logger.debug(" with body    : %s", prepared_request.body.encoder)
            else:
                if len(prepared_request.body) > 2048:
                    logger.debug(" with body    : .... too long to be dumped ! ...")
                else:
                    logger.debug(" with body    : %s", prepared_request.body)

        # Get response
        try:
            response = self.session.send(
                prepared_request, stream=True, timeout=(self.connect_timeout, self.timeout), allow_redirects=False
            )
        except requests.exceptions.ReadTimeout:
            logger.warning(
                "'%s' '%s' timeout after %d seconds", prepared_request.method, prepared_request.url, self.timeout
            )
            raise

        # Read stream and make observable progress
        content_bytes = io.BytesIO()
        content_bytes_total = int(response.headers["Content-Length"]) if "Content-Length" in response.headers else None
        content_bytes_done = 0
        for chunk in response.iter_content(chunk_size=requests.models.CONTENT_CHUNK_SIZE):
            content_bytes.write(chunk)
            content_bytes_done += len(chunk)
            self._download_monitor(content_bytes_total, content_bytes_done)

        # Get content
        content = content_bytes.getvalue()

        # Log response
        logger.debug("Response code : %d", response.status_code)
        logger.debug(" with headers : %s", response.headers)
        if ("Content-Length" in response.headers and int(response.headers["Content-Length"]) > 10240) or len(
            content
        ) > 2048:
            logger.debug(" with content    : .... too long to be dumped ! ...")
        else:
            logger.debug(" with content    : %s", content)

        # 200 = return response and meta
        if response.status_code >= 200 and response.status_code <= 299:
            return (content, response.headers)

        # Otherwise raise error
        raise HTTPBadCodeError(prepared_request.url, response.status_code, headers=response.headers, content=content)

    def head(self, path: URL, query: dict = None):
        """
        HEAD HTTP Request.

        Args:
            path: request path
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("HEAD", path, query=query)
        return load(content, metadata=metadata)

    def get(self, path: URL, query: dict = None):
        """
        GET HTTP Request.

        Args:
            path: request path
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("GET", path, query=query)
        return load(content, metadata=metadata)

    def post(self, path: URL, data, files: dict = None, query: dict = None):
        """
        POST HTTP Request.

        Args:
            path: request path
            data: Payload data
            files: A dict that contains info about files to send
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("POST", path, query=query, data=data, files=files)
        return load(content, metadata=metadata)

    def put(self, path: URL, data, files: dict = None, query: dict = None):
        """
        PUT HTTP Request.

        Args:
            path: request path
            data: Payload data
            files: A dict that contains info about files to send
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("PUT", path, query=query, data=data, files=files)
        return load(content, metadata=metadata)

    def patch(self, path: URL, data, files: dict = None, query: dict = None):
        """
        PATCH HTTP Request.

        Args:
            path: request path
            data: Payload data
            files: A dict that contains info about files to send
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("PATCH", path, query=query, data=data, files=files)
        return load(content, metadata=metadata)

    def delete(self, path: URL, query: dict = None):
        """
        DELETE HTTP Request.

        Args:
            path: request path
            query: Query param as dict

        Returns:
            Python data
        """
        (content, metadata) = self.request("DELETE", path, query=query)
        return load(content, metadata=metadata)
