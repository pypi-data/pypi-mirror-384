from apeex.bundles.bundle import Bundle
from apeex.contracts.container import ContainerInterface
from apeex.adapters.http.router_adapter import RouterAdapter
from .services.hello_services import HelloService
from .controllers.hello_controller import HelloController

class DemoBundle(Bundle):
    def build(self, container: ContainerInterface) -> None:

        # Register HelloService
        container.set("HelloService", HelloService())
        # Use existing router from container
        router: RouterAdapter = container.get("router")

        router.add_controller(HelloController, container)

    def boot(self, kernel) -> None:
        pass

    def shutdown(self) -> None:
        pass
