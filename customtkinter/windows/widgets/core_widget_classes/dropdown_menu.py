from __future__ import annotations

import tkinter
import sys
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from ..appearance_mode import CTkAppearanceModeBaseClass
from ..scaling import CTkScalingBaseClass
from ..theme import ThemeManager
from ..font.ctk_font import CTkFont, CTkFontArgs
from ..utility import pop_from_dict_by_set


class DropdownMenuArgs(TypedDict, total=False):
    fg_color: str | tuple[str, str]
    hover_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    min_character_width: int
    font: CTkFontArgs | CTkFont | tuple | str


class DropdownMenu(tkinter.Menu, CTkAppearanceModeBaseClass, CTkScalingBaseClass):

    # attributes that are passed to and managed by the tkinter menu only:
    _valid_tk_menu_attributes: set[str] = {"background", "bd", "border", "disabledforeground",
                                           "foreground", "name", "postcommand", "selectcolor",
                                           "takefocus", "tearoffcommand", "title", "type"}

    def __init__(self,
                 values: list[str] | None = None,
                 command: Callable[[str], None] | None = None,
                 **kwargs: Unpack[DropdownMenuArgs]) -> None:

        menu_kwargs = pop_from_dict_by_set(kwargs, self._valid_tk_menu_attributes)

        self._theme_info: DropdownMenuArgs = ThemeManager.get_info("DropdownMenu", None, **kwargs)

        # call init methods of super classes
        tkinter.Menu.__init__(self, **menu_kwargs)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        #functionality
        self._values: list[str] = [] if values is None else values
        self._command: Callable[[str], None] | None = command

        self._configure_menu_for_platforms()
        self._add_menu_commands()

    def destroy(self) -> None:
        if isinstance(self._font, CTkFont):
            self._font.remove_size_configure_callback(self._update_font)

        # call destroy methods of super classes
        tkinter.Menu.destroy(self)
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling """
        super().configure(font=self._apply_font_scaling(self._font))

    def _configure_menu_for_platforms(self) -> None:
        """ apply platform specific appearance attributes, configure all colors """

        if sys.platform == "darwin":
            super().configure(tearoff=False,
                              font=self._apply_font_scaling(self._font))

        elif sys.platform.startswith("win"):
            super().configure(tearoff=False,
                              relief="flat",
                              activebackground=self._apply_appearance_mode(self._theme_info["hover_color"]),
                              borderwidth=self._apply_widget_scaling(4),
                              activeborderwidth=self._apply_widget_scaling(4),
                              bg=self._apply_appearance_mode(self._theme_info["fg_color"]),
                              fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                              activeforeground=self._apply_appearance_mode(self._theme_info["text_color"]),
                              font=self._apply_font_scaling(self._font),
                              cursor="hand2")

        else:
            super().configure(tearoff=False,
                              relief="flat",
                              activebackground=self._apply_appearance_mode(self._theme_info["hover_color"]),
                              borderwidth=0,
                              activeborderwidth=0,
                              bg=self._apply_appearance_mode(self._theme_info["fg_color"]),
                              fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                              activeforeground=self._apply_appearance_mode(self._theme_info["text_color"]),
                              font=self._apply_font_scaling(self._font))

    def _add_menu_commands(self) -> None:
        """ delete existing menu labels and createe new labels with command according to values list """

        self.delete(0, "end")  # delete all old commands

        if sys.platform.startswith("linux"):
            for value in self._values:
                self.add_command(label="  " + value.ljust(self._theme_info["min_character_width"]) + "  ",
                                 command=lambda v=value: self._button_callback(v),
                                 compound="left")
        else:
            for value in self._values:
                self.add_command(label=value.ljust(self._theme_info["min_character_width"]),
                                 command=lambda v=value: self._button_callback(v),
                                 compound="left")

    def _button_callback(self, value: str) -> None:
        if self._command is not None:
            self._command(value)

    def open(self, x: int | float, y: int | float) -> None:
        if sys.platform == "darwin":
            y += self._apply_widget_scaling(8)
        else:
            y += self._apply_widget_scaling(3)

        if sys.platform == "darwin" or sys.platform.startswith("win"):
            self.post(int(x), int(y))
        else:  # Linux
            self.tk_popup(int(x), int(y))

    def close(self) -> None:
        self.unpost()

    def is_open(self) -> bool:
        return bool(self.winfo_viewable())

    def configure(self, **kwargs: Unpack[DropdownMenuArgs]) -> None:
        if "min_character_width" in kwargs:
            self._theme_info["min_character_width"] = kwargs.pop("min_character_width")
            self._add_menu_commands()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            super().configure(bg=self._apply_appearance_mode(self._theme_info["fg_color"]))

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = self._check_color_type(kwargs.pop("hover_color"))
            super().configure(activebackground=self._apply_appearance_mode(self._theme_info["hover_color"]))

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            super().configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]))

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._add_menu_commands()

        super().configure(**kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)
        self._configure_menu_for_platforms()

    def _set_appearance_mode(self, mode: Literal["light", "dark"]) -> None:
        """ colors won't update on appearance mode change when dropdown is open, because it's not necessary """
        super()._set_appearance_mode(mode)
        self._configure_menu_for_platforms()
