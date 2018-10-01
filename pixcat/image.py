# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

import math
import random
import re
from mimetypes import guess_extension, guess_type
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Dict, Generator, List, Optional, Tuple, Union

from dataclasses import InitVar, dataclass, field
from PIL import Image as PILImage

import requests

from . import terminal
from .__about__ import __pkg_name__
from .errors import BadFileError

TERM        = terminal.PixTerminal()
NET_SESSION = requests.Session()

PNG_TMP_COMPRESS = 3


@dataclass
class Image:
    location: InitVar[Union[str, Path]]
    id:       Optional[int] = None


    path:            Path           = field(init=False, default=None)
    origin_path:     Optional[Path] = field(init=False, default=None)
    origin_url:      Optional[str]  = field(init=False, default=None)
    downloaded_path: Optional[str]  = field(init=False, default=None)

    w: int = field(init=False, default=0)
    h: int = field(init=False, default=0)


    _pil_image: type(PILImage) = field(init=False, repr=False, default=None)

    _tmpfile_keepalive: List[type(NamedTemporaryFile)] = \
        field(init=False, repr=False, compare=False, default_factory=list)

    _resized_cache: Dict[Tuple[str, tuple], "Image"] = \
        field(init=False, repr=False, compare=False, default_factory=dict)


    def __post_init__(self, location) -> None:
        # To make pylint shut up
        self._resized_cache     = {}
        self._tmpfile_keepalive = []

        if re.match(r"https?://.+", str(location)):
            self._get_from_url(location)
        else:
            self.path        = Path(location).expanduser().resolve()
            self.origin_path = self.path

        self._process_input_file()
        self._pil_image = PILImage.open(self.path)
        self.w, self.h  = self._pil_image.size

        # TODO: verify available
        self.id = self.id or random.randint(1, 4_294_967_295)


    def _get_from_url(self, url: str) -> Path:
        response = NET_SESSION.get(url)

        # Raise exception if HTTP return code is between 400 and 600.
        response.raise_for_status()

        ext  = guess_extension(response.headers["Content-Type"])
        file = NamedTemporaryFile(prefix=f".{__pkg_name__}-", suffix=ext)
        file.write(response.content)

        self.path       = self.downloaded_path = Path(file.name)
        self.origin_url = url

        self._tmpfile_keepalive.append(file)


    def _process_input_file(self) -> None:
        if not self.path.is_file():
            raise BadFileError(self, f"doesn't exist or not a file.")

        mime, encoding = guess_type(str(self.path))

        if encoding is not None:
            raise BadFileError(self, f"unsupported encoding: {encoding}")

        if not mime or not mime.startswith("image/"):
            raise BadFileError(self, "file was not recognized as image.")

        if mime == "image/png":
            return

        self.path = self._get_png()


    def _get_png(self) -> Path:
        file = NamedTemporaryFile(prefix=f".{__pkg_name__}-", suffix=".png")

        PILImage.open(self.path).save(file.name,
                                      compress_level=PNG_TMP_COMPRESS)
        self._tmpfile_keepalive.append(file)

        return Path(file.name)


    @property
    def cols(self):
        return math.ceil(self.w / TERM.cell_px_width)

    @property
    def rows(self):
        return math.ceil(self.h / TERM.cell_px_height)


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

        max_w = max_w or self.w
        max_h = max_h or self.h

        assert min_w <= max_w
        assert min_h <= max_h

        w, h = self.w, self.h

        min_w = self._negative_col_to_px(min_w)
        min_h = self._negative_row_to_px(min_h)
        max_w = self._negative_col_to_px(max_w)
        max_h = self._negative_row_to_px(max_h)

        # Upscale if image is smaller than minimum width/height:
        if (self.w < min_w or  self.h < min_h) and \
           self.w < max_w and self.h < max_h:

            if stretch:
                w, h = min_w, min_h

            elif min_w >= min_h:
                # If calculated height > max_h: max_h, if < min_h: min_h
                h = min(max_h, math.ceil((min_w / self.w) * self.h))
                w = math.floor((h / self.h) * self.w)

            else:
                w = min(max_w, math.ceil((min_h / self.h) * self.w))
                h = math.floor((w / self.w) * self.h)

        # Downscale if image is bigger than maximum width/height:
        elif self.w > max_w or self.h > max_h:

            if stretch:
                w, h = max_w, max_h

            elif max_w >= max_h:
                h = min(max_h, math.ceil((max_w / self.w) * self.h))
                w = math.floor((h / self.h) * self.w)

            else:
                w = min(max_w, math.ceil((max_h / self.h) * self.w))
                h = math.floor((w / self.w) * self.h)

        # Nothing to do:
        else:
            return self

        # If an image was already made for decided width/height, return it:

        cached = self._resized_cache.get((w, h))
        if cached:
            return cached

        # Resize image and save to temporary file:

        filt = getattr(PILImage, resample.upper())
        img  = self._pil_image.resize((w, h), filt)
        file = NamedTemporaryFile(prefix=f".{__pkg_name__}-", suffix=".png")
        img.save(file.name, compress_level=PNG_TMP_COMPRESS)

        # New Image object of the resized image, bind temp file handle to it.
        # Save it in the cache dict so it can be re-used later.
        # The temp file will exist as long as the Image is in the cache dict.

        img                  = Image(file.name)
        img.origin_path      = self.origin_path
        img.origin_url       = self.origin_url
        img.downloaded_path  = self.downloaded_path

        # pylint: disable=protected-access
        img._tmpfile_keepalive.append(file)
        self._resized_cache[(w, h)] = img

        return img


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

        # If x/y or relative_(x/y) is set, only one must be set
        assert {bool(x), bool(relative_x)} != {True}
        assert {bool(y), bool(relative_y)} != {True}

        assert align in ("left", "center", "right")

        crop_w = self._negative_col_to_px(crop_w)
        crop_h = self._negative_row_to_px(crop_h)

        params = {
            "offset_x": offset_x, "offset_y": offset_y,
            "crop_w":   crop_w,   "crop_h":   crop_h,
            "z_index":  z,

            "action": "transmit+display",
            "medium" : "file",
            "format" : "png",
            "id":      self.id,
            "payload": str(self.path),
        }

        if align == "center":
            relative_x += round(TERM.width / 2) - round(self.cols / 2)

        elif align == "right":
            relative_x += TERM.width - self.cols

        if relative_x:
            print(" " * relative_x, end="")
        elif x:
            print(TERM.move_x(x))  # FIXME

        if relative_y:
            print("\n" * relative_y, end="")  # FIXME: moving up
        elif y:
            print(TERM.move_y(y))  # FIXME

        TERM.run_code(**params)
        return self


    def hide(self) -> "Image":
        TERM.run_code(action="delete", del_data_target="id", id=self.id)
        return self


    def copy(self, new_id: Optional[int] = None) -> "Image":
        obj = type(self)(self.path, id=new_id)

        obj.origin_path      = self.origin_path
        obj.origin_url       = self.origin_url
        obj.downloaded_path  = self.downloaded_path

        return obj


    def __copy__(self) -> "Image":
        return self.copy()


    @classmethod
    def factory(cls, *locations: Union[Path, str]
               ) -> Generator["Image", None, None]:

        for location in locations:
            # URL
            if re.match(r"https?://.+", str(location)):
                try:
                    yield cls(location)
                except (BadFileError, requests.RequestException) as err:
                    print(TERM.red(f"\n{err.args[0]}\n"))
                continue

            path = Path(location).expanduser().resolve()

            # Folder
            if path.is_dir():
                for item in path.iterdir():
                    yield from cls.factory(item)
                continue

            # File
            mime, encoding = guess_type(str(path))

            if not encoding and mime and mime.startswith("image/"):
                try:
                    yield cls(path)
                except (BadFileError, OSError) as err:
                    print(TERM.red(f"\n{err.args[0]}\n"))
