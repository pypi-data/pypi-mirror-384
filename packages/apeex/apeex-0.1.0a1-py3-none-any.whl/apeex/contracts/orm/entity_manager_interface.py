from typing import Protocol, Any, Optional, Type, runtime_checkable

@runtime_checkable
class EntityManagerInterface(Protocol):
    """
    Provides the primary API for persisting, removing, and querying entities.
    """

    def persist(self, entity: Any) -> None:
        """Mark the entity for persistence."""
        ...

    def remove(self, entity: Any) -> None:
        """Mark the entity for removal."""
        ...

    def find(self, entity_class: Type, id: Any) -> Optional[Any]:
        """Find an entity by its primary key."""
        ...

    def flush(self) -> None:
        """Flush all changes to the underlying database."""
        ...

    def clear(self) -> None:
        """Clear the persistence context."""
        ...
