from starlette.responses import Response as StarletteResponse
from apeex.contracts.http import ResponseInterface
from apeex.contracts.http.response_emitter_interface import ResponseEmitterInterface

class FastAPIResponseEmitter(ResponseEmitterInterface):
    def emit(self, response: ResponseInterface):
        return StarletteResponse(
            content=response.body,
            status_code=response.status_code,
            headers=response.headers,
        )