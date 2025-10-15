from typing import Protocol, Mapping, runtime_checkable

@runtime_checkable
class ResponseInterface(Protocol):
    status_code: int
    headers: Mapping[str, str]
    body: bytes
    @classmethod
    def from_body(cls, body: bytes, status: int=200, headers: Mapping[str,str]|None=None) -> "ResponseInterface": ...
