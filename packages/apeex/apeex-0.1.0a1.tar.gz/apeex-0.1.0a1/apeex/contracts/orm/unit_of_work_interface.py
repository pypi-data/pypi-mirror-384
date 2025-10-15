from typing import Protocol, Any, runtime_checkable

@runtime_checkable
class UnitOfWorkInterface(Protocol):
    """
    Tracks changes to entities and commits them through the ORM Engine.
    """

    def register_new(self, entity: Any) -> None:
        """Register a new entity for insertion."""
        ...

    def register_dirty(self, entity: Any) -> None:
        """Register an entity that has been modified."""
        ...

    def register_removed(self, entity: Any) -> None:
        """Register an entity for removal."""
        ...

    def commit(self) -> None:
        """Apply all changes through the ORM engine."""
        ...
