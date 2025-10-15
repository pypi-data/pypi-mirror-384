from __future__ import annotations
from typing import Any, Callable, Dict, Optional
from apeex.http.route import Route


class RouteMatch:
    """
    Represents a successful route match result.
    Holds the matched Route, path parameters, and resolved controller.
    """

    def __init__(
        self,
        route: Route,
        path_params: Optional[Dict[str, Any]] = None,
        controller: Optional[Callable[..., Any]] = None,
    ):
        self.route = route
        self.path_params: Dict[str, Any] = path_params or {}
        self.controller_callable: Callable[..., Any] = controller or route.controller

    def __repr__(self) -> str:
        return f"<RouteMatch path='{self.route.path}' params={self.path_params}>"
