# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

"""Usage:
  pixcat (-d|--detect-support)
  pixcat [r|resize | t|thumbnail | f|fit-screen] [options] LOCATION...

Display images on a kitty terminal with optional resizing.

For options taking a NUM argument, NUM will be seen as pixels by default.
To indicate terminal columns/rows, append "t" to the number, e.g. "12t".

Arguments:
  LOCATION: File, folder to be be scanned recursively for images, or URL.
            Any number of file, folder or URLs can be specified.

Options:
  Resizing:
    -S, --stretch             Do not force keeping the original aspect ratio.
    -r ALGO, --resample ALGO  From fastest/worse to slowest/best quality:
                              nearest, bilinear, bicubic, lanczos (default).

  Specific to r/resize:
    -w NUM, --min-width NUM   Upscale when width is lower than NUM.
    -h NUM, --min-height NUM  Upscale when height is lower than NUM.
    -W NUM, --max-width NUM   Downscale when height is higher than NUM.
    -H NUM, --max-height NUM  Downscale when height is higher than NUM.

  Specific to t/thumbnail:
    -s PX, --size PX  Scale to PXxPX pixels, default 256.

  Specific to f/fit-screen:
    -e, --enlarge                    Scale up for images smaller than terminal.
    -o NUM, --horizontal-margin NUM  Have a left-right padding of NUM.
    -v NUM, --vertical-margin NUM    Have a top-bottom padding of NUM.

  Positioning:
    -x NUM, --absolute-x NUM  Left image origin, from the terminal's left.
    -y NUM, --absolute-y NUM  Top image origin, from the terminal's top.
    -z INT, --z-index INT     Images are drawn in front of others that have a
                              lower index. -1 and lower will draw behind text.

    -X NUM, --relative-x NUM  Like -x, but from current cursor position.
    -Y NUM, --relative-y NUM  Like -y, but from current cursor position.

    -a ALI, --align ALI       Image and text alignement, -X is added to it.
                              left, center (default) or right.

    -c NUM, --crop-w NUM      Crop image left-to-right to NUM.
    -C NUM, --crop-h NUM      Crop image top-to-bottom to NUM.

  General:
    -O, --print-origin    Print image origin, like a path or URL.
    -n, --print-name      Print image filename.
    -i, --print-id        Print kitty image ID.

    -q, --quiet           Keep quiet about errors, e.g. "cannot identify image"
    -R, --raise-errors    Exit and show full traceback if an error happens.

    -g, --hang            Wait for an enter keypress between every image.
    -G, --hang-final      Wait for enter keypress after all images are drawn.

    -d, --detect-support  Exit with 0 if terminal supports images, else 1.


  Standard:
    --         Mark the end of options, useful if a LOCATION starts by a dash.
    --help     Show this help.
    --version  Show the program version.

Examples:
  pixcat image.jpg
    Just display image.jpg, no resizing.
    If the width exceeds the terminal's, it will be cropped.

  pixcat fit-screen --enlarge image.jpg
    Display image.jpg, downscale or upscale (if --enlarge) when necessary to
    make image match terminal dimensions.

  pixcat resize -w 64 -h 32 -W 512 -H 256 --align right --relative-x -2 *.png
    Display all png files in the current dir with a size of at least 64x32 and
    no bigger than 512x256.

    Align the pictures against the terminal's right edge,
    minus 2 columns (negative --relative-x).

  pixcat thumbnail --size 128 --resample nearest dir1 dir2
    Recursively find and display images in dir1 and dir2,
    with a min-max-size of 128x128 (aspect ratio will be taken into account).

    The nearest rescaling algorithm will trade quality for speed, useful
    if there are a lot of images to display.

  pixcat t -s 128 -r nearest dir1 dir2
    Same as the command above, short form.

Bugs and limitations:
  - Does not work in tmux
  - Resizing the terminal can lead to a mess, use clear/CTRL+L to fix it."""


import sys
from pathlib import Path
from typing import List, Optional

import docopt

from . import Image
from .__about__ import __version__
from .size import HSize, VSize
from .terminal import TERM

def to_hsize(val) -> HSize:
    return HSize(float(val))


def to_vsize(val) -> VSize:
    return VSize(float(val))


CLI_TO_FUNCTIONS_PARAMS = {
    "resize": {
        "--min-width":   ("min_w",    to_hsize),
        "--min-height":  ("min_h",    to_vsize),
        "--max-width":   ("max_w",    to_hsize),
        "--max-height":  ("max_h",    to_vsize),
        "--stretch":     ("stretch",  bool),
        "--resample":    ("resample", str),
    },
    "thumbnail": {
        "--size":     ("size",     int),
        "--stretch":  ("stretch",  bool),
        "--resample": ("resample", str),
    },
    "fit_screen": {
        "--enlarge":           ("enlarge",  bool),
        "--horizontal-margin": ("h_margin", to_hsize),
        "--vertical-margin":   ("v_margin", to_vsize),
        "--stretch":           ("stretch",  bool),
        "--resample":          ("resample", str),
    },
    "show": {
        "--absolute-x": ("x",          to_hsize),
        "--absolute-y": ("y",          to_vsize),
        "--z-index":    ("z",          int),
        "--relative-x": ("relative_x", to_hsize),
        "--relative-y": ("relative_y", to_vsize),
        "--align":      ("align",      str),
        "--crop-w":     ("crop_w",     to_hsize),
        "--crop-h":     ("crop_h",     to_vsize),
    }
}


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        params = docopt.docopt(__doc__, argv=argv, version=__version__)
    except docopt.DocoptExit:
        if len(sys.argv) > 1:
            print("Invalid command syntax, check help:\n")

        main(["--help"])
        sys.exit(1)

    if params["--detect-support"]:
        sys.exit(0 if TERM.detect_support() else 1)

    images = Image.factory(
        *params["LOCATION"],
        raise_errors = params["--raise-errors"],
        print_errors = not params["--quiet"]
    )

    for image in images:
        handle_image(image, params)

    if params["--hang-final"]:
        input("Press enter to exit...")


def handle_image(image: Image, params: dict) -> None:
    if params["r"] or params["resize"]:
        image = image.resize(**cli_to_func_params("resize", params))

    elif params["t"] or params["thumbnail"]:
        image = image.thumbnail(**cli_to_func_params("thumbnail", params))

    elif params["f"] or params["fit-screen"]:
        image = image.fit_screen(**cli_to_func_params("fit_screen", params))

    print_align = lambda t: print(TERM.align(t, params["--align"] or "center"))

    if params["--print-name"]:
        if isinstance(image.origin, (Path, str)):
            print_align(Path(image.origin).name)
        else:
            print_align("-")

    if params["--print-origin"]:
        if isinstance(image.origin, (Path, str)):
            print_align(str(image.origin))
        else:
            print_align("-")

    if params["--print-id"]:
        print_align(image.id)

    image.show(**cli_to_func_params("show", params))

    if params["--hang"]:
        input()


def cli_to_func_params(func_name: str, params: dict) -> dict:
    mappings = CLI_TO_FUNCTIONS_PARAMS
    return {
        mappings[func_name][param][0]: mappings[func_name][param][1](value)
        for param, value in params.items()
        if value is not None and param in mappings[func_name]
    }
