from typing import Any, Dict, Optional
from urllib.parse import parse_qs

class Request:
    """
    Represents an HTTP request in the Apeex framework.
    """
    def __init__(
        self,
        method: str,
        path: str,
        headers: Optional[Dict[str, str]] = None,
        query_string: Optional[str] = None,
        body: Any = None,
    ):
        self.method = method.upper()
        self.path = path
        self.headers = headers or {}
        self.query_string = query_string or ""
        self.body = body
        self._query_params = None

    @property
    def query_params(self) -> Dict[str, Any]:
        """Lazily parse query string into a dictionary."""
        if self._query_params is None:
            parsed = parse_qs(self.query_string, keep_blank_values=True)
            # Flatten single-element lists
            self._query_params = {k: v[0] if len(v) == 1 else v for k, v in parsed.items()}
        return self._query_params

    def get_header(self, name: str, default: Optional[str] = None) -> Optional[str]:
        return self.headers.get(name.lower(), default)

    @classmethod
    def from_scope(cls, scope: Dict[str, Any], body: Any = None) -> "Request":
        """
        Build a Request from ASGI scope (compatible with FastAPI/Starlette).
        """
        headers = {k.decode().lower(): v.decode() for k, v in scope.get("headers", [])}
        query_string = scope.get("query_string", b"").decode()
        return cls(
            method=scope["method"],
            path=scope["path"],
            headers=headers,
            query_string=query_string,
            body=body,
        )

    def get(self, name: str, default: Any = None) -> Any:
        """
        Get a value from query_params or headers by name.
        Tries query_params first, then headers.
        """
        print("apeex/http/Request", self.query_params)
        if name in self.query_params:
            return self.query_params[name]
        # Потом ищем в headers
        return self.headers.get(name.lower(), default)