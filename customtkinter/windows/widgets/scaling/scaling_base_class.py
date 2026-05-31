from __future__ import annotations

import copy
from typing import Any
from typing_extensions import Literal

from .scaling_tracker import ScalingTracker
from ..font import CTkFont
from ..utility import parse_geometry_string


class CTkScalingBaseClass:
    """
    Super-class that manages the scaling values and callbacks.
    Works for widgets and windows, type must be set in init method with
    scaling_type attribute. Methods:

    - _set_scaling() abstractmethod, gets called when scaling changes, must be overridden
    - destroy() must be called when sub-class is destroyed
    - _apply_scaling()
    - _reverse_scaling()
    - _apply_font_scaling()
    - _apply_argument_scaling()
    - _apply_geometry_scaling()
    - _reverse_geometry_scaling()

    """
    def __init__(self, scaling_type: Literal["widget", "window"] = "widget") -> None:
        self.__scaling_type: Literal["widget", "window"] = scaling_type
        self.__scaling: float = 1.0

        if self.__scaling_type == "widget":
            ScalingTracker.add_widget(self._set_scaling, self)
            self.__scaling = ScalingTracker.get_widget_scaling(self)
        elif self.__scaling_type == "window":
            ScalingTracker.activate_high_dpi_awareness()  # make process DPI aware
            ScalingTracker.add_window(self._set_scaling, self)
            self.__scaling = ScalingTracker.get_window_scaling(self)

    def destroy(self) -> None:
        if self.__scaling_type == "widget":
            ScalingTracker.remove_widget(self._set_scaling, self)
        elif self.__scaling_type == "window":
            ScalingTracker.remove_window(self)

    def get_scaling(self) -> float:
        return self.__scaling

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        """ Called when scaling factor changes.
        It can be overridden, but super method must be called at the beginning """
        self.__scaling = new_widget_scaling if self.__scaling_type == "widget" else new_window_scaling

    # Some parts of Tk - notably canvas - are very buggy with floats, because they use locale-dependent parsing
    # (and thus might not recognize "." as the decimal point)
    # https://wiki.tcl-lang.org/page/locale
    # https://github.com/python/cpython/issues/56767
    # Hence, we must ensure any integer value stays that way
    def _apply_scaling(self, value: int | float) -> int | float:
        if isinstance(value, int) or self.__scaling_type == "window":
            return round(value * self.__scaling)
        else:
            return value * self.__scaling

    def _reverse_scaling(self, value: int | float) -> int | float:
        if isinstance(value, int) or self.__scaling_type == "window":
            return round(value / self.__scaling)
        else:
            return value / self.__scaling

    def _apply_font_scaling(self, font: CTkFont | tuple) -> tuple:
        """ Takes CTkFont object and returns tuple font with scaled size, has to be called again for every change of font object """
        if isinstance(font, tuple):
            if len(font) == 1:
                return font
            elif len(font) == 2:
                return font[0], -abs(round(font[1] * self.__scaling))
            elif 3 <= len(font) <= 6:
                return font[0], -abs(round(font[1] * self.__scaling)), font[2:]
            else:
                raise ValueError(f"Can not scale font {font}. font needs to be tuple of len 1-6")
        elif isinstance(font, CTkFont):
            return font.create_scaled_tuple(self.__scaling)
        else:
            raise ValueError(f"Can not scale font '{font}' of type {type(font)}. font needs to be tuple or instance of CTkFont")

    def _apply_argument_scaling(self, kwargs: dict[str, Any]) -> dict[str, Any]:
        scaled_kwargs = copy.copy(kwargs)

        # scale padding values and x, y values for place geometry manager
        for key in ("padx", "pady", "x", "y"):
            if key in scaled_kwargs:
                if isinstance(scaled_kwargs[key], (int, float)):
                    scaled_kwargs[key] = self._apply_scaling(scaled_kwargs[key])
                elif isinstance(scaled_kwargs[key], tuple):
                    scaled_kwargs[key] = tuple(self._apply_scaling(v) for v in scaled_kwargs[key])

        return scaled_kwargs

    def _apply_geometry_scaling(self, geometry_string: str) -> str:
        width, height, x, y = parse_geometry_string(geometry_string)

        retval = ""
        if width is not None and height is not None:
            retval += f"{round(width * self.__scaling)}x{round(height * self.__scaling)}"
        if x is not None and y is not None:
            retval += f"+{x}+{y}"
        return retval

    def _reverse_geometry_scaling(self, scaled_geometry_string: str) -> str:
        width, height, x, y = parse_geometry_string(scaled_geometry_string)

        retval = ""
        if width is not None and height is not None:
            retval += f"{round(width / self.__scaling)}x{round(height / self.__scaling)}"
        if x is not None and y is not None:
            retval += f"+{x}+{y}"
        return retval
