from __future__ import annotations

import inspect
import importlib
from typing import Any, Callable, Dict, Optional, get_type_hints

from apeex.http.request import Request
from apeex.http.response import Response
from apeex.http.route_match import RouteMatch
from apeex.http.exceptions import HttpException
from apeex.contracts.container import ContainerInterface
from apeex.contracts.http.router_interface import RouterInterface
from apeex.contracts.http.controller_resolver_interface import  ControllerResolverInterface
from apeex.contracts.http.request_interface import RequestInterface
from apeex.contracts.http.response_interface import ResponseInterface


class ControllerResolver(ControllerResolverInterface):
    """
    Resolves controller callables from route definitions.
    Supports function-based and class-based controllers.
    Provides autowiring of arguments from DI container and route params.
    """

    def __init__(self, container: ContainerInterface, router: RouterInterface):
        self.container = container
        self.router = router

    # ---------------------------------------------------------------------- #
    # Controller resolution
    # ---------------------------------------------------------------------- #

    def resolve(self, path: str, method: str) -> Optional[Callable]:
        # Создаём временный Request, чтобы вызвать match
        request = Request(method=method, path=path, headers={}, body=None)
        print(f"ControllerResolver.resolve: try {method} {path}")
        route_data = self.router.match(request)
        if not route_data:
            print("ControllerResolver.resolve: no route matched")
            return None
        print(f"ControllerResolver.resolve: matched {route_data['route']}")

        route_match = RouteMatch(
            route=route_data["route"],
            path_params=route_data.get("path_params", {}),
            controller=route_data["handler"]
        )
        return self._resolve_route_match(route_match)

    def _resolve_route_match(self, route_match: RouteMatch) -> Callable[[RequestInterface], ResponseInterface]:
        """
        Resolve controller from RouteMatch to callable.
        Supports function, class-based, and string references.
        """
        controller = route_match.controller_callable

        if isinstance(controller, str):
            controller = self._import_controller(controller)

        if inspect.isclass(controller):
            controller_instance = self.container.autowire(controller)
            return self._wrap_callable(controller_instance, "index", route_match)

        if callable(controller):
            return self._wrap_function(controller, route_match)

        raise HttpException(f"Unsupported controller type: {controller}")

    # ---------------------------------------------------------------------- #
    # Internal helpers
    # ---------------------------------------------------------------------- #

    def _import_controller(self, path: str) -> Any:
        """
        Import controller from string like 'app.demo_bundle.controllers.hello_controller:hello'
        or 'app.demo_bundle.controllers.HelloController::index'
        """
        if "::" in path:
            module_path, class_method = path.split("::", 1)
            module = importlib.import_module(module_path)
            cls = getattr(module, class_method.split(".")[0])
            return cls

        if ":" in path:
            module_path, func_name = path.split(":", 1)
            module = importlib.import_module(module_path)
            return getattr(module, func_name)

        raise HttpException(f"Invalid controller path: {path}")

    def _wrap_function(self, func: Callable, route_match: RouteMatch) -> Callable:
        """
        Wrap a function controller to inject dependencies and request.
        """

        def wrapper(request: RequestInterface) -> ResponseInterface:
            kwargs = self._build_kwargs(func, request, route_match.path_params)
            result = func(**kwargs)
            return self._normalize_response(result)

        return wrapper

    def _wrap_callable(self, instance: Any, method_name: str, route_match: RouteMatch) -> Callable:
        """
        Wrap a class-based controller method.
        """
        if not hasattr(instance, method_name):
            raise HttpException(f"Controller {instance.__class__.__name__} has no method '{method_name}'")

        method = getattr(instance, method_name)

        def wrapper(request: RequestInterface) -> ResponseInterface:
            kwargs = self._build_kwargs(method, request, route_match.path_params)
            result = method(**kwargs)
            return self._normalize_response(result)

        return wrapper

    def _build_kwargs(
        self, callable_obj: Callable, request: RequestInterface, path_params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build arguments for controller call using type hints and path params.
        """

        sig = inspect.signature(callable_obj)
        type_hints = get_type_hints(callable_obj)
        kwargs = {}

        for name, param in sig.parameters.items():
            if name in path_params:
                kwargs[name] = path_params[name]
            elif name == "request":
                kwargs[name] = request
            else:
                if name in type_hints and type_hints[name] == RequestInterface:
                    kwargs[name] = request
                else:
                    if self.container.has(name):
                        kwargs[name] = self.container.get(name)
        return kwargs

    def _normalize_response(self, result):
        """
        Converts the controller's result to a Response object.
        """
        # Если контроллер уже вернул Response
        if isinstance(result, Response):
            return result

        # Если контроллер вернул словарь — считаем это JSON
        if isinstance(result, dict):
            return Response.json(result)

        # Если контроллер вернул строку — обычный текстовый ответ
        if isinstance(result, str):
            return Response.text(result)

        # Если None — 204 No Content
        if result is None:
            return Response(status_code=204)

        # Если что-то другое — оборачиваем в текст
        return Response.text(str(result))