from typing import Protocol, Mapping, Any

class RequestInterface(Protocol):
    method: str
    path: str
    headers: Mapping[str, str]
    query_params: Mapping[str, str]
    body: bytes
    def get(self, name: str, default: Any=None) -> Any: ...