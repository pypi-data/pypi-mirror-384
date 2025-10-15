"""
FastAPIResponseAdapter

Adapter to wrap FastAPI Response into our ResponseInterface.
Allows using FastAPI Response objects within the Apeex framework
independently of FastAPI.
"""

from fastapi import Response
from apeex.contracts.http import ResponseInterface
from typing import Optional, Dict

class FastAPIResponseAdapter(ResponseInterface):
    def __init__(self, response: Response):
        self.status_code = response.status_code
        self.headers = dict(response.headers)
        self.body = response.body

    @classmethod
    def from_body(cls, body: bytes, status: int = 200, headers: Optional[Dict[str, str]] = None):
        """
        Creates an adapted Response from raw body, status, and headers.
        """
        return cls(Response(content=body, status_code=status, headers=headers))
