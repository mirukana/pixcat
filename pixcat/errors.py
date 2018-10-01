# Copyright 2018 miruka
# This file is part of pixcat, licensed under LGPLv3.

"pixcat exceptions"


class BadFileError(Exception):
    def __init__(self, image, text: str = ""):
        super().__init__(f"{image.path}: {text}")


class NotOKAnswerError(Exception):
    def __init__(self, from_code: str, answer: str):
        super().__init__(f"{from_code!r} : terminal responded with {answer!r}")
