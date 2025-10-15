from typing import List
import click
from apeex.contracts.cli import CommandRunnerInterface

class CommandRunnerAdapter(CommandRunnerInterface):
    """
    Адаптер для выполнения CLI команд через Click.
    Ядро не зависит от Click напрямую.
    """
    def __init__(self, commands: List[click.Command] = None):
        self.commands = commands or []

    def add_command(self, command: click.Command):
        """
        Позволяет добавлять новые CLI команды.
        """
        self.commands.append(command)

    def run(self, argv: List[str]) -> int:
        """
        Запуск CLI с аргументами argv
        """
        @click.group()
        def cli_group():
            pass

        # Регистрация всех команд
        for cmd in self.commands:
            cli_group.add_command(cmd)

        # Запуск CLI
        try:
            cli_group(prog_name="apeex", args=argv)
            return 0
        except SystemExit as e:
            return e.code
