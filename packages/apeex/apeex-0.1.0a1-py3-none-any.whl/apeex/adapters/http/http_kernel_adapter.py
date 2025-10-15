"""
HttpKernelAdapter

Adapter to integrate FastAPI with the Apeex HttpKernelInterface.
Allows using FastAPI under the hood while keeping the ability
to swap out the HTTP engine for another implementation.
"""

from fastapi import FastAPI
from apeex.contracts.http import HttpKernelInterface, RequestInterface, ResponseInterface
from apeex.contracts.http.router_interface import RouterInterface
from .response_adapter import FastAPIResponseAdapter

class HttpKernelAdapter(HttpKernelInterface):
    def __init__(self, app: FastAPI, router: RouterInterface):
        self._app = app
        self._router = router

    async def handle(self, request: RequestInterface) -> ResponseInterface:
        """
        Handles an HTTP request and returns a ResponseInterface.
        For the MVP, it simply returns an "OK" response.
        In the future, routing and controller dispatching can be added here.
        """
        return FastAPIResponseAdapter.from_body(b"OK")
