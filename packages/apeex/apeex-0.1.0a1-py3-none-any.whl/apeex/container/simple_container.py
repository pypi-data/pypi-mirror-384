from apeex.contracts.container import ContainerInterface, NotFoundException
from typing import Any

class SimpleContainer(ContainerInterface):
    """Simple DI container compatible with PSR-11 style."""

    def __init__(self):
        self._services: dict[str, Any] = {}

    def register(self, service_id: str, service: Any) -> None:
        """
        Register any object or service under a given ID.
        This is an extension beyond PSR-11.
        """
        self._services[service_id] = service

    def get(self, service_id: str) -> Any:
        """Return a service by ID or raise NotFoundException if not found."""
        if service_id not in self._services:
            raise NotFoundException(f"Service '{service_id}' not found in container")
        return self._services[service_id]

    def has(self, service_id: str) -> bool:
        """Return True if service exists in the container."""
        return service_id in self._services
