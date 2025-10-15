from typing import Protocol

class MigrationRunnerInterface(Protocol):
    def migrate(self) -> None: ...
