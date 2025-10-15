from typing import Protocol, List

class CommandRunnerInterface(Protocol):
    def run(self, argv: List[str]) -> int: ...
