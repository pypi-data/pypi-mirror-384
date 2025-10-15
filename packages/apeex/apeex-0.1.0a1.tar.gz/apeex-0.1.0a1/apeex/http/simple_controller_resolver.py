from typing import Callable, Optional
from apeex.contracts.http.controller_resolver_interface import ControllerResolverInterface
from apeex.contracts.http import RequestInterface
from apeex.contracts.http import ResponseInterface


class SimpleControllerResolver(ControllerResolverInterface):
    def __init__(self):
        self.routes: dict[tuple[str, str], Callable[[RequestInterface], ResponseInterface]] = {}

    def add_route(self, path: str, method: str, controller: Callable[[RequestInterface], ResponseInterface]):
        self.routes[(path, method.upper())] = controller

    def get_controller(self, path: str, method: str) -> Optional[Callable[[RequestInterface], ResponseInterface]]:
        return self.routes.get((path, method.upper()))

    # NEW
    def resolve(self, path: str, method: str) -> Optional[Callable[[RequestInterface], ResponseInterface]]:
        return self.get_controller(path, method)
