import math
from typing import Callable, List, Union

from .terminal import TERM


class Size:
    def __init__(self, kind: str, px: int = 0, cells: int = 0) -> None:
        assert not (px and cells)
        assert kind in ("width", "height")

        self.kind: str = kind

        if px:
            self._px:    int = px
            self._cells: int = math.ceil(px / self._term_cell_size)
        else:
            self._cells: int = cells
            self._px:    int = math.ceil(cells * self._term_cell_size)

    def __repr__(self) -> str:
        return "%s(%s)" % (
            type(self).__name__,
            f"kind='{self.kind}', px={self.px}, cells={self.cells}"
        )


    def __copy__(self) -> "Size":
        return type(self)(kind=self.kind, px=self.px)

    def _from_px(self, px: Union[int, float]) -> "Size":
        return type(self)(kind=self.kind, px=math.ceil(px))

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(kind=self.kind, cells=math.ceil(cells))


    def __int__(self) -> int:
        return self.px


    def __eq__(self, other) -> bool:
        return self.px == int(other)

    def __gt__(self, other) -> bool:
        return self.px > int(other)


    def __add__(self, other) -> "Size":
        return self._from_px(self.px + int(other))

    def __sub__(self, other) -> "Size":
        return self._from_px(self.px - int(other))

    def __mul__(self, other) -> "Size":
        return self._from_px(self.px * int(other))

    def __floordiv__(self, other) -> "Size":
        return self._from_px(self.px // int(other))

    def __truediv__(self, other) -> "Size":
        # Half of pixels don't exist
        return self._from_px(self.px / int(other))

    def __pow__(self, other) -> "Size":
        return self._from_px(self.px ** int(other))


    def __radd__(self, other) -> "Size":
        return self._from_px(int(other) + self.px)

    def __rsub__(self, other) -> "Size":
        return self._from_px(int(other) - self.px)

    def __rmul__(self, other) -> "Size":
        return self._from_px(int(other) * self.px)

    def __rfloordiv__(self, other) -> "Size":
        return self._from_px(int(other) // self.px)

    def __rtruediv__(self, other) -> "Size":
        # Half of pixels don't exist
        return self._from_px(int(other) / self.px)

    def __rpow__(self, other) -> "Size":
        return self._from_px(int(other) ** self.px)


    def __floor__(self) -> "Size":
        "Reduce px down to the nearest terminal cell."
        return self._from_cells(math.floor(self.px / self._term_cell_size))

    def __ceil__(self) -> "Size":
        "Increase px up to the nearest terminal cell."
        return self._from_cells(math.ceil(self.px / self._term_cell_size))



    @property
    def _term_cell_size(self) -> int:
        return getattr(TERM, f"cell_px_{self.kind}")


    @property
    def px(self) -> int:
        return self._px

    @property
    def cells(self) -> int:
        return self._cells


class MutableSize(Size):
    @property
    def px(self) -> int:
        return super().px

    @px.setter
    def px(self, to: int) -> None:
        self._px    = to
        self._cells = math.ceil(to / self._term_cell_size)

    @property
    def cells(self) -> int:
        return super().cells

    @cells.setter
    def cells(self, to: int) -> None:
        self._cells = to
        self._px    = math.ceil(to * self._term_cell_size)



class HSize(MutableSize):
    def __init__(self, px: int = 0, cells: int = 0) -> None:
        super().__init__(kind="width", px=px, cells=cells)

    def __repr__(self) -> str:
        return super().__repr__().replace("kind='width', ", "")

    def _from_px(self, px: Union[int, float]) -> "HSize":
        return type(self)(px=math.ceil(px))

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(cells=math.ceil(cells))



class VSize(MutableSize):
    def __init__(self, px: int = 0, cells: int = 0) -> None:
        super().__init__(kind="height", px=px, cells=cells)

    def __repr__(self) -> str:
        return super().__repr__().replace("kind='height', ", "")

    def _from_px(self, px: Union[int, float]) -> "VSize":
        return type(self)(px=math.ceil(px))

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return type(self)(cells=math.ceil(cells))



class TermHSize(Size):
    def __init__(self) -> None:
        super().__init__(kind="width", px=TERM.px_width)

    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__,
                           f"px={self.px}, cells={self.cells}")

    def _from_px(self, px:Union[int, float]) -> "HSize":
        return HSize(px=math.ceil(px))

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return HSize(cells=math.ceil(cells))

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
        return VSize(px=math.ceil(px))

    def _from_cells(self, cells: Union[int, float]) -> "Size":
        return VSize(cells=math.ceil(cells))

    @property
    def px(self) -> int:
        return TERM.px_height

    @property
    def cells(self) -> int:
        return TERM.height



AxisSizeType = Union[HSize, VSize, TermHSize, TermVSize]
AxisSizeType = Union[AxisSizeType, Callable[["AxisSizes", int], AxisSizeType]]
AxisSizeType = Union[AxisSizeType, List[AxisSizeType]]


class AxisSizes(list):
    def __init__(self, sizes: AxisSizeType):
        super().__init__(self._listify(sizes))


    def __repr__(self) -> str:
        return "%s(%s)" % (type(self).__name__, super().__repr__())


    @staticmethod
    def _listify(value) -> List[Union[HSize, VSize]]:
        values = list(value) if hasattr(value, "__iter__") else [value]

        for val in values:
            assert isinstance(val, (HSize, VSize, TermHSize, TermVSize,
                                    Callable, Ellipsis))

        return values


    def __getitem__(self, index):
        try:
            item = super().__getitem__(index)
        except IndexError:
            item = super().__getitem__(-1)

        return item(self, index) if callable(item) else item
