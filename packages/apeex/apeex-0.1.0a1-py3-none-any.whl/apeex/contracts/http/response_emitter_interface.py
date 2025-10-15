from typing import Protocol
from apeex.contracts.http import ResponseInterface

class ResponseEmitterInterface(Protocol):
    def emit(self, response: ResponseInterface):
        ...