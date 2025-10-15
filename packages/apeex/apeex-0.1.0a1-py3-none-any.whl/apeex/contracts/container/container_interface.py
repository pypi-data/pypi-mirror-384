from abc import ABC, abstractmethod
from typing import Any, Protocol, Type, Callable, runtime_checkable

class ContainerException(Exception):
    pass

class NotFoundException(ContainerException):
    pass

@runtime_checkable
class ContainerInterface(Protocol):
    """
    Interface for a Dependency Injection container.
    """

    def set(self, name: str, service: Any) -> None:
        """Register a service instance by name."""

    def set_factory(self, name: str, factory: Callable[['ContainerInterface'], Any]) -> None:
        """Register a service factory by name; receives container as argument."""

    def get(self, name: str) -> Any:
        """Retrieve a service by name; raise exception if not found."""

    def has(self, name: str) -> bool:
        """Check if a service is registered."""

    def autowire(self, cls: Type) -> Any:
        """Create an instance of cls, automatically resolving dependencies."""
