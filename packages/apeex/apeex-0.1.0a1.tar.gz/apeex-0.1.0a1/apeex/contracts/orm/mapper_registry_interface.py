from typing import Protocol, Type, runtime_checkable
from apeex.orm.class_metadata import ClassMetadata

@runtime_checkable
class MapperRegistryInterface(Protocol):
    """
    Provides metadata mapping for entity classes.
    """

    def get_metadata(self, entity_class: Type) -> ClassMetadata:
        """Return metadata for a given entity class."""
        ...
