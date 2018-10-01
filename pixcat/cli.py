# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

"""Usage:
  pixcat [r | resize | t | thumbnail | f | fit-screen] [options] [--] PATH...

Display images on a kitty terminal with optional resizing.

For resizing options, measures (INT number arguments) are in pixel by default.
To indicate columns/rows instead, prefix the number with a dash.

Positioning options are always in columns/rows.

Arguments:
  PATH: Image file, or folder that will be scanned recursively for images.
        Multiple files or folders can be specified.

Options:
  Resizing:
    -S, --stretch             Do not force keeping the original aspect ratio.
    -r ALGO, --resample ALGO  From fastest/worse to slowest/best quality:
                              nearest, bilinear, bicubic, lanczos (default).

  Specific to r/resize:
    -w INT, --min-width INT   Upscale when width is lower than INT.
    -h INT, --min-height INT  Upscale when height is lower than INT.
    -W INT, --max-width INT   Downscale when height is higher than INT.
    -H INT, --max-height INT  Downscale when height is higher than INT.

  Specific to t/thumbnail:
    -s INT, --size INT  Scale to INTxINT, default 256.

  Specific to f/fit-screen:
    -e, --enlarge                    Scale up for images smaller than terminal.
    -o INT, --horizontal-margin INT  Have a left-right padding of INT columns.
    -v INT, --vertical-margin INT    Have a top-bottom padding of INT columns.

  Positioning:
    -x INT, --absolute-x INT  Left image origin in columns, from terminal left.
    -y INT, --absolute-y INT  Top image origin in rows, from terminal top.
    -z INT, --z-index INT     Images are drawn in front of others that have a
                              lower index. -1 and lower will draw behind text.

    -X INT, --relative-x INT  Like -x, but from current cursor position.
    -Y INT, --relative-y INT  Like -y, but from current cursor position.

    -a ALI, --align ALI       Image and text alignement, -X is added to it.
                              left, center (default) or right.

    -f INT, --offset-x INT    Left offset in pixel, max is column width.
    -F INT, --offset-y INT    Top offset in pixel, max is row height.

    -c INT, --crop-w INT      Crop image left-to-right to INT pixels.
    -C INT, --crop-h INT      Crop image top-to-bottom to INT pixels.

  Other:
    -p, --print-path      Print image paths.
    -P, --print-tmp-path  Print temporary paths of processed images.
    -n, --print-name      Print image filename.
    -i, --print-id        Print kitty image ID.
    -g, --hang            Wait for an enter keypress between every image.
    -G, --hang-final      Wait for enter keypress after all images are drawn,
                          useful to wait before deleting temp processed images.

  Performance:
    -t INT, --tmp-compress INT  PNG compression for temporary files, 0-10.
                                Lower values trade memory usage for speed.

  Generic:
    --         Mark the end of options, useful if a PATH starts with a dash.
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
  - Absolute positioning options do not work reliably yet
  - An images has 1/4294967295 chances of overriding another when displayed
  - No support in multiplexers like tmux yet
  - No support over remote terminals yet
  - Resizing the terminal can lead to a mess, use clear/CTRL+L to fix it."""


import sys
from typing import List, Optional

import docopt

from . import Image, data, terminal
from . import image as image_module
from .__about__ import __version__

TERM = terminal.PixTerminal()


def main(argv: Optional[List[str]] = None) -> None:
    argv = argv if argv is not None else sys.argv[1:]

    try:
        params = docopt.docopt(__doc__, argv=argv, version=__version__)
    except docopt.DocoptExit:
        if len(sys.argv) > 1:
            print("Invalid command syntax, check help:\n")

        main(["--help"])
        sys.exit(1)

    if params["--tmp-compress"]:
        image_module.PNG_TMP_COMPRESS = int(params["--tmp-compress"])

    for image in Image.factory(*params["PATH"]):
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

    if params["--print-path"]:
        print_align(image.origin_path)

    if params["--print-tmp-path"]:
        print_align(image.path)

    if params["--print-name"]:
        print_align(image.origin_path.name)

    if params["--print-id"]:
        print_align(image.id)

    image.show(**cli_to_func_params("show", params))

    if params["--hang"]:
        input()


def cli_to_func_params(func_name: str, params: dict) -> dict:
    mappings = data.CLI_TO_FUNCTIONS_PARAMS
    return {
        mappings[func_name][param][0]: mappings[func_name][param][1](value)
        for param, value in params.items()
        if value is not None and param in mappings[func_name]
    }
