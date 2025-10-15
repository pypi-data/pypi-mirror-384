from typing import Protocol, Iterable, Mapping, Any, Optional, runtime_checkable

@runtime_checkable
class RepositoryInterface(Protocol):
    """
    Provides an abstract API for querying entities of a specific type.
    """

    def find(self, id: Any) -> Optional[Any]:
        """Find an entity by ID."""
        ...

    def find_all(self) -> Iterable[Any]:
        """Return all entities."""
        ...

    def find_by(self, criteria: Mapping[str, Any]) -> Iterable[Any]:
        """Find entities matching given criteria."""
        ...
