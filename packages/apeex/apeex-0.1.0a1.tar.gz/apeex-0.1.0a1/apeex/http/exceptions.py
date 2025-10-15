class HttpException(Exception):
    """Base class for all HTTP exceptions."""
    status_code = 500
    default_message = "Internal Server Error"

    def __init__(self, message: str = None, status_code: int = None):
        super().__init__(message or self.default_message)
        if status_code:
            self.status_code = status_code


class NotFound(HttpException):
    status_code = 404
    default_message = "Not Found"


class MethodNotAllowed(HttpException):
    status_code = 405
    default_message = "Method Not Allowed"
