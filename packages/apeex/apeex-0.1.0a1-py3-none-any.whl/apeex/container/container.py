import inspect
from typing import Any, Callable, Type, Dict
from apeex.contracts.container import ContainerInterface, NotFoundException


class Container(ContainerInterface):
    """
    Simple MVP Dependency Injection container supporting:
    - service/factory registration
    - autowiring via type hints
    - singleton scope
    """

    def __init__(self):
        self._services: Dict[str, Any] = {}
        self._factories: Dict[str, Callable[['Container'], Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def set(self, name: str, service: Any) -> None:
        """Register a service instance directly."""
        self._services[name] = service

    def set_factory(self, name: str, factory: Callable[['Container'], Any]) -> None:
        self._factories[name] = factory

    def get(self, name: str) -> Any:
        if name in self._services:
            return self._services[name]
        if name in self._factories:
            instance = self._factories[name](self)
            self._services[name] = instance
            return instance
        raise NotFoundException(...)

    def has(self, name: str) -> bool:
        return name in self._services or name in self._factories or name in self._singletons

    def autowire(self, cls: Type) -> Any:
        """
        Create instance via autowiring with singleton support.
        Automatically resolves constructor dependencies recursively.
        """
        name = cls.__name__

        # Return singleton if already created
        if name in self._services:
            return self._services[name]

        signature = inspect.signature(cls.__init__)
        kwargs = {}

        for param in list(signature.parameters.values())[1:]:  # skip self
            if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
                continue  # skip *args and **kwargs

            param_type = param.annotation
            if param_type is inspect.Parameter.empty:
                raise ValueError(f"Cannot autowire parameter '{param.name}' of {cls}")

            try:
                # Try to get existing service
                kwargs[param.name] = self.get(param_type.__name__)
            except NotFoundException:
                # If not registered, recursively autowire dependency
                kwargs[param.name] = self.autowire(param_type)

        # Create instance and cache it (singleton)
        instance = cls(**kwargs)
        self._services[name] = instance
        return instance

        instance = cls(**kwargs)
        self._services[name] = instance
        return instance

        self._services[name] = instance
        return instance

    def build_bundle(self, bundle) -> None:
        """Call bundle.build(container) hook to register bundle services."""
        bundle.build(self)
