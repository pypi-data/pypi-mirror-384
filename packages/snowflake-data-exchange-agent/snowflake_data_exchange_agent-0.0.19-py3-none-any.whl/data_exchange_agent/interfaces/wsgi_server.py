"""WSGI server interface module for the data exchange agent."""

from abc import ABC, abstractmethod


class WSGIServerInterface(ABC):
    """
    Interface for WSGI server implementations.

    This abstract base class defines the interface that WSGI server implementations
    must follow to provide WSGI server functionality.
    """

    @abstractmethod
    def start(self) -> None:
        """Start the WSGI server."""
        pass
