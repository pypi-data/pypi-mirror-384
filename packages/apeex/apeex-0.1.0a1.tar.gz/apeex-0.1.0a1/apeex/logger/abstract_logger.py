from abc import abstractmethod
from apeex.logger import LoggerInterface
from typing import Any, Dict


class AbstractLogger(LoggerInterface):
    """Base class implementing all LoggerInterface methods except `log()`."""

    @abstractmethod
    def log(self, level: str, message: str, context: Dict[str, Any] = None):
        """Subclasses must implement the actual logging logic."""
        raise NotImplementedError

    def emergency(self, message: str, context: Dict[str, Any] = None):
        self.log("emergency", message, context)

    def alert(self, message: str, context: Dict[str, Any] = None):
        self.log("alert", message, context)

    def critical(self, message: str, context: Dict[str, Any] = None):
        self.log("critical", message, context)

    def error(self, message: str, context: Dict[str, Any] = None):
        self.log("error", message, context)

    def warning(self, message: str, context: Dict[str, Any] = None):
        self.log("warning", message, context)

    def notice(self, message: str, context: Dict[str, Any] = None):
        self.log("notice", message, context)

    def info(self, message: str, context: Dict[str, Any] = None):
        self.log("info", message, context)

    def debug(self, message: str, context: Dict[str, Any] = None):
        self.log("debug", message, context)
