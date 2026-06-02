from __future__ import annotations

import tkinter
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer
from .font.ctk_font import FontType
from .theme import ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame
from .ctk_button import CTkButton
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkSegmentedButtonThemedArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: ColorType
    selected_color: ColorType
    unselected_color: ColorType
    selected_hover_color: ColorType
    unselected_hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    font: FontType

class CTkSegmentedButtonArgs(CTkSegmentedButtonThemedArgs, total=False):
    state: Literal["normal", "disabled"]
    values: list[str] | None
    variable: tkinter.StringVar | None
    command: Callable[[str], None] | None
    background_corner_colors: tuple[ColorType, ...] | None


class CTkSegmentedButton(CTkFrame):
    """
    Segmented button with corner radius, border width, variable support.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkSegmentedButtonArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkSegmentedButtonThemedArgs.__annotations__)
        self._theme_sb_info: CTkSegmentedButtonThemedArgs = ThemeManager.get_info("CTkSegmentedButton", theme_key, **theme_args)

        #validity checks
        for key in self._theme_sb_info:
            if "_color" in key:
                self._theme_sb_info[key] = self._check_color_type(self._theme_sb_info[key],
                                                                  transparency=key == "bg_color")

        super().__init__(master=master,
                         bg_color=self._theme_sb_info["bg_color"],
                         fg_color="transparent",
                         width=self._theme_sb_info["width"],
                         height=self._theme_sb_info["height"],
                         corner_radius=self._theme_sb_info["corner_radius"])

        # rendering options
        self._background_corner_colors: tuple[ColorType, ...] | None = kwargs.pop("background_corner_colors", None)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", "normal")
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._values: list[str] = kwargs.pop("values", [])
        self._variable: tkinter.StringVar | None = kwargs.pop("variable", None)
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None
        self._buttons_dict: dict[str, CTkButton] = {}  # mapped from value to button object

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._check_unique_values(self._values)
        self._current_value: str = ""
        if len(self._values) > 0:
            self._create_buttons_from_values()
            self._update_geometry()

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self.set(self._variable.get(), from_variable_callback=True)

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        super().destroy()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        if height is not None:
            for button in self._buttons_dict.values():
                button.configure(height=height)

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    @staticmethod
    def _check_unique_values(values: list[str]) -> None:
        """ raises exception if values are not unique """
        if len(values) != len(set(values)):
            raise ValueError("CTkSegmentedButton values are not unique")

    def _configure_button_corners_for_index(self, index: int) -> None:
        fg_color = self._theme_sb_info["fg_color"]
        is_vertical = self._theme_sb_info["orientation"] == "vertical"
        button = self._buttons_dict[self._values[index]]

        #just one button
        if index == 0 and len(self._values) == 1:
            if self._background_corner_colors is None:
                button.configure(background_corner_colors=(self._bg_color, self._bg_color, self._bg_color, self._bg_color))
            else:
                button.configure(background_corner_colors=self._background_corner_colors)

        #first button (left/top)
        elif index == 0:
            if self._background_corner_colors is None:
                if is_vertical:
                    button.configure(background_corner_colors=(self._bg_color, self._bg_color, fg_color, fg_color))
                else:
                    button.configure(background_corner_colors=(self._bg_color, fg_color, fg_color, self._bg_color))
            else:
                if is_vertical:
                    button.configure(background_corner_colors=(self._background_corner_colors[0], self._background_corner_colors[1], fg_color, fg_color))
                else:
                    button.configure(background_corner_colors=(self._background_corner_colors[0], fg_color, fg_color, self._background_corner_colors[3]))

        #last button (right/bottom)
        elif index == len(self._values) - 1:
            if self._background_corner_colors is None:
                if is_vertical:
                    button.configure(background_corner_colors=(fg_color, fg_color, self._bg_color, self._bg_color))
                else:
                    button.configure(background_corner_colors=(fg_color, self._bg_color, self._bg_color, fg_color))
            else:
                if is_vertical:
                    button.configure(background_corner_colors=(fg_color, fg_color, self._background_corner_colors[2], self._background_corner_colors[3]))
                else:
                    button.configure(background_corner_colors=(fg_color, self._background_corner_colors[1], self._background_corner_colors[2], fg_color))

        #button in the middle
        else:
            button.configure(background_corner_colors=(fg_color, fg_color, fg_color, fg_color))

    def _unselect_button_by_value(self, value: str) -> None:
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(fg_color=self._theme_sb_info["unselected_color"],
                                                hover_color=self._theme_sb_info["unselected_hover_color"])

    def _select_button_by_value(self, value: str) -> None:
        self._unselect_button_by_value(self._current_value)
        self._current_value = value
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(fg_color=self._theme_sb_info["selected_color"],
                                                hover_color=self._theme_sb_info["selected_hover_color"])

    def _create_button(self, value: str) -> CTkButton:
        new_button = CTkButton(self,
                               width=0,
                               height=self._desired_height,
                               corner_radius=self._theme_sb_info["corner_radius"],
                               border_width=self._theme_sb_info["border_width"],
                               fg_color=self._theme_sb_info["unselected_color"],
                               border_color=self._theme_sb_info["fg_color"],
                               hover_color=self._theme_sb_info["unselected_hover_color"],
                               text_color=self._theme_sb_info["text_color"],
                               text_color_disabled=self._theme_sb_info["text_color_disabled"],
                               text=value,
                               font=self._theme_sb_info["font"],
                               state=self._state,
                               command=lambda v=value: self.set(v, from_button_callback=True))
        return new_button

    def _create_buttons_from_values(self) -> None:
        self._buttons_dict.clear()
        for index, value in enumerate(self._values):
            self._buttons_dict[value] = self._create_button(value)
            self._configure_button_corners_for_index(index)

    def _update_geometry(self) -> None:
        number_of_columns, number_of_rows = self.grid_size()
        if self._theme_sb_info["orientation"] == "vertical":
            # remove minsize from every grid cell in the first column
            for n in range(number_of_rows):
                self.grid_rowconfigure(n, weight=1, minsize=0)
            self.grid_columnconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_rowconfigure(index, weight=1, minsize=self._reverse_scaling(self._current_height))
                self._buttons_dict[value].grid(row=index, column=0, sticky="nsew")
        else:
            # remove minsize from every grid cell in the first row
            for n in range(number_of_columns):
                self.grid_columnconfigure(n, weight=1, minsize=0)
            self.grid_rowconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_columnconfigure(index, weight=1, minsize=self._reverse_scaling(self._current_height))
                self._buttons_dict[value].grid(row=0, column=index, sticky="nsew")

    def configure(self, **kwargs: Unpack[CTkSegmentedButtonArgs]) -> None:
        if "width" in kwargs:
            self._theme_sb_info["width"] = kwargs.pop("width")
            super().configure(width=self._theme_sb_info["width"])

        if "height" in kwargs:
            self._theme_sb_info["height"] = kwargs.pop("height")
            super().configure(height=self._theme_sb_info["height"])

        if "corner_radius" in kwargs:
            self._theme_sb_info["corner_radius"] = kwargs.pop("corner_radius")
            super().configure(corner_radius=self._theme_sb_info["corner_radius"])
            for button in self._buttons_dict.values():
                button.configure(corner_radius=self._theme_sb_info["corner_radius"])

        if "border_width" in kwargs:
            self._theme_sb_info["border_width"] = kwargs.pop("border_width")
            for button in self._buttons_dict.values():
                button.configure(border_width=self._theme_sb_info["border_width"])

        if "bg_color" in kwargs:
            self._theme_sb_info["bg_color"] = kwargs.pop("bg_color")
            super().configure(bg_color=self._theme_sb_info["bg_color"])
            if len(self._buttons_dict) > 0:
                self._configure_button_corners_for_index(0)
            if len(self._buttons_dict) > 1:
                self._configure_button_corners_for_index(len(self._buttons_dict) - 1)

        if "fg_color" in kwargs:
            self._theme_sb_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            for index, button in enumerate(self._buttons_dict.values()):
                button.configure(border_color=self._theme_sb_info["fg_color"])
                self._configure_button_corners_for_index(index)

        if "selected_color" in kwargs:
            self._theme_sb_info["selected_color"] = self._check_color_type(kwargs.pop("selected_color"))
            if self._current_value in self._buttons_dict:
                self._buttons_dict[self._current_value].configure(fg_color=self._theme_sb_info["selected_color"])

        if "selected_hover_color" in kwargs:
            self._theme_sb_info["selected_hover_color"] = self._check_color_type(kwargs.pop("selected_hover_color"))
            if self._current_value in self._buttons_dict:
                self._buttons_dict[self._current_value].configure(hover_color=self._theme_sb_info["selected_hover_color"])

        if "unselected_color" in kwargs:
            self._theme_sb_info["unselected_color"] = self._check_color_type(kwargs.pop("unselected_color"))
            for value, button in self._buttons_dict.items():
                if value != self._current_value:
                    button.configure(fg_color=self._theme_sb_info["unselected_color"])

        if "unselected_hover_color" in kwargs:
            self._theme_sb_info["unselected_hover_color"] = self._check_color_type(kwargs.pop("unselected_hover_color"))
            for value, button in self._buttons_dict.items():
                if value != self._current_value:
                    button.configure(hover_color=self._theme_sb_info["unselected_hover_color"])

        if "text_color" in kwargs:
            self._theme_sb_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            for button in self._buttons_dict.values():
                button.configure(text_color=self._theme_sb_info["text_color"])

        if "text_color_disabled" in kwargs:
            self._theme_sb_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            for button in self._buttons_dict.values():
                button.configure(text_color_disabled=self._theme_sb_info["text_color_disabled"])

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            for i in range(len(self._buttons_dict)):
                self._configure_button_corners_for_index(i)

        if "font" in kwargs:
            font = kwargs.pop("font")
            for button in self._buttons_dict.values():
                button.configure(font=font)

        if "values" in kwargs:
            for button in self._buttons_dict.values():
                button.destroy()
            self._values = kwargs.pop("values")

            self._check_unique_values(self._values)

            if len(self._values) > 0:
                self._create_buttons_from_values()
                self._update_geometry()

            if self._current_value in self._values:
                self._select_button_by_value(self._current_value)

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            for button in self._buttons_dict.values():
                button.configure(state=self._state)

        check_kwargs_empty(kwargs, raise_error=True)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name in self._theme_sb_info:
            return self._theme_sb_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def set(self, value: str, from_variable_callback: bool = False, from_button_callback: bool = False) -> None:
        """ Changes the selected value to the desired one, regardless of the widget's state and admissible values. """
        if value != self._current_value:
            self._select_button_by_value(value)

            if self._variable is not None and not from_variable_callback:
                self._variable_callback_blocked = True
                self._variable.set(value)
                self._variable_callback_blocked = False

            if from_button_callback:
                if self._command is not None:
                    self._command(self._current_value)

    def get(self, index: int | None = None) -> str:
        """ Returns the current value.\n
        If an index is provided, returns the value in that position. """
        if index is None:
            return self._current_value
        else:
            return self._values[index]

    def index(self, value: str | None = None) -> int:
        """ Returns index of selected value, raises ValueError if the value is missing.\n
        If the parameter is provided, returns the associated index or raises ValueError if no value is found. """
        if value is None:
            value = self._current_value
        return self._values.index(value)

    def insert(self, index: int, value: str) -> None:
        """ Creates new button with given value at position index. """
        if value == "":
            raise ValueError("CTkSegmentedButton can not insert value ''")
        if value in self._buttons_dict:
            raise ValueError(f"CTkSegmentedButton can not insert value '{value}', already part of the values")

        self._values.insert(index, value)
        self._buttons_dict[value] = self._create_button(value)

        self._configure_button_corners_for_index(index)
        if index > 0:
            self._configure_button_corners_for_index(index - 1)
        if index < len(self._buttons_dict) - 1:
            self._configure_button_corners_for_index(index + 1)

        self._update_geometry()

        if value == self._current_value:
            self._select_button_by_value(self._current_value)

    def add(self, value: str) -> None:
        """ Appends new button with given value. """
        self.insert(len(self._buttons_dict), value)

    def delete(self, value: str) -> None:
        """ Deletes button by value. """
        if value not in self._buttons_dict:
            raise ValueError(f"CTkSegmentedButton does not contain value '{value}'")

        self._buttons_dict.pop(value).destroy()
        index_to_remove = self.index(value)
        self._values.pop(index_to_remove)

        #there are still buttons
        if len(self._buttons_dict) > 0:
            # removed index was first element (left or top)
            if index_to_remove == 0:
                self._configure_button_corners_for_index(0)
            # removed index was last element (right or bottom)
            elif index_to_remove == len(self._buttons_dict):
                self._configure_button_corners_for_index(index_to_remove - 1)

        self._update_geometry()

    def len(self) -> int:
        """ Returns the number of defined buttons. """
        return len(self._values)

    def move(self, new_index: int, value: str) -> None:
        if not 0 <= new_index < len(self._values):
            raise ValueError(f"CTkSegmentedButton new_index {new_index} not in range of value list with len {len(self._values)}")
        if value not in self._buttons_dict:
            raise ValueError(f"CTkSegmentedButton has no value named '{value}'")

        self.delete(value)
        self.insert(new_index, value)
