from typing import Any, Callable, Dict, List, Optional
from apeex.http.route import Route
from apeex.http.exceptions import NotFound, MethodNotAllowed


class Router:
    """
    Simple HTTP router that matches paths and HTTP methods.
    """

    def __init__(self):
        self._routes: List[Route] = []

    def add_route(
        self,
        path: str,
        handler: Callable[..., Any],
        methods: Optional[List[str]] = None,
        name: Optional[str] = None,
    ):
        route = Route(path, methods, handler, name)
        self._routes.append(route)
        return route

    def get(self, path: str, handler: Callable[..., Any], name: Optional[str] = None):
        return self.add_route(path, handler, ["GET"], name)

    def post(self, path: str, handler: Callable[..., Any], name: Optional[str] = None):
        return self.add_route(path, handler, ["POST"], name)

    def match(self, path: str, method: str) -> tuple[Callable[..., Any], Dict[str, Any]]:
        """
        Try to match a request path/method.
        Returns (handler, params) or raises HttpException.
        """
        allowed_methods = set()

        for route in self._routes:
            params = route.matches(path, method)
            if params is not None:
                return route.handler, params

            # check if path matches, but method not allowed
            if route.path_matches(path):
                allowed_methods.update(route.methods)

        if allowed_methods:
            raise MethodNotAllowed(f"Method {method} not allowed for {path}")
        raise NotFound(f"No route matches {path}")

    def __iter__(self):
        yield from self._routes
