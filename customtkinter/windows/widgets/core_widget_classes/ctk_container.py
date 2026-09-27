from __future__ import annotations

import tkinter
from abc import ABC
from typing import Iterable
from typing_extensions import TypedDict, Unpack

from ..theme import ColorType, TransparentColorType
from ..utility import check_kwargs_empty, check_colors


class CTkContainerArgs(TypedDict, total=False, closed=True):
    fg_color: TransparentColorType


class CTkContainer(ABC):

    def __init__(self, **kwargs: Unpack[CTkContainerArgs]) -> None:
        #validity checks
        check_colors(kwargs, CTkContainerArgs)

        # foreground color: it is used as bg_color for children widgets.
        # if set as "transparent", sub-classes must override get_fg_color()
        # to provide a different value
        self._fg_color: TransparentColorType = kwargs.pop("fg_color", "transparent")

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

    def get_fg_color(self) -> ColorType:
        if self._fg_color == "transparent":
            raise ValueError("Output of get_fg_color() method can't be 'transparent'.\n"
                             "It must be overridden to replace the attribute '_fg_color' with a true color")
        return self._fg_color

    def propagate_fg_color(self, children: Iterable[tkinter.Misc]) -> None:
        fg_color = self.get_fg_color()
        for child in children:
            try:
                child.configure(bg_color=fg_color)
            except Exception:
                pass
