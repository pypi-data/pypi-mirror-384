from typing import Protocol, Callable, Optional
from apeex.contracts.http import RequestInterface
from apeex.contracts.http import ResponseInterface

# ----------------------------
# Интерфейс ControllerResolver
# ----------------------------
class ControllerResolverInterface(Protocol):
    """
    Интерфейс для реализации маршрута в контроллере.
    """
    def get_controller(self, path: str, method: str) -> Optional[Callable[[RequestInterface], ResponseInterface]]:
        ...

    def resolve(self, path: str, method: str) -> Optional[Callable]:
        ...