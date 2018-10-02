# pixcat

[![PyPI downloads](http://pepy.tech/badge/pixcat)](
    http://pepy.tech/project/pixcat)
[![PyPI version](https://img.shields.io/pypi/v/pixcat.svg)](
    https://pypi.org/project/pixcat)
[![PyPI pyversions](https://img.shields.io/pypi/pyversions/pixcat.svg)](
    https://pypi.python.org/pypi/pixcat)

**WORK IN PROGRESS**

Display images on a [kitty](https://sw.kovidgoyal.net/kitty/) terminal
with optional custom/thumbnail/fit-to-screen resizing.  
Developed with the goal of being a more powerful alternative to `kitty icat`,
while also providing an usable Python 3.6+ API.

## Usage

Basic CLI examples:

```sh
pixcat file.jpg

pixcat fit-screen --enlarge /tmp/abc.jpg

pixcat thumbnail --size 128 --align left 'https://picsum.photos/480?random'

pixcat resize --min-width 1920 --min-height 1080 \
              --max-width 1920 --max-height 1080 \
              ~/images/wallpapers 1.jpg 2.png
```

The commands and options have short forms too.  
See `pixcat --help` for more information.

Same examples using the Python package (no documentation yet):

```python3
from pixcat import Image

Image("file.jpg").show()

Image("/tmp/abc.jpg").fit_screen(enlarge=True).show()

Image("https://picsum.photos/480?random").thumbnail(128).show(align="left")

for i in Image.factory("~/images/wallpapers", "1.jpg", "2.png"):
    i.resize(1920, 1080, 1920, 1080).show()
```

## Installation

Requires Python 3.6+, tested on GNU/Linux only.

```sh
pip3 install --upgrade pixcat
```
