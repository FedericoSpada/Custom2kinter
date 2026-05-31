from __future__ import annotations

from typing import Iterable
from abc import ABC
import tkinter
from ..theme import ColorType, TransparentColorType
from ..appearance_mode import CTkAppearanceModeBaseClass



class CTkContainer(ABC):

    def __init__(self,
                 fg_color: TransparentColorType) -> None:

        # foreground color: it is used as bg_color for children widgets.
        # if set as "transparent", sub-classes must override get_fg_color()
        # to provide a different value
        self._fg_color: TransparentColorType = CTkAppearanceModeBaseClass._check_color_type(fg_color, transparency=True)

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
