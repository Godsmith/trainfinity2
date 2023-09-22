from dataclasses import dataclass

from typing import Callable

from trainfinity2.mode import Mode


@dataclass
class Box:
    text: str
    callback: Callable[..., None]
    callback_args: list
    mode: Mode | None = None

    def click(self):
        self.callback(*self.callback_args)
