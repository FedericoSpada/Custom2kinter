from __future__ import annotations

from typing_extensions import Literal

from .appearance_mode_tracker import AppearanceModeTracker
from ..theme import ColorType, TransparentColorType


class CTkAppearanceModeBaseClass:
    """
    Super-class that manages the appearance mode. Methods:

    - destroy() must be called when sub-class is destroyed
    - _set_appearance_mode() abstractmethod, gets called when appearance mode changes, must be overridden
    - _apply_appearance_mode() to convert tuple color

    """
    def __init__(self) -> None:
        AppearanceModeTracker.add(self._set_appearance_mode, self)

    def destroy(self) -> None:
        AppearanceModeTracker.remove(self._set_appearance_mode)

    def _set_appearance_mode(self) -> None:
        """ Called when appearance mode changes """

    def _get_appearance_mode(self) -> Literal["light", "dark"]:
        """ get appearance mode as a string, 'light' or 'dark' """
        if AppearanceModeTracker.get_mode() == 0:
            return "light"
        else:
            return "dark"

    @staticmethod
    def _apply_appearance_mode(color: TransparentColorType,
                               if_transparent: ColorType | None = None) -> str:
        """
        'color' and 'if_transparent' can be either a single hex color string or a color name or they can be a
        tuple color with (light_color, dark_color).
        If the 'if_transparent' parameter is provided, 'color' is replaced with it if 'transparent'.
        The functions returns always a single color string based on the active appearance mode.
        """

        if color == "transparent" and if_transparent is not None:
            color = if_transparent

        if isinstance(color, (tuple, list)):
            return color[AppearanceModeTracker.get_mode()]
        else:
            return color

    @staticmethod
    def _check_color_type(color: TransparentColorType | list[str],
                          transparency: bool = False) -> TransparentColorType:
        if color is None:
            raise ValueError("color is None, for transparency set color='transparent'")
        elif isinstance(color, (tuple, list)) and (color[0] == "transparent" or color[1] == "transparent"):
            raise ValueError(f"transparency is not allowed in tuple color {color}, use 'transparent'")
        elif color == "transparent" and not transparency:
            raise ValueError("transparency is not allowed for this attribute")
        elif isinstance(color, str):
            return color
        elif isinstance(color, (tuple, list)) and len(color) == 2 and isinstance(color[0], str) and isinstance(color[1], str):
            return tuple(color)
        else:
            raise ValueError(f"color {color} must be string ('transparent' or 'color-name' or 'hex-color') or tuple of two strings, not {type(color)}")
