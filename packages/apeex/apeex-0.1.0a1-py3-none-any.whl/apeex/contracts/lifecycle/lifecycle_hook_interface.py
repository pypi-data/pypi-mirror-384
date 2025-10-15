from typing import Protocol

class LifecycleHookInterface(Protocol):
    """
    Маркер для сервисов, которым нужно вызвать init() после сборки контейнера
    """
    def init(self) -> None: ...
