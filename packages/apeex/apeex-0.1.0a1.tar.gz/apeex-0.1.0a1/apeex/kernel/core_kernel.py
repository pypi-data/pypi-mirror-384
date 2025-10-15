from typing import List, Optional
from apeex.contracts.container import ContainerInterface
from apeex.contracts.http.router_interface import RouterInterface
from apeex.bundles.bundle import Bundle
from apeex.utils.bundles_discovery import discover_entrypoint_bundles, discover_local_bundles
import inspect

class CoreKernel:
    """
    Core application Kernel.
    Manages container, bundles, and application lifecycle.
    """
    def __init__(self, container: ContainerInterface):
        self.container = container
        self.bundles: List[Bundle] = []
        self.router: Optional[RouterInterface] = None

    def register_bundle(self, bundle: Bundle):
        self.bundles.append(bundle)

    def bootstrap(self):
        """Initialize configuration and container"""
        # Use the kernel's container, not a new one
        container = self.container

        # Auto-register bundles (entry points + local)
        for bundle_cls in discover_entrypoint_bundles():
            self.register_bundle(bundle_cls())
        for bundle_cls in discover_local_bundles():
            self.register_bundle(bundle_cls())

        # Register services from config
        from config.services import SERVICES
        for name, factory in SERVICES.items():
            if container.has(name):
                continue
            # Если это класс — создаём экземпляр без аргументов
            if inspect.isclass(factory):
                container.set(name, factory())
                continue
            # Если это вызываемый объект (функция/лямбда), проверим сигнатуру
            if callable(factory):
                sig = inspect.signature(factory)
                if len(sig.parameters) == 0:
                    container.set(name, factory())
                else:
                    container.set_factory(name, lambda f=factory, c=container: f(c))
                continue
            # Иначе считаем это уже готовым инстансом
            container.set(name, factory)

        # Build all bundles
        for bundle in self.bundles:
            bundle.build(container)

    def boot(self):
        """Boot all bundles"""
        for bundle in self.bundles:
            bundle.boot(self)

    def shutdown(self):
        """Shutdown all bundles"""
        for bundle in self.bundles:
            bundle.shutdown()

    def register_router(self, router: RouterInterface):
        """
        Register a router to collect all bundle routes.
        """
        self.router = router

    def build_routes(self):
        """
        Collect routes from all registered bundles and add them to the router.
        """
        if not hasattr(self, "router"):
            raise RuntimeError("Router is not registered in Kernel")

        for bundle in self.bundles:
            if hasattr(bundle, "get_routes"):
                for route in bundle.get_routes():
                    self.router.add_route(**route)