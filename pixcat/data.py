ESC = "\033"

# kitty sends a response on stdin (...) for those actions
ACTIONS_WITH_ANSWER = {"display", "transmit+display", "query"}

IMAGE_CONTROLS = {
    "action": ("a", {
        "query":            "q",  # check if image is already transmited?
        "transmit":         "t",  # id key must be used to set stored image id
        "display":          "p",  # retrieve image from id, id key must be used
        "transmit+display": "T",
        "delete":           "d",
    }),
    "format": ("f", {
        "rgb":  "24",
        "rgba": "32",
        "png":  "100",
    }),
    "medium": ("t", {
        "direct":    "d",  # payload: base64 raw image data, 4096 bytes chunks
        "file":      "f",  # payload: base64 file path
        "tempfile":  "t",  # like file, but the file will be deleted after
        "sharedmem": "s"   # payload: "/shared_mem_object_name"
    }),
    "compress": ("o", {
        "zlib": "z"
    }),
    "chunks": ("m", {
        "partial": "1",
        "final":   "0"
    }),
    "id": ("i", {}),

    # In px, no need to specify if format is png.
    "source_w": ("s", {}),
    "source_h": ("v", {}),


    "del_target": ("d", {
        "all":            "a",
        "id":             "i",  # specify using index key
        "at_cursor":      "c",  # current cursor position
        "at_cell":        "p",  # specify cell using origin_x and origin_y keys
        "at_cell_zindex": "q",  # same as above, but also specify z_index
        "at_cols":        "x",  # specify column using origin_x
        "at_row":         "y",  # specify row using origin_y
    }),

    # delete + free up stored image data
    "del_data_target": ("d", {
        "all":            "A",
        "id":             "I",
        "at_cursor":      "C",
        "at_cell":        "P",
        "at_cell_zindex": "Q",
        "at_cols":        "X",
        "at_row":         "Y",
        "at_zindex":      "Z",
    }),

    "offset_x":  ("X", {}),
    "offset_y":  ("Y", {}),

    "origin_x":  ("x", {}),
    "origin_y":  ("y", {}),
    "z_index":   ("z", {}),

    "crop_w": ("w", {}),
    "crop_h": ("h", {}),

    "fit_cols": ("c", {}),
    "fit_rows": ("r", {}),
}

CLI_TO_FUNCTIONS_PARAMS = {
    "resize": {
        "--min-width":   ("min_w",    int),
        "--min-height":  ("min_h",    int),
        "--max-width":   ("max_w",    int),
        "--max-height":  ("max_h",    int),
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
        "--horizontal-margin": ("h_margin", int),
        "--vertical-margin":   ("v_margin", int),
        "--stretch":           ("stretch",  bool),
        "--resample":          ("resample", str),
    },
    "show": {
        "--absolute-x": ("x",          int),
        "--absolute-y": ("y",          int),
        "--z-index":    ("z",          int),
        "--relative-x": ("relative_x", int),
        "--relative-y": ("relative_y", int),
        "--align":      ("align",      str),
        "--offset-x":   ("offset_x",   int),
        "--offset-y":   ("offset_y",   int),
        "--crop-w":     ("crop_w",     int),
        "--crop-h":     ("crop_h",     int),
    }
}
