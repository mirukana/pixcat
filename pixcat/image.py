# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

import io
import math
import random
import re
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Generator, Optional, Tuple, Union

from dataclasses import InitVar, dataclass, field
from PIL import Image as PILImage

from . import data
from .terminal import TERM


@dataclass
class Image:
    min_id   = data.MIN_ID
    max_id   = data.MAX_ID
    used_ids = set()
    types    = Union[bytes, str, Path, PILImage.Image]

    source: InitVar[types]
    id:     Optional[int] = None

    origin: types = field(init=False, default=None)

    _pil_image: PILImage.Image = field(init=False, repr=False, default=None)

    _resized_cache: Dict[Tuple[str, tuple], "Image"] = \
        field(init=False, repr=False, compare=False, default_factory=dict)


    def __post_init__(self, source) -> None:
        self._resized_cache = {}  # to make pylint shut up
        self.origin         = source
        self.id             = self._get_id()
        self._pil_image     = self._get_pil_image(source)


    def _get_id(self) -> int:
        # Avoid hanging if somehow more than 4 billion of ids are registered:
        if len(self.used_ids) >= self.max_id:
            self.used_ids = set()

        random_id = random.randint(self.min_id, self.max_id)

        while random_id in self.used_ids:
            random_id = random.randint(self.min_id, self.max_id)

        self.used_ids.add(random_id)
        return random_id


    def _get_pil_image(self, source) -> PILImage.Image:
        if isinstance(source, PILImage.Image):
            return source

        if re.match(r"https?://.+", str(source)):
            import requests
            req = requests.get(source)
            req.raise_for_status()  # Raise if 400 < http code < 600
            source = req.content    # bytes

        if isinstance(source, bytes):
            # Don't use `with`  here, or _get_kitty_file() will fail.
            out = io.BytesIO()
            out.write(source)
            out.seek(0)
            return PILImage.open(out)

        self.origin = path = Path(source).expanduser().resolve()
        return PILImage.open(path)


    def _get_kitty_file(self) -> str:
        dest = NamedTemporaryFile(prefix=".pixcat-", delete=False)
        self._pil_image.save(dest.name, format="PNG", compress_level=0)
        return dest.name


    @property
    def cols(self) -> int:
        return math.ceil(self._pil_image.size[0] / TERM.cell_px_width)

    @property
    def rows(self) -> int:
        return math.ceil(self._pil_image.size[1] / TERM.cell_px_height)


    @staticmethod
    def _negative_col_to_px(num: int) -> int:
        return num if num >= 0 else TERM.cell_px_width * abs(num)

    @staticmethod
    def _negative_row_to_px(num: int) -> int:
        return num if num >= 0 else TERM.cell_px_height * abs(num)


    def resize(self,
               min_w:    int           = 1,
               min_h:    int           = 1,
               max_w:    Optional[int] = None,
               max_h:    Optional[int] = None,
               stretch:  bool          = False,
               resample: str           = "lanczos") -> "Image":

        w, h = img_w, img_h = self._pil_image.size

        max_w = max_w or img_w
        max_h = max_h or img_h

        assert min_w <= max_w
        assert min_h <= max_h

        min_w = self._negative_col_to_px(min_w)
        min_h = self._negative_row_to_px(min_h)
        max_w = self._negative_col_to_px(max_w)
        max_h = self._negative_row_to_px(max_h)

        # Upscale if image is smaller than minimum width/height:
        if (img_w < min_w or img_h < min_h) and img_w < max_w and img_h <max_h:

            if stretch:
                w, h = min_w, min_h

            elif min_w >= min_h:
                # If calculated height > max_h: max_h, if < min_h: min_h
                h = min(max_h, math.ceil((min_w / img_w) * img_h))
                w = math.floor((h / img_h) * img_w)

            else:
                w = min(max_w, math.ceil((min_h / img_h) * img_w))
                h = math.floor((w / img_w) * img_h)

        # Downscale if image is bigger than maximum width/height:
        elif img_w > max_w or img_h > max_h:

            if stretch:
                w, h = max_w, max_h

            elif max_w >= max_h:
                h = min(max_h, math.ceil((max_w / img_w) * img_h))
                w = math.floor((h / img_h) * img_w)

            else:
                w = min(max_w, math.ceil((max_h / img_h) * img_w))
                h = math.floor((w / img_w) * img_h)

        # Nothing to do:
        else:
            return self

        # If an image was already made for decided width/height, return it:

        cached = self._resized_cache.get((w, h))
        if cached:
            return cached

        # Return and save in the cache dict an Image object of the resized.

        resample = getattr(PILImage, resample.upper())
        image    = type(self)(self._pil_image.resize((w, h), resample))

        self._resized_cache[(w, h)] = image
        return image


    def thumbnail(self,
                  size:     int  = 256,
                  stretch:  bool = False,
                  resample: str  = "lanczos") -> "Image":

        return self.resize(*(size,) * 4, stretch, resample)


    def fit_screen(self,
                   h_margin: int  = 0,
                   v_margin: int  = 0,
                   enlarge:  bool = False,
                   stretch:  bool = False,
                   resample: str  = "lanczos") -> "Image":

        h_margin = self._negative_col_to_px(h_margin) * 4
        v_margin = self._negative_row_to_px(v_margin) * 4

        max_wh = (TERM.px_width - h_margin, TERM.px_height - v_margin)
        min_wh =  max_wh if enlarge else (0, 0)

        return self.resize(*min_wh, *max_wh, stretch, resample)


    def show(self,
             x:          Optional[int] = None,
             y:          Optional[int] = None,
             z:          int  = 0,
             relative_x: int  = 0,
             relative_y: int  = 0,
             align:      str  = "center",
             offset_x:   int  = 0,
             offset_y:   int  = 0,
             crop_w:     int  = 0,
             crop_h:     int  = 0) -> "Image":

        assert align in ("left", "center", "right")

        crop_w = self._negative_col_to_px(crop_w)
        crop_h = self._negative_row_to_px(crop_h)

        params = {
            "offset_x": offset_x, "offset_y": offset_y,
            "crop_w":   crop_w,   "crop_h":   crop_h,
            "z_index":  z,

            "action": "transmit+display",
            "medium" : "tempfile",
            "format" : "png",
            "id":      self.id,
            "payload": self._get_kitty_file(),
        }

        if x is not None:
            print(TERM.move_x(x), end="")

        elif align == "center":
            relative_x += round(TERM.width / 2) - round(self.cols / 2)

        elif align == "right":
            relative_x += TERM.width - self.cols

        if relative_x:
            print(TERM.move_relative_x(relative_x), end="")

        if y is not None:
            print(TERM.move_y(y), end="")

        if relative_y:
            print(TERM.move_relative_y(relative_y), end="")

        TERM.run_code(**params)
        return self


    def hide(self, resized_too: bool = True) -> "Image":
        ids = [self.id]

        if resized_too:
            ids += [img.id for img in self._resized_cache.values()]

        for id_ in ids:
            TERM.run_code(action="delete", del_data_target="id", id=id_)

        return self


    def copy(self, new_id: Optional[int] = None) -> "Image":
        return type(self)(source=self.origin, id=new_id)


    def __copy__(self) -> "Image":
        return self.copy()


    @classmethod
    def factory(cls,
                *sources:      "Image.types",
                raise_errors:  bool = False,
                print_errors:  bool = True) -> Generator["Image", None, None]:

        for source in sources:
            try:
                if isinstance(source, (bytes, PILImage.Image)) or \
                   re.match(r"https?://.+", str(source)):
                    yield cls(source)
                    continue

                path = Path(source).expanduser().resolve()

                if path.is_dir():
                    for item in path.iterdir():
                        yield from cls.factory(
                            item,
                            raise_errors = raise_errors,
                            print_errors = print_errors
                        )
                    continue

                yield cls(path)

            except Exception as err:
                if raise_errors:
                    raise

                if print_errors:
                    print(TERM.red("%s: %s" % (type(err).__name__, err)))
