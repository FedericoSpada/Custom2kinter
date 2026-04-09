from __future__ import annotations

from tkinter.font import Font
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from ..theme import ThemeManager


class CTkFontArgs(TypedDict, total=False):
    family: str
    size: int
    weight: Literal["normal", "bold"]
    slant: Literal["italic", "roman"]
    underline: bool
    overstrike: bool


class CTkFont(Font):
    """
    Font object with size in pixel, independent of scaling.
    To get scaled tuple representation use create_scaled_tuple() method.

    family	The font family name as a string.
    size	The font height as an integer in pixel.
    weight	'bold' for boldface, 'normal' for regular weight.
    slant	'italic' for italic, 'roman' for unslanted.
    underline	1 for underlined text, 0 for normal.
    overstrike	1 for overstruck text, 0 for normal.

    Tkinter Font: https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/fonts.html
    """

    def __init__(self,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkFontArgs]) -> None:

        self._theme_info: CTkFontArgs = ThemeManager.get_info("CTkFont", theme_key, **kwargs)

        super().__init__(family=self._theme_info["family"],
                         size=-abs(self._theme_info["size"]),
                         weight=self._theme_info["weight"],
                         slant=self._theme_info["slant"],
                         underline=self._theme_info["underline"],
                         overstrike=self._theme_info["overstrike"])

        #functionality
        self._family: str = super().cget("family")
        self._tuple_style_string: str = self._get_style_string()
        self._size_configure_callback_list: list[Callable[[], None]] = []

    @classmethod
    def from_parameter(cls, parameter: CTkFont | CTkFontArgs | tuple | str) -> CTkFont:
        if isinstance(parameter, CTkFont):
            return parameter

        elif isinstance(parameter, dict):
            return CTkFont(**parameter)

        elif isinstance(parameter, tuple) and 2 <= len(parameter) <= 3:
            style = parameter[2] if len(parameter) >= 3 else ""
            return CTkFont(family=parameter[0],
                           size=parameter[1],
                           weight="bold" if "bold" in style else "normal",
                           slant="italic" if "italic" in style else "roman",
                           underline="underline" in style,
                           overstrike="overstrike" in style)

        elif isinstance(parameter, tuple) and 4 <= len(parameter) <= 6:
            parameter += ("",) * (6 - len(parameter))
            return CTkFont(family=parameter[0],
                           size=parameter[1],
                           weight="bold" if "bold" in parameter[2] else "normal",
                           slant="italic" if "italic" in parameter[3] else "roman",
                           underline="underline" in parameter[4],
                           overstrike="overstrike" in parameter[5])

        elif isinstance(parameter, str):
            return CTkFont(theme_key=parameter)

        else:
            raise ValueError(f"Wrong font type {type(parameter)}.\n" +
                             "For consistency, Customtkinter requires the font argument to be a tuple of len 2 to 6, " +
                             "an instance of CTkFont, an instance of CTkFontArgs or a str representing a custom theme key.\n" +
                             "\nUsage example:\n" +
                             "font=customtkinter.CTkFont(family='<name>', size=<size in px>)\n" +
                             "font=('<name>', <size in px>)\n" +
                             "font={'family': '<name>', 'size': <size in px>}\n" +
                             "font='<theme_key>'\n")

    def add_size_configure_callback(self, callback: Callable[[], None]) -> None:
        """ add function, that gets called when font got configured """
        self._size_configure_callback_list.append(callback)

    def remove_size_configure_callback(self, callback: Callable[[], None]) -> None:
        """ remove function, that gets called when font got configured """
        try:
            self._size_configure_callback_list.remove(callback)
        except ValueError:
            pass

    def create_scaled_tuple(self, font_scaling: float) -> tuple[str, int, str]:
        """ return scaled tuple representation of font in the form (family: str, size: int, style: str)"""
        return self._family, round(-abs(self._theme_info["size"]) * font_scaling), self._tuple_style_string

    def config(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("'config' is not implemented for CTk widgets. For consistency, always use 'configure' instead.")

    def configure(self, **kwargs: Unpack[CTkFontArgs]) -> None:
        if "family" in kwargs:
            super().configure(family=kwargs.pop("family"))
            self._family = super().cget("family")

        if "size" in kwargs:
            self._theme_info["size"] = kwargs.pop("size")
            super().configure(size=-abs(self._theme_info["size"]))

        super().configure(**kwargs)

        # update style string for create_scaled_tuple() method
        self._tuple_style_string = self._get_style_string()

        # call all functions registered with add_size_configure_callback()
        for callback in self._size_configure_callback_list:
            callback()

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "size":
            return self._theme_info["size"]
        else:
            return super().cget(attribute_name)

    def copy(self) -> CTkFont:
        return copy.deepcopy(self)

    def _get_style_string(self) -> str:
        weight = super().cget('weight')
        slant = self._theme_info['slant']
        underline = " underline" if self._theme_info["underline"] else ""
        overstrike = " overstrike" if self._theme_info["overstrike"] else ""
        return f"{weight} {slant}{underline}{overstrike}"
