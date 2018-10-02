import array
import base64
import fcntl
import sys
import termios
from contextlib import contextmanager
from typing import Tuple

import blessed

from . import data


class KittyAnswerError(Exception):
    def __init__(self, from_code: str, answer: str):
        super().__init__(f"{from_code!r} : terminal responded with {answer!r}")


class PixTerminal(blessed.Terminal):
    actions_with_answer = data.ACTIONS_WITH_ANSWER
    img_controls        = data.IMAGE_CONTROLS
    esc                 = data.ESC


    @property
    def size(self) -> Tuple[int, int]:
        return (self.width, self.height)


    @property
    def px_size(self) -> Tuple[int, int]:
        buf = array.array("H", [0, 0, 0, 0])
        fcntl.ioctl(sys.stdout, termios.TIOCGWINSZ, buf)
        return (buf[2], buf[3])

    @property
    def px_width(self) -> int:
        return self.px_size[0]

    @property
    def px_height(self) -> int:
        return self.px_size[1]


    @property
    def cell_px_size(self) -> Tuple[int, int]:
        return (self.px_width // self.width, self.px_height // self.height)

    @property
    def cell_px_width(self) -> int:
        return self.cell_px_size[0]

    @property
    def cell_px_height(self) -> int:
        return self.cell_px_size[1]


    def get_code(self, payload: str = "", **controls: str) -> str:
        real_keys = {
            self.img_controls[k][0]:
                self.img_controls[k][1][v] if self.img_controls[k][1] else v

            for k, v in controls.items()
        }

        keys_str = ",".join([f"{k}={v}" for k, v in real_keys.items()])

        if payload:
            payload = str(base64.b64encode(bytes(payload, "utf-8")), "utf-8")

        # print("%r" % f"{ESC}_G{keys_str};{payload}{ESC}\\")
        return f"{self.esc}_G{keys_str};{payload}{self.esc}\\"


    def run_code(self, payload: str = "", **controls: str) -> None:
        code = self.get_code(payload, **controls)
        print(code)

        if controls.get("action", "transmit") not in self.actions_with_answer:
            return

        # Catch responses kitty print on stdin:
        chars = []
        while True:
            with self.cbreak():
                char = sys.stdin.read(1)
                chars.append(char)
                if char == "\\":
                    break

        self._handle_response(code, "".join(chars))


    @staticmethod
    def _handle_response(from_code: str, answer: str) -> None:
        if answer and ";OK" not in answer:
            raise KittyAnswerError(from_code, answer)


    # y then x for those because blessings does it like that for some reason
    def move_relative(self, y: int = 0, x: int = 0) -> str:
        cursor_y, cursor_x = self.get_location()
        return self.move(cursor_y + y, cursor_x + x)

    def move_relative_x(self, x: int = 0) -> str:
        cursor_y, cursor_x = self.get_location()
        return self.move(cursor_y, cursor_x + x)

    def move_relative_y(self, y: int = 0) -> str:
        cursor_y, cursor_x = self.get_location()
        return self.move(cursor_y + y, cursor_x)


    @contextmanager
    def location_relative(self, x: int = 0, y: int = 0) -> str:
        cursor_y, cursor_x = self.get_location()
        with self.location(x=cursor_x + x, y=cursor_y + y):
            yield


    def align(self, text: str, align: str = "left") -> str:
        if align == "left":
            return self.ljust(text)

        if align == "center":
            return self.center(text)

        if align == "right":
            return self.rjust(text)

        raise ValueError("Alignement must be 'left', 'center' or 'right'.")


TERM = PixTerminal()
