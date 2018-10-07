import math
from typing import Union

from .terminal import TERM


class Size:
    def __init__(self,
                 kind:  str,
                 px:    Union[int, float] = 0,
                 cells: Union[int, float] = 0) -> None:

        assert not (px and cells)
        assert kind in ("width", "height")

        self.kind: str = kind

        if px:
            self._px:    float = px
            self._cells: float = px / self._term_cell_size
        else:
            self._cells: float = cells
            self._px:    float = cells * self._term_cell_size

    def __repr__(self) -> str:
        return "%s(%s)" % (
            type(self).__name__,
            f"kind='{self.kind}', px={self.px}, cells={self.cells}"
        )


    def __copy__(self) -> "Size":
        return type(self)(kind=self.kind, px=self.px)

    def _from_px(self, px: Union[int, float]) -> "Size":
        return type(self)(kind=self.kind, px=px)

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(kind=self.kind, cells=cells)


    def __int__(self) -> int:
        return int(self.px)

    def __float__(self) -> float:
        return float(self.px)

    def __bool__(self) -> bool:
        return bool(self.px)


    def __eq__(self, other) -> bool:
        return self.px == float(other)

    def __gt__(self, other) -> bool:
        return self.px > float(other)

    def __ge__(self, other) -> bool:
        return self.px >= float(other)


    def __add__(self, other) -> "Size":
        return self._from_px(self.px + float(other))

    def __sub__(self, other) -> "Size":
        return self._from_px(self.px - float(other))

    def __mul__(self, other) -> "Size":
        return self._from_px(self.px * float(other))

    def __floordiv__(self, other) -> "Size":
        return self._from_px(self.px // float(other))

    def __truediv__(self, other) -> "Size":
        return self._from_px(self.px / float(other))

    def __pow__(self, other) -> "Size":
        return self._from_px(self.px ** float(other))


    def __radd__(self, other) -> "Size":
        return self._from_px(float(other) + self.px)

    def __rsub__(self, other) -> "Size":
        return self._from_px(float(other) - self.px)

    def __rmul__(self, other) -> "Size":
        return self._from_px(float(other) * self.px)

    def __rfloordiv__(self, other) -> "Size":
        return self._from_px(float(other) // self.px)

    def __rtruediv__(self, other) -> "Size":
        return self._from_px(float(other) / self.px)

    def __rpow__(self, other) -> "Size":
        return self._from_px(float(other) ** self.px)


    def __pos__(self) -> "Size":
        return self._from_px(+self.px)

    def __neg__(self) -> "Size":
        return self._from_px(-self.px)

    def __abs__(self) -> "Size":
        return self._from_px(abs(self.px))

    def __invert__(self) -> "Size":
        return self._from_px(~self.px)

    def __round__(self) -> "Size":
        return self._from_px(round(self.px))

    def __floor__(self) -> "Size":
        return self._from_px(math.floor(self.px))

    def __ceil__(self) -> "Size":
        return self._from_px(math.ceil(self.px))


    def round_cell(self) -> "Size":
        "Reduce px down to the nearest terminal cell."
        return self._from_cells(math.floor(self.px / self._term_cell_size))

    def floor_cell(self) -> "Size":
        "Reduce px down to the nearest terminal cell."
        return self._from_cells(math.floor(self.px / self._term_cell_size))

    def ceil_cell(self) -> "Size":
        "Increase px up to the nearest terminal cell."
        return self._from_cells(math.ceil(self.px / self._term_cell_size))


    @property
    def _term_cell_size(self) -> int:
        return getattr(TERM, f"cell_px_{self.kind}")


    @property
    def px(self) -> float:
        return self._px

    @property
    def cells(self) -> float:
        return self._cells


class MutableSize(Size):
    @property
    def px(self) -> float:
        return super().px

    @px.setter
    def px(self, to: Union[int, float]) -> None:
        self._px    = float(to)
        self._cells = to / self._term_cell_size

    @property
    def cells(self) -> float:
        return super().cells

    @cells.setter
    def cells(self, to: Union[int, float]) -> None:
        self._cells = float(to)
        self._px    = to * self._term_cell_size



class HSize(MutableSize):
    def __init__(self, px: Union[int, float] = 0, cells: Union[int, float] = 0
                ) -> None:
        super().__init__(kind="width", px=px, cells=cells)

    def __repr__(self) -> str:
        return super().__repr__().replace("kind='width', ", "")

    def _from_px(self, px: Union[int, float]) -> "HSize":
        return type(self)(px=px)

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(cells=cells)



class VSize(MutableSize):
    def __init__(self, px: Union[int, float] = 0, cells: Union[int, float] = 0
                ) -> None:
        super().__init__(kind="height", px=px, cells=cells)

    def __repr__(self) -> str:
        return super().__repr__().replace("kind='height', ", "")

    def _from_px(self, px: Union[int, float]) -> "VSize":
        return type(self)(px=px)

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(cells=cells)



class TermHSize(Size):
    def __init__(self) -> None:
        super().__init__(kind="width", px=TERM.px_width)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__,
                           f"px={self.px}, cells={self.cells}")

    def _from_px(self, px:Union[int, float]) -> "HSize":
        return HSize(px=px)

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return HSize(cells=cells)

    @property
    def px(self) -> int:
        return TERM.px_width

    @property
    def cells(self) -> int:
        return TERM.width



class TermVSize(Size):
    def __init__(self) -> None:
        super().__init__(kind="height", px=TERM.px_height)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__,
                           f"px={self.px}, cells={self.cells}")

    def _from_px(self, px: Union[int, float]) -> "VSize":
        return VSize(px=px)

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return VSize(cells=cells)

    @property
    def px(self) -> int:
        return TERM.px_height

    @property
    def cells(self) -> int:
        return TERM.height
