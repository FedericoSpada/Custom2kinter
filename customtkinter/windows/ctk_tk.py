from __future__ import annotations

import tkinter
import sys
import os
import platform
import ctypes
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack
from packaging import version

from .widgets.appearance_mode import CTkAppearanceModeBaseClass
from .widgets.scaling import CTkScalingBaseClass
from .widgets.core_widget_classes import CTkContainer
from .widgets.theme import ColorType, ThemeManager
from .widgets.utility import pop_from_dict_by_iterable, check_kwargs_empty, parse_geometry_string


class CTkThemedArgs(TypedDict, total=False):
    fg_color: ColorType
    title: str

class ValidTkArgs(TypedDict, total=False):
    use: int | str | None
    #--- Constructor only ---
    baseName: str | None
    className: str
    screenName: str | None
    useTk: bool
    sync: bool
    #--- Configure only ---
    bd: float | str
    border: float | str
    borderwidth: float | str
    class_: str
    cursor: str
    height: float | str
    width: float | str
    padx: float | int | str
    pady: float | int | str
    highlightthickness: float | str
    highlightbackground: str
    highlightcolor: str
    menu: tkinter.Menu
    relief: Literal["raised", "sunken", "flat", "ridge", "solid", "groove"]
    takefocus: bool
    container: bool
    screen: str
    visual: str | tuple[str, int]

class CTkArgs(CTkThemedArgs, ValidTkArgs, total=False):
    pass


