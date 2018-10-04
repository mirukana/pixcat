# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

import math
import textwrap
from typing import AnyStr, Callable, Iterable, Optional, Union

import ansiwrap
from ansiwrap import ansilen
from dataclasses import dataclass, field

from . import Image
from .terminal import TERM

FromCallable = Union[None, Image, AnyStr]
CellType     = Union[None, Image, AnyStr, Callable[["Grid"], FromCallable]]


@dataclass
class Grid:
    cells: Iterable[CellType] = field()

    cell_w:   int           = 256  # TODO: accept val in cols/rows
    cell_h:   int           = 256
    max_cols: Optional[int] = None
    max_rows: Optional[int] = None

    text_overflow:   str = "wrap"  # wrap or shorten
    cut_placeholder: str = " …"

    raise_errors: bool = False
    print_errors: bool = True


    @property
    def cell_cols(self) -> int:
        return math.ceil(self.cell_w / TERM.cell_px_width)

    @property
    def cell_rows(self) -> int:
        return math.ceil(self.cell_h / TERM.cell_px_height)

    @property
    def cells_per_row(self) -> int:
        if self.max_cols:
            return self.max_cols

        return max(1, math.floor(TERM.width / self.cell_cols))


    def show(self) -> "Grid":
        # We have to handle y/rows manually because of forced blank lines,
        # terminal scrolling, etc; but x/columns are no trouble.
        start_x = x = TERM.get_location()[1]

        printed_rows = 0

        for index, cell in enumerate(self.cells):

            last_in_row   = index % self.cells_per_row == 0
            one_per_row   = self.cells_per_row < 2
            first_in_row  = index == 0

            if last_in_row and (one_per_row or not first_in_row):
                # Print enough lines to begin a new row below the previous one
                TERM.print_esc("\n" * self.cell_rows)

                printed_rows += 1

                if self.max_rows and printed_rows > self.max_rows:
                    break

                x = start_x

            content: FromCallable = self._get_content(cell)

            if isinstance(content, Image):
                content_cols = content.cols
                content_rows = content.rows
            elif not content:
                content_cols = content_rows = 0
            else:
                content_cols = ansilen(max(content.splitlines(), key=ansilen))
                content_rows = ansilen(content.splitlines())

            # Calculate paddings inside the cell to align the content
            inner_x = round((self.cell_cols / 2) - (content_cols / 2))
            inner_y = math.floor((self.cell_rows / 2) - (content_rows / 2))

            # Print the vertical padding as blank lines
            TERM.print_esc("\n" * inner_y)

            if isinstance(content, Image):
                content.show(x = x + inner_x, z=-1)
            else:
                print(textwrap.indent(content, " " * (x + inner_x)))

            # If needed, print blank lines to "complete the cell",
            # i.e. content height didn't fill it.
            # The cursor needs to always be at the cell row's bottom,
            # for the next "put back" escape code to work properly.
            TERM.print_esc("\n" * (self.cell_rows - content_rows - inner_y))

            # "Undo" any terminal scrolling and put cursor back to the row
            # beginning so we can print more content in line.
            TERM.print_esc(TERM.move_relative_y(-self.cell_rows - 1))

            x += self.cell_cols

        TERM.print_esc("\n" * self.cell_rows)
        return self


    def _get_content(self, cell: CellType) -> Union[Image, str]:
        if cell is None:
            return ""

        if isinstance(cell, Callable):
            return self._get_content(cell(self))

        if isinstance(cell, Image):
            return self._get_resized_image(cell)

        return self._get_text(cell)


    def _get_resized_image(self, image: Image) -> Image:
        try:
            return image.resize(1, 1, self.cell_w, self.cell_h)

        except Exception as err:
            if self.raise_errors:
                raise

            if self.print_errors:
                print(TERM.red("%s: %s" % (type(err).__name__, err)))


    def _get_text(self, text: AnyStr) -> str:
        assert self.text_overflow in ("wrap", "shorten")

        lines = getattr(ansiwrap, self.text_overflow)(
            str(text),
            width              = self.cell_cols,
            placeholder        = self.cut_placeholder,
            tabsize            = 4,
            replace_whitespace = False,
            drop_whitespace    = False
        )

        if isinstance(lines, str):  # shorten returns a str, wrap a list
            return lines

        lines = [l for line in lines for l in line.splitlines()]
        return "\n".join(lines[:self.cell_rows])
