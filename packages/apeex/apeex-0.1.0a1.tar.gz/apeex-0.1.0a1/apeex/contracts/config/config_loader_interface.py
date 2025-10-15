from typing import Protocol, Any, Mapping

class ConfigLoaderInterface(Protocol):
    def load(self, path: str) -> Mapping[str, Any]: ...