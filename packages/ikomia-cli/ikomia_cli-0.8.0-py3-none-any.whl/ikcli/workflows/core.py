"""Workflow core API."""

from ikcli.net.api import Object


class WorkflowBase(Object):
    """Workflow API Object."""

    def __repr__(self) -> str:
        """
        Return a representation of Workflow object.

        Returns:
            Workflow object representation
        """
        return f"Workflow {self['name']}"
