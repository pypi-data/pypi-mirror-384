"""
FastAPIRequestAdapter

Adapter to wrap FastAPI Request into our RequestInterface.
Allows using FastAPI Request objects within the Apeex framework
without coupling directly to FastAPI.
"""

from fastapi import Request
from apeex.contracts.http import RequestInterface
from typing import Any

class FastAPIRequestAdapter(RequestInterface):
    def __init__(self, request: Request):
        self._request = request
        self.method = request.method
        self.path = request.url.path
        self.headers = dict(request.headers)
        self.query_params = dict(request.query_params)
        self.body = b""

    async def get(self, name: str, default: Any = None) -> Any:
        """
        Returns the value of the query parameter with the given name.
        """
        return self.query_params.get(name, default)
