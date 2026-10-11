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
    """
    Base class of every object that can contain other widgets.

    Its 'fg_color' is used as bg_color by the children widgets: classes that allow "transparent"
    must override get_fg_color() to return a true color, which is the value the children widgets use.
    Widgets require a CTkContainer as 'master'.
    """

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
        """
        Returns the actual main color of the widget.
        Children widgets use it to resolve their "transparent" color.

        Raises:
            ValueError: if the color is "transparent" and the method has not been overridden.
        """
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
