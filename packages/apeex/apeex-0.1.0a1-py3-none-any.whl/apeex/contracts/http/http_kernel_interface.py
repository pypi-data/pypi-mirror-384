from typing import Protocol
from apeex.contracts.http import RequestInterface
from apeex.contracts.http import ResponseInterface

class HttpKernelInterface(Protocol):
    async def handle(self, request: RequestInterface) -> ResponseInterface: ...