class CTk(tkinter.Tk, CTkAppearanceModeBaseClass, CTkScalingBaseClass, CTkContainer):
    """
    Main app window with dark titlebar on Windows and macOS.
    For detailed information check out the documentation.
    """

    _deactivate_macos_window_header_manipulation: bool = False
    _deactivate_windows_window_header_manipulation: bool = False

    def __init__(self, **kwargs: Unpack[CTkArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkThemedArgs.__annotations__)
        self._theme_info: CTkThemedArgs = ThemeManager.get_info("CTk", None, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key], transparency=False)

        self._enable_macos_dark_title_bar()

        # call init methods of super classes
        tkinter.Tk.__init__(self, **pop_from_dict_by_iterable(kwargs, ValidTkArgs.__annotations__))
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="window")
        CTkContainer.__init__(self, fg_color=self._theme_info["fg_color"])

        # _desired_width and _desired_height represent desired size set by geometry or when resizing the window and
        # don't consider the scaling factor
        self._desired_width: int = 600
        self._desired_height: int = 500
        self._min_width: int = 0
        self._min_height: int = 0
        self._max_width: int = 1_000_000
        self._max_height: int = 1_000_000

        # set bg of tkinter.Tk
        super().configure(bg=self._apply_appearance_mode(self._fg_color))

        # set title
        super().title(self._theme_info["title"])

        # functionality
        self._iconbitmap_method_called: bool = False  # indicates if wm_iconbitmap method got called
        self._state_before_windows_set_titlebar_color: str | None = None
        self._window_exists: bool = False  # indicates if the window is already shown through update() or mainloop() after init
        self._withdraw_called_before_window_exists: bool = False  # indicates if withdraw() was called before window is first shown through update() or mainloop()
        self._iconify_called_before_window_exists: bool = False  # indicates if iconify() was called before window is first shown through update() or mainloop()
        self._block_update_dimensions_event: bool = False
        self.focused_widget_before_widthdraw: tkinter.Misc | None = None

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        # Windows only
        if sys.platform.startswith("win"):
            # set CustomTkinter titlebar icon
            self.after(200, self._windows_set_titlebar_icon)
            # set titlebar color
            self._windows_set_titlebar_color(self._get_appearance_mode())

        self.bind("<Configure>", self._update_dimensions_event)
        self.bind("<FocusIn>", self._focus_in_event)
        #allows CTkEntry and CTkTextbox to lose focus
        def set_focus(event: tkinter.Event) -> None:
            if hasattr(event.widget, "focus_set"):
                event.widget.focus_set()
        self.bind_all("<Button-1>", set_focus, add=True)

    def destroy(self) -> None:
        self._disable_macos_dark_title_bar()

        # call destroy methods of super classes
        tkinter.Tk.destroy(self)
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

        #delete still existing after() tasks (old Python versions don't have after_info)
        if hasattr(self, "after_info"):
            for after_id in self.after_info():
                self.after_cancel(after_id)

    def _focus_in_event(self, _: tkinter.Event) -> None:
        # sometimes window looses jumps back on macOS if window is selected from Mission Control, so has to be lifted again
        if sys.platform == "darwin":
            self.lift()

    def _update_dimensions_event(self, _: tkinter.Event) -> None:
        if not self._block_update_dimensions_event:
            # detect current window size
            self._desired_width = self._reverse_scaling(super().winfo_width())
            self._desired_height = self._reverse_scaling(super().winfo_height())

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        # Force new dimensions on window by using min, max, and geometry. Without min, max it won't work.
        super().minsize(self._apply_scaling(self._desired_width), self._apply_scaling(self._desired_height))
        super().maxsize(self._apply_scaling(self._desired_width), self._apply_scaling(self._desired_height))

        super().geometry(f"{self._apply_scaling(self._desired_width)}x{self._apply_scaling(self._desired_height)}")

        # set new scaled min and max with delay (delay prevents weird bug where window dimensions snap to unscaled dimensions when mouse releases window)
        self.after(1000, self._set_scaled_min_max)  # Why 1000ms delay? Experience! (Everything tested on Windows 11)

    def block_update_dimensions_event(self) -> None:
        self._block_update_dimensions_event = False

    def unblock_update_dimensions_event(self) -> None:
        self._block_update_dimensions_event = False

    def _set_scaled_min_max(self) -> None:
        super().minsize(self._apply_scaling(self._min_width), self._apply_scaling(self._min_height))
        super().maxsize(self._apply_scaling(self._max_width), self._apply_scaling(self._max_height))

    def withdraw(self) -> None:
        if not self._window_exists:
            self._withdraw_called_before_window_exists = True
        super().withdraw()

    def iconify(self) -> None:
        if not self._window_exists:
            self._iconify_called_before_window_exists = True
        super().iconify()

    def update(self) -> None:
        if not self._window_exists:
            if sys.platform.startswith("win"):
                if not self._withdraw_called_before_window_exists and not self._iconify_called_before_window_exists:
                    self.deiconify()
            self._window_exists = True
        super().update()

    def mainloop(self, *args: Any, **kwargs: Any) -> None:
        if not self._window_exists:
            if sys.platform.startswith("win"):
                self._windows_set_titlebar_color(self._get_appearance_mode())

                if not self._withdraw_called_before_window_exists and not self._iconify_called_before_window_exists:
                    self.deiconify()

            self._window_exists = True
        super().mainloop(*args, **kwargs)

    def resizable(self, width: bool | None = None, height: bool | None = None) -> tuple[bool, bool] | None:
        current_resizable_values = super().resizable(width, height)

        if sys.platform.startswith("win"):
            self._windows_set_titlebar_color(self._get_appearance_mode())

        return current_resizable_values

    def minsize(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None:
            self._min_width = width
            self._desired_width = max(self._desired_width, width)
        if height is not None:
            self._min_height = height
            self._desired_height = max(self._desired_width, height)
        super().minsize(self._apply_scaling(self._min_width), self._apply_scaling(self._min_height))

    def maxsize(self, width: int | None = None, height: int | None = None) -> None:
        if width is not None:
            self._max_width = width
            self._desired_width = min(self._desired_width, width)
        if height is not None:
            self._max_height = height
            self._desired_height = min(self._desired_width, height)
        super().maxsize(self._apply_scaling(self._max_width), self._apply_scaling(self._max_height))

    def geometry(self, geometry_string: str | None = None) -> str | None:
        if geometry_string is not None:
            super().geometry(self._apply_geometry_scaling(geometry_string))

            # update width and height attributes
            width, height, _, _ = parse_geometry_string(geometry_string)
            if width is not None and height is not None:
                # bound values between min and max
                self._desired_width = max(self._min_width, min(width, self._max_width))
                self._desired_height = max(self._min_height, min(height, self._max_height))
            return None
        else:
            return self._reverse_geometry_scaling(super().geometry())

    def configure(self, **kwargs: Unpack[CTkArgs]) -> None:
        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"))
            self._theme_info["fg_color"] = self._fg_color
            super().configure(bg=self._apply_appearance_mode(self._fg_color))

            self.propagate_fg_color(self.winfo_children())

        if "title" in kwargs:
            self.title(kwargs.pop("title"))

        super().configure(**pop_from_dict_by_iterable(kwargs, ValidTkArgs.__annotations__))
        check_kwargs_empty(kwargs, raise_error=True)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "fg_color":
            return self._theme_info["fg_color"]
        else:
            return super().cget(attribute_name)

    def wm_iconbitmap(self, bitmap: Any = None, default: Any = None) -> None:
        self._iconbitmap_method_called = True
        super().wm_iconbitmap(bitmap, default)

    def iconbitmap(self, bitmap: Any = None, default: Any = None) -> None:
        self._iconbitmap_method_called = True
        super().wm_iconbitmap(bitmap, default)

    def _windows_set_titlebar_icon(self) -> None:
        try:
            # if not the user already called iconbitmap method, set icon
            if not self._iconbitmap_method_called:
                customtkinter_directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                self.iconbitmap(os.path.join(customtkinter_directory, "assets", "icons", "CustomTkinter_icon_Windows.ico"))
        except Exception:
            pass

    @classmethod
    def _enable_macos_dark_title_bar(cls) -> None:
        if sys.platform == "darwin" and not cls._deactivate_macos_window_header_manipulation:  # macOS
            if version.parse(platform.python_version()) < version.parse("3.10"):
                if version.parse(tkinter.Tcl().call("info", "patchlevel")) >= version.parse("8.6.9"):  # Tcl/Tk >= 8.6.9
                    os.system("defaults write -g NSRequiresAquaSystemAppearance -bool No")
                    # This command allows dark-mode for all programs

    @classmethod
    def _disable_macos_dark_title_bar(cls) -> None:
        if sys.platform == "darwin" and not cls._deactivate_macos_window_header_manipulation:  # macOS
            if version.parse(platform.python_version()) < version.parse("3.10"):
                if version.parse(tkinter.Tcl().call("info", "patchlevel")) >= version.parse("8.6.9"):  # Tcl/Tk >= 8.6.9
                    os.system("defaults delete -g NSRequiresAquaSystemAppearance")
                    # This command reverts the dark-mode setting for all programs.

    def _windows_set_titlebar_color(self, appearance_mode: Literal["light", "dark"]) -> None:
        """
        Set the titlebar color of the window to light or dark theme on Microsoft Windows.

        Credits for this function:
        https://stackoverflow.com/questions/23836000/can-i-change-the-title-bar-in-tkinter/70724666#70724666

        MORE INFO:
        https://docs.microsoft.com/en-us/windows/win32/api/dwmapi/ne-dwmapi-dwmwindowattribute
        """

        if sys.platform.startswith("win") and not self._deactivate_windows_window_header_manipulation:

            if self._window_exists:
                self._state_before_windows_set_titlebar_color = self.state()

                if self._state_before_windows_set_titlebar_color != "iconic" or self._state_before_windows_set_titlebar_color != "withdrawn":
                    self.focused_widget_before_widthdraw = self.focus_get()
                    super().withdraw()  # hide window so that it can be redrawn after the titlebar change so that the color change is visible
            else:
                self.focused_widget_before_widthdraw = self.focus_get()
                super().withdraw()
                super().update()

            if appearance_mode.lower() == "dark":
                value = ctypes.c_int(1)
            elif appearance_mode.lower() == "light":
                value = ctypes.c_int(0)
            else:
                return

            try:
                hwnd = ctypes.windll.user32.GetParent(self.winfo_id())
                DWMWA_USE_IMMERSIVE_DARK_MODE = 20
                DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1 = 19

                # try with DWMWA_USE_IMMERSIVE_DARK_MODE
                if ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE,
                                                              ctypes.byref(value),
                                                              ctypes.sizeof(value)) != 0:

                    # try with DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20h1
                    ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, DWMWA_USE_IMMERSIVE_DARK_MODE_BEFORE_20H1,
                                                               ctypes.byref(value),
                                                               ctypes.sizeof(value))

            except Exception as err:
                print(err)

            if self._window_exists:
                if self._state_before_windows_set_titlebar_color == "normal":
                    self.deiconify()
                elif self._state_before_windows_set_titlebar_color == "iconic":
                    self.iconify()
                elif self._state_before_windows_set_titlebar_color == "zoomed":
                    self.state("zoomed")
                else:
                    self.state(self._state_before_windows_set_titlebar_color)  # other states

            if self.focused_widget_before_widthdraw is not None:
                self.after(10, self.focused_widget_before_widthdraw.focus)
                self.focused_widget_before_widthdraw = None

    def _set_appearance_mode(self) -> None:
        if sys.platform.startswith("win"):
            self._windows_set_titlebar_color(self._get_appearance_mode())

        super().configure(bg=self._apply_appearance_mode(self._fg_color))
