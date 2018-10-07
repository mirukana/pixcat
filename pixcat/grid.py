# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

# Pylint doesn't recognize Axis as a list
# pylint: disable=unsubscriptable-object

# General rule for Size-based cursor movements:
# use .floor_cell() for paddings, .ceil_cell() for the rest

import math
from collections import UserList
from typing import AnyStr, Callable, Iterable, List, Optional, Tuple, Union

import ansiwrap
from ansiwrap import ansilen
from dataclasses import dataclass, field

from . import Image
from .size import HSize, TermHSize, TermVSize, VSize
from .terminal import TERM

ReturnedContent = Union[Image, AnyStr]
Content         = Union[None, Image, AnyStr,
                        Callable[["Grid"], ReturnedContent]]

ColSize   = Union[HSize, TermHSize]
RowSize   = Union[VSize, TermVSize]
AlignSize = Union[HSize, VSize]
Cell      = Union["Column", "Row"]
AxisCell  = Union[Cell, Callable[["Axis", int], Cell]]


@dataclass
class Column:
    size:  ColSize = HSize(256)
    align: str     = "center"  # left, center, right


@dataclass
class Row:
    size:  RowSize = VSize(256)
    align: str     = "center" # top, center or right


@dataclass
class Axis(UserList):
    data:        List[AxisCell] = field(default_factory=list)
    wrap_around: bool           = False

    def __getitem__(self, index):
        try:
            item = self.data[index]
        except IndexError:
            item = self.data[index % len(self) if self.wrap_around else -1]

        return item(self, index) if callable(item) else item



@dataclass
class Grid:
    cols: Axis = field(default=Axis([Column(HSize(px=256))]))
    rows: Axis = field(default=Axis([Row(VSize(px=256))]))

    max_cols: Optional[int] = None
    max_rows: Optional[int] = None

    force_even: bool = False
    force_odd:  bool = False

    text_overflow:   str = "wrap"  # wrap or shorten
    cut_placeholder: str = " …"

    raise_errors: bool = False
    print_errors: bool = True


    @property
    def cells_per_row(self) -> int:
        if self.max_cols:
            can_fit = self.max_cols
        else:
            term_w = TermHSize()
            index  = at_col = can_fit = 0

            while True:
                to_col = self.cols[index].size

                if at_col + to_col > term_w - TERM.cell_px_width:
                    break

                at_col  += to_col
                can_fit += 1
                index   += 1

        if self.force_even:
            # Nearest even number down, e.g. 3 → 2
            return max(2, math.floor(can_fit / 2.0) * 2)

        if self.force_odd:
            # Nearest odd number down, e.g. 4 → 3, 3 → 3
            return max(1, can_fit - 1 if can_fit % 2 == 0 else can_fit)

        return max(1, can_fit)


    def show(self, contents: Iterable[Content]) -> "Grid":
        col = row = 0

        for content in contents:
            restore_x = TERM.move_x(TERM.get_location()[1] - 1)

            self._show_content(*self._get_content(content, col, row), col, row)

            # "Undo" any terminal scrolling and put cursor back to the row
            # beginning so we can print more content in line.
            TERM.print_esc(
                TERM.move_relative_y(
                    -self.rows[row].size.ceil_cell().cells
                ),
                restore_x
            )

            # Advance the cursor x position in the row
            TERM.print_esc(
                TERM.move_relative_x(self.cols[col].size.ceil_cell().cells)
            )

            col += 1

            if col >= self.cells_per_row:
                TERM.print_esc("\n" * self.rows[row].size.ceil_cell().cells)

                col  = 0
                row += 1

                if self.max_rows and row > self.max_rows:
                    break

        TERM.print_esc("\n" * self.rows[row].size.ceil_cell().cells)
        return self


    def _get_content(self, cell: Content, col: int, row: int
                    ) -> Tuple[ReturnedContent, HSize, VSize]:
        if cell is None:
            return ("", HSize(0), VSize(0))

        if isinstance(cell, Callable):
            return self._get_content(cell(self), col, row)

        if isinstance(cell, Image):
            img = self._get_resized_image(cell, col, row)
            return (img, img.width, img.height)

        text         = self._get_text(cell, col, row)
        longest_line = ansilen(max(text.splitlines(), key=ansilen))
        num_lines    = ansilen(text.splitlines())
        return (text, HSize(cells=longest_line), VSize(cells=num_lines))


    def _get_resized_image(self, cell: Image, col: int, row: int) -> Image:
        try:
            return cell.resize(
                HSize(px=1), VSize(px=1),
                # TODO: change this to use new Size stuff
                self.cols[col].size, self.rows[row].size
            )

        except Exception as err:
            if self.raise_errors:
                raise

            if self.print_errors:
                print(TERM.red("%s: %s" % (type(err).__name__, err)))


    def _get_text(self, cell: AnyStr, col: int, row: int) -> str:
        params = {
            "width":              self.cols[col].size.ceil_cell().cells,
            "placeholder":        self.cut_placeholder,
            "tabsize":            4,
            "replace_whitespace": False,
            "drop_whitespace":    False
        }

        assert self.text_overflow in ("wrap", "shorten")

        if self.text_overflow == "wrap":
            lines = ansiwrap.wrap(cell, **params)
        else:
            lines = [ansiwrap.shorten(l, **params) for l in cell.splitlines()]

        return "\n".join(lines[:self.rows[row].size.ceil_cell().cells])


    def _show_content(self,
                      content: ReturnedContent,
                      width:   HSize,
                      height:  VSize,
                      col:     int,
                      row:     int) -> None:

        inner_y = self._get_align(self.rows[row], height)

        restore_x = TERM.move_x(TERM.get_location()[1] - 1)

        if isinstance(content, Image):
            inner_x = self._get_align(self.cols[col], width)
            content.show(align="left", relative_x=inner_x, relative_y=inner_y)

        else:
            # Print vertical padding as blank lines, put cursor back to right x
            TERM.print_esc("\n" * inner_y.floor_cell().cells, restore_x)

            for line in content.splitlines():
                inner_x = self._get_align(self.cols[col],
                                          HSize(cells=ansilen(line)))

                TERM.print_esc(" " * inner_x.floor_cell().cells,
                               line, "\n",
                               restore_x)

        # If needed, print blank lines to "complete the cell",
        # i.e. content height didn't fill it.
        # The cursor needs to always be at the cell row's bottom.
        TERM.print_esc(
            "\n" * (self.rows[row].size.ceil_cell() - height - inner_y)\
                    .floor_cell().cells
        )


    @staticmethod
    def _get_align(cell: Cell, child_size: AlignSize) -> AlignSize:
        assert cell.align in ("left", "top", "center", "right", "bottom")

        if cell.align in ("left", "top"):
            return type(cell.size)(0)

        if cell.align == "center":
            return (cell.size / 2 - child_size / 2).floor_cell()

        return (cell.size - child_size).floor_cell()
