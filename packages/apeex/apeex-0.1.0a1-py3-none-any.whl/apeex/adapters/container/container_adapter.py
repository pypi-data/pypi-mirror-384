from apeex.contracts.container.container_interface import ContainerInterface
from typing import Any, Callable, Dict, Type

class SimpleContainer(ContainerInterface):
    def __init__(self):
        self._factories: Dict[str, Callable[[Any], Any]] = {}
        self._shared: Dict[str, Any] = {}

    def register(
            self,
            identifier: str,
            factory: Callable[["ContainerInterface"], Any],
            shared: bool = True
    ) -> None:
        self._factories[identifier] = factory

    def get(self, identifier_or_type: str | Type) -> Any:
        identifier = identifier_or_type if isinstance(identifier_or_type, str) else identifier_or_type.__name__
        if identifier in self._shared and self._shared[identifier] is not None:
            return self._shared[identifier]
        instance = self._factories[identifier](self)
        if identifier in self._shared:
            self._shared[identifier] = instance
        return instance

    def has(self, identifier_or_type: str | Type) -> bool:
        identifier = identifier_or_type if isinstance(identifier_or_type, str) else identifier_or_type.__name__
        return identifier in self._factories
