# apeex/bundles/bundle.py
from apeex.contracts.container import ContainerInterface
from abc import ABC, abstractmethod

class Bundle(ABC):
    @abstractmethod
    def build(self, container: ContainerInterface) -> None:
        pass

    @abstractmethod
    def boot(self, kernel) -> None:
        """Accept kernel as argument to avoid circular import"""
        pass

    @abstractmethod
    def shutdown(self) -> None:
        pass
