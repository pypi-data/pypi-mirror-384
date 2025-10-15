from fastapi import APIRouter
from apeex.contracts.http import RouterInterface, RequestInterface
from apeex.http.route import Route
from typing import Any, Iterable, Mapping, Type, Optional
import inspect

class RouterAdapter(RouterInterface):
    def __init__(self):
        self._router = APIRouter()
        self._routes = []

    def add_route(self, path: str, methods: Iterable[str], handler: Any, name: str|None=None) -> None:
        self._router.add_api_route(path, handler, methods=list(methods), name=name)
        self._routes.append(Route(path, list(methods), handler, name))
        print(f"RouterAdapter: registered route {methods} {path} -> {getattr(handler, '__name__', handler)}")

    from typing import Type
    import inspect
    from apeex.container.container import Container

    def add_controller(self, controller_cls: Type, container: Container):
        """Scan methods with @Route decorator and register them."""
        controller = container.autowire(controller_cls)

        # Inspect class functions (to access original function attrs like __route__)
        for name, func in inspect.getmembers(controller_cls, inspect.isfunction):
            route_info = getattr(func, "__route__", None)

            if route_info:
                # Bind function to the controller instance
                bound_method = getattr(controller, name)
                self.add_route(
                    path=route_info["path"],
                    methods=route_info.get("methods", ["GET"]),
                    handler=bound_method,
                    name=route_info.get("name"),
                )

    def match(self, request: RequestInterface) -> Optional[Mapping[str, Any]]:
        path = getattr(request, "path", "/")
        method = getattr(request, "method", "GET").upper()

        for route in self._routes:
            params = route.matches(path, method)
            if params is not None:
                return {
                    "route": route,
                    "path_params": params,
                    "handler": route.handler,
                }
        return None
