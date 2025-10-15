from typing import Protocol, runtime_checkable
from .entity_manager_interface import EntityManagerInterface

@runtime_checkable
class OrmEngineInterface(Protocol):
    """
    The ORM Engine interface is responsible for providing access
    to the EntityManager and coordinating low-level ORM operations.
    """

    def get_entity_manager(self) -> EntityManagerInterface:
        """Return the main EntityManager instance."""
        ...
