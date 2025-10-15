"""Project API Object."""

from pathlib import Path

import ikclient.core.client
from yarl import URL

from ikcli.common.core import Members
from ikcli.net.api import List, Object
from ikcli.net.http.core import HTTPRequest
from ikcli.workflows.archive import Archive
from ikcli.workflows.core import WorkflowBase


class Deployment(Object):
    """Deployment API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Deployment object.

        Returns:
            Deployment object representation
        """
        return f"Deployment {self['provider']} {self['region']} {self['flavour']} {self['endpoint']}"

    def get_endpoint_client(self) -> ikclient.core.client.Client:
        """
        Get deployment endpoint client.

        Returns:
            Deployment endpoint client
        """
        # Get auth token
        token = self._http.auth.token

        # Remove scheme from token if present
        try:
            token = token[token.index(" ") :].strip()
        except ValueError:
            # no scheme
            pass

        # Return endpoint client with valid auth token
        return ikclient.core.client.Client(URL(self["endpoint"]), token=token)

    def logs(self, start: int = None, end: int = None, level: str = None, limit: int = 1000) -> dict:
        """
        Return deployment logs.

        Args:
            start: Get logs since given timestamps in millis
            end: Get logs until given timestamp in millis, missing mean now
            level: Specify a level to filter logs
            limit: Limit to number logs

        Returns:
            A dict with 'logs' as array and 'end' as timestamp in millis
        """
        # Craft query
        query = {
            "start": start,
            "end": end,
            "level": level,
            "limit": limit,
        }

        # Get log endpoint
        return self._http.get(self._url / "logs/", query=query)

    def usage(self, from_ts_in_ms: int, to_ts_in_ms: int) -> list:
        """
        Return deployment usage, per products.

        Args:
            from_ts_in_ms: Get usage since timestamp in millis
            to_ts_in_ms: Get usage until timestamp in millis

        Returns:
            A list with usage information per product
        """
        query = {
            "from": from_ts_in_ms,
            "to": to_ts_in_ms,
        }
        return self._http.get(self._url / "usage/", query=query)


class Deployments(List):
    """Deployment API List."""

    def __init__(self, http: HTTPRequest, url: URL):
        """
        Initialize a new Deployments object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Deployments
        """
        super().__init__(http, url, Deployment)


class Workflow(WorkflowBase):
    """Workflow API Object."""

    @property
    def deployments(self) -> Deployments:
        """
        Return workflow deployment list.

        Returns:
            workflow deployment list
        """
        return Deployments(self._http, self._url / "deployments/")


class Workflows(List):
    """Workflow API List."""

    def __init__(self, http: HTTPRequest, url: URL):
        """
        Initialize a new Workflows object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Workflows
        """
        super().__init__(http, url, Workflow)

    def create(self, filename: Path = None, **_) -> Workflow:
        """
        Create a new workflow from filename.

        Args:
            filename: Workflow json file name
            **_: Extra kwargs to give to package creation (not used)

        Returns:
            A new workflow
        """
        with Archive(filename) as zfh:
            data = self._http.post(self._url, None, files={"archive": zfh})
            return Workflow(self._http, URL(data["url"]), data=data)


class Project(Object):
    """Project API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of object.

        Returns:
            Object representation
        """
        return f"Project {self['name']}"

    @property
    def members(self) -> Members:
        """
        Return member list.

        Returns:
            Member list
        """
        return Members(self._http, self._url / "members/")

    @property
    def workflows(self) -> Workflows:
        """
        Return project workflow list.

        Returns:
            Project workflow list
        """
        return Workflows(self._http, self._url / "workflows/")


class Projects(List):
    """Project API List."""

    def __init__(self, http, url: URL = None):
        """
        Initialize a new Projects object.

        Args:
            http: A HTTPRequest object to talk with api
            url: Absolute or relative path to Projects
        """
        if url is None:
            url = URL("/v1/projects/")

        super().__init__(http, url, Project)

    def get(self, **kwargs) -> Object:
        """
        Get project from the given name and/or path.

        Args:
            kwargs: lookup params

        Returns:
            Project
        """
        if "path" in kwargs and kwargs["path"] != "":
            return super().get(name=kwargs["name"], namespace=kwargs["path"])

        return super().get(**kwargs)
