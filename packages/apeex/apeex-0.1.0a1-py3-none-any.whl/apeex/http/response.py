from typing import Any, Dict, Optional


class Response:
    """
    Represents an HTTP response in the Apeex framework.
    """
    def __init__(
        self,
        content: Any,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
    ):
        self.content = content
        self.status_code = status_code
        self.headers = headers or {"Content-Type": "text/plain; charset=utf-8"}

    def set_header(self, name: str, value: str):
        self.headers[name] = value

    @classmethod
    def json(cls, data: Any, status_code: int = 200) -> "Response":
        import json
        return cls(json.dumps(data, ensure_ascii=False), status_code, {"Content-Type": "application/json"})

    @classmethod
    def text(cls, text: str, status_code: int = 200) -> "Response":
        return cls(text, status_code, {"Content-Type": "text/plain; charset=utf-8"})
