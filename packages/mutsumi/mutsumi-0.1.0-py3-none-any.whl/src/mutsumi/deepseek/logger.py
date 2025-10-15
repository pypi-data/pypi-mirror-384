import logging
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown

__all__ = ['console_logger', 'DeepSeekLogger']

class ConsoleWrapper(Console):
    def write(self, s:str) -> None:
        self.print(s, end="")

console_handler = logging.StreamHandler(ConsoleWrapper())

console_logger = logging.Logger("console")
console_logger.addHandler(console_handler)


log_dir = Path("log").absolute()
if log_dir.exists():
    if not log_dir.is_dir():
        raise OSError(f"'{log_dir} exists but not a dir.'")
else:
    log_dir.mkdir()


class DeepSeekLogger(logging.Logger):
    def __init__(self, name: str) -> None:
        super().__init__(name, logging.DEBUG)
        self.formatter = logging.Formatter(
            "[%(asctime)s %(levelname)s:%(name)s] %(message)s",
            "%Y-%m-%d %H:%M:%S",
        )

        self.file_handler = logging.FileHandler(log_dir / ("deepseek_" + name + ".log"))
        self.file_handler.setLevel(logging.DEBUG)
        self.file_handler.setFormatter(self.formatter)

        self.console_handler = logging.StreamHandler(ConsoleWrapper())
        self.console_handler.setLevel(logging.INFO)
        self.console_handler.setFormatter(self.formatter)

        self.addHandler(self.file_handler)
        self.addHandler(self.console_handler)
        return

