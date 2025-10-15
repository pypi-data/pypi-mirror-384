from typing import Any, Callable, Dict, List, Optional, Pattern, Union
import re


class Route:
    """
    Represents a single route definition in Apeex.
    """

    def __init__(
        self,
        path: str,
        methods: Optional[List[str]] = None,
        handler: Optional[Callable[..., Any]] = None,
        name: Optional[str] = None,
    ):
        self.path = path
        self.methods = [m.upper() for m in (methods or ["GET"])]
        self.handler = handler
        self.name = name or handler.__name__ if handler else None
        self._pattern, self._param_names = self._compile_path(path)

    def _compile_path(self, path: str) -> tuple[Pattern[str], List[str]]:
        """
        Convert path with `{param}` placeholders into a regex pattern.
        Example: "/users/{id}" → r"^/users/(?P<id>[^/]+)$"
        """
        param_names = re.findall(r"{(\w+)}", path)
        regex = re.sub(r"{(\w+)}", r"(?P<\1>[^/]+)", path)
        return re.compile(f"^{regex}$"), param_names

    def matches(self, path: str, method: str) -> Optional[Dict[str, str]]:
        """
        Return extracted parameters if route matches given path/method.
        Otherwise, return None.
        """
        if method.upper() not in self.methods:
            return None
        match = self._pattern.match(path)
        if match:
            return match.groupdict()
        return None

    def path_matches(self, path: str) -> bool:
        """Check if the route path pattern matches the given path (ignoring method)."""
        return bool(self._pattern.match(path))

    def __repr__(self) -> str:
        return f"<Route {self.methods} {self.path}>"

    def route(path: str, methods: list[str] | None = None, name: str | None = None):
        if methods is None:
            methods = ["GET"]

        def decorator(func):
            func.__route__ = {"path": path, "methods": methods, "name": name}
            return func

        return decorator

    def __call__(self, func):
        # Присваиваем информацию маршрута функции
        func.__route__ = {
            "path": self.path,
            "methods": self.methods,
            "name": self.name or func.__name__
        }
        return func