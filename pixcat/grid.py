# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

import math
from typing import AnyStr, Callable, Iterable, Optional, Union

from . import Image
from .terminal import TERM

CellType = Union[Image, Callable, AnyStr]


def show(cells:         Iterable[CellType],
         cell_w:        int           = 256,
         cell_h:        int           = 256,
         max_cols:      Optional[int] = None,
         max_rows:      Optional[int] = None,
         raise_errors:  bool          = False,
         print_errors:  bool          = True) -> None:

    auto_calc_cols = True if max_rows is None else False

    # We have to handle y/rows manually because of forced blank lines,
    # terminal scrolling, etc; but x/columns are no trouble.
    start_x = x = TERM.get_location()[1]

    printed_rows = 0

    for index, cell in enumerate(cells):
        # Update every time in case user resizes terminal
        cell_cols = math.ceil(cell_w / TERM.cell_px_width)
        cell_rows = math.ceil(cell_h / TERM.cell_px_height)

        if auto_calc_cols:
            max_cols = max(1, math.floor(TERM.width / cell_cols))


        # If we're over the max cells per row allowed for this cell and
        # this isn't the first cell, unless only one cell per column:
        if index % max_cols == 0 and ((max_cols < 2 and True) or (index > 0)):
            printed_rows += 1

            # Print enough lines to begin a new row below the previous one
            TERM.print_esc("\n" * cell_rows)

            if max_rows and printed_rows > max_rows:
                break

            x = start_x


        try:
            resized = cell.resize(1, 1, cell_w, cell_h)
        except Exception as err:
            if raise_errors:
                raise
            if print_errors:
                print(TERM.red("%s: %s" % (type(err).__name__, err)))


        # Calculate paddings inside the cell to align the image
        inner_x = round(cell_cols / 2) - round(resized.cols / 2)
        inner_y = round(cell_rows / 2) - round(resized.rows / 2)

        # Print the vertical padding as blank lines
        TERM.print_esc("\n" * inner_y)

        resized.show(x = x + inner_x)

        # If needed, print blank lines to "complete the cell",
        # i.e. image height didn't fill it. Take padding into consideration.
        # The cursor needs to always be at the cell row's bottom,
        # for the next "put back" escape code to work properly.
        TERM.print_esc("\n" * (cell_rows - resized.rows - inner_y))

        # "Undo" any terminal scrolling and put cursor back to the row
        # beginning so we can print more images in line.
        TERM.print_esc(TERM.move_relative_y(-cell_rows - 1))

        x += cell_cols
