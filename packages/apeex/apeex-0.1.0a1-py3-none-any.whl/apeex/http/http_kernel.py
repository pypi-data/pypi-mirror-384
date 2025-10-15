from typing import Optional, Mapping

from apeex.contracts.http import RequestInterface, ResponseInterface
from apeex.contracts.http.controller_resolver_interface import ControllerResolverInterface
from apeex.contracts.http.http_kernel_interface import HttpKernelInterface
from apeex.contracts.container import ContainerInterface
from apeex.http.request import Request
import json
from starlette.responses import Response
from apeex.http.response import Response as ApeexResponse


class SimpleResponse(ResponseInterface):
    def __init__(self, body: bytes, status_code: int = 200, headers: Optional[Mapping[str, str]] = None):
        self.body = body
        self.status_code = status_code
        self.headers = headers or {}

    @classmethod
    def from_body(cls, body, status: int = 200, headers: Optional[Mapping[str, str]] = None) -> "SimpleResponse":
        if isinstance(body, (dict, list)):
            body_bytes = json.dumps(body).encode("utf-8")
        elif isinstance(body, str):
            body_bytes = body.encode("utf-8")
        elif isinstance(body, bytes):
            body_bytes = body
        else:
            body_bytes = str(body).encode("utf-8")
        return cls(body_bytes, status, headers)

    def to_fastapi_response(self) -> Response:
        """Конвертирует SimpleResponse в Starlette/FastAPI Response"""
        return Response(
            content=self.body,
            status_code=self.status_code,
            headers=self.headers,
            media_type="application/json"
        )


class HttpKernel(HttpKernelInterface):
    """Minimal HTTP kernel implementing HttpKernelInterface."""

    def __init__(self, container: ContainerInterface):
        self.container = container
        self.resolver: ControllerResolverInterface = container.get("controller_resolver")

    def create_request_from_asgi(self, scope: dict, body: bytes):
        method = scope.get("method", "GET")
        path = scope.get("path", "/")
        headers_list = scope.get("headers", [])
        headers = {k.decode(): v.decode() for k, v in headers_list}

        query_string_bytes = scope.get("query_string", b"")
        query_string = query_string_bytes.decode() if isinstance(query_string_bytes, bytes) else str(query_string_bytes)

        return Request(
            method=method,
            path=path,
            headers=headers,
            query_string=query_string,
            body=body
        )

    def handle(self, request: RequestInterface) -> ResponseInterface:
        controller_callable = self.resolver.resolve(request.path, request.method)

        if controller_callable is None:
            return SimpleResponse.from_body({"error": "Not Found"}, status=404)

        result = controller_callable(request)

        # Support Apeex Response object by converting to SimpleResponse
        if isinstance(result, ApeexResponse):
            body = result.content
            if isinstance(body, str):
                body = body.encode("utf-8")
            elif not isinstance(body, (bytes, bytearray)):
                body = str(body).encode("utf-8")
            return SimpleResponse(body=body, status_code=result.status_code, headers=result.headers)

        if not isinstance(result, ResponseInterface):
            result = SimpleResponse.from_body(result)

        return result
