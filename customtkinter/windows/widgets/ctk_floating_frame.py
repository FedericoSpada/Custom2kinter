from __future__ import annotations

import tkinter
import sys
from typing import Any
from typing_extensions import TypedDict, Unpack

from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame, CTkFrameThemedArgs
from ..ctk_toplevel import CTkToplevel
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkFloatingFrameThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int  #not used on Linux
    border_width: int
    fg_color: TransparentColorType
    border_color: ColorType
    transparency: float

class CTkFloatingFrameArgs(CTkFloatingFrameThemedArgs, total=False, closed=True):
    pass


class CTkFloatingFrame(CTkFrame):
    """
    Frame with rounded corners and border, detached from any window and always on top of everything.
    For detailed information check out the documentation.
    """

    #if you need to use exactly these colors inside any CTkFloatingFrame, change them to something else
    transparent_color = ("#FEFDFE", "#010201")

    def __init__(self,
                 master: tkinter.Misc | None = None,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkFloatingFrameArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkFloatingFrameThemedArgs.__annotations__)
        self._theme_ff_info: CTkFloatingFrameThemedArgs = ThemeManager.get_info("CTkFloatingFrame", theme_key, **theme_args)

        #validity checks
        for key in self._theme_ff_info:
            if "_color" in key:
                self._theme_ff_info[key] = self._check_color_type(self._theme_ff_info[key],
                                                                  transparency=key == "fg_color")

        # toplevel
        self._toplevel = CTkToplevel(master)
        self._toplevel.withdraw()
        self._toplevel.attributes("-topmost", True)
        self._toplevel.attributes("-alpha", 1.0 - self._theme_ff_info["transparency"])
        self._toplevel.resizable(width=True, height=True)

        if sys.platform.startswith("win"):
            self._toplevel.overrideredirect(True)
            self._toplevel.attributes("-transparentcolor", self._apply_appearance_mode(self.transparent_color))
            self._toplevel.attributes("-toolwindow", True) # removes icon from taskbar
        elif sys.platform.startswith("darwin"):
            if tkinter.TkVersion >= 9.0: #necessary to achieve transparent edges due to changes in Tk 9.x on MacOS
                self._toplevel.wm_attributes(stylemask=('fullsizecontent','titled'))
                self._toplevel.title("")
                self._theme_ff_info["corner_radius"] = 0
            else:
                self._toplevel.overrideredirect(True)
                self.transparent_color = "systemTransparent"
                self._toplevel.attributes("-transparent", True)
        else:
            #Linux doesn't support transparency, so we force the frame to cover all available space
            self._toplevel.overrideredirect(True)
            self._theme_ff_info["corner_radius"] = 0

        # frame
        frame_kwargs = {key: value for key, value in self._theme_ff_info.items() if key in CTkFrameThemedArgs.__annotations__}
        super().__init__(master=self._toplevel, bg_color=self.transparent_color, **frame_kwargs)
        self.pack(fill=tkinter.BOTH, expand=True)

        # functionality
        self._open_kwargs: dict[str, Any] = {}

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self.bind("<Configure>", lambda _: self.update_dimensions(), add=True)

    def _set_appearance_mode(self) -> None:
        if sys.platform.startswith("win"):
            self._toplevel.attributes("-transparentcolor", self._apply_appearance_mode(self.transparent_color))
        super()._set_appearance_mode()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkFloatingFrameArgs]) -> None:
        if "corner_radius" in kwargs:
            if sys.platform.startswith("linux"):
                kwargs.pop("corner_radius")

        if "transparency" in kwargs:
            self._theme_ff_info["transparency"] = kwargs.pop("transparency")
            self._toplevel.attributes("-alpha", 1.0 - self._theme_ff_info["transparency"])

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "transparency":
            return self._theme_ff_info["transparency"]
        else:
            return super().cget(attribute_name)

    def open(self, x_root: int, y_root: int, anchor: AnchorType = "nw") -> None:
        """ Shows the frame in the position where the corner provided with 'anchor'
        is exactly at (x_root, y_root) coordinates with respect to the screen. """

        #memorize values to be re-applied if needed
        self._open_kwargs["x_root"] = x_root
        self._open_kwargs["y_root"] = y_root
        self._open_kwargs["anchor"] = anchor

        self._toplevel.update_idletasks()
        width = self.winfo_reqwidth()
        height = self.winfo_reqheight()

        if anchor == "center":
            anchor = ""

        if   "w" in anchor: x_delta = 0
        elif "e" in anchor: x_delta = width
        else:               x_delta = round(width / 2)
        if   "n" in anchor: y_delta = 0
        elif "s" in anchor: y_delta = height
        else:               y_delta = round(height / 2)

        self._toplevel.geometry(f"{width}x{height}+{x_root - x_delta}+{y_root - y_delta}",
                                apply_scaling=False)
        self._toplevel.deiconify()
        if tkinter.TkVersion >= 9.0 and sys.platform.startswith("darwin"): #necessary to achieve transparent edges due to changes in Tk 9.x on MacOS
            self._toplevel.wm_attributes(stylemask=('fullsizecontent','titled'))

    def close(self) -> None:
        """ Hides the widget. """
        self._open_kwargs.clear()
        self._toplevel.withdraw()

    def is_open(self) -> bool:
        """ Returns whether the frame is currently open. """
        return bool(self._open_kwargs)

    def update_dimensions(self) -> None:
        """ If new widgets are added in a second moment, it's better to call
        this method to force an update of the dimensions. """
        if self._open_kwargs:
            self.open(**self._open_kwargs)
