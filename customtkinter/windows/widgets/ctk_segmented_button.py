from __future__ import annotations

import tkinter
import copy
from typing import Any, Callable
from typing_extensions import Literal

from .theme import ThemeManager
from .font import CTkFont
from .utility import check_kwargs_empty
from .ctk_frame import CTkFrame
from .ctk_button import CTkButton


class CTkSegmentedButton(CTkFrame):
    """
    Segmented button with corner radius, border width, variable support.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 width: int = 140,
                 height: int = 28,
                 corner_radius: int | None = None,
                 border_width: int = 3,

                 bg_color: str | tuple[str, str] = "transparent",
                 fg_color: str | tuple[str, str] | None = None,
                 selected_color: str | tuple[str, str] | None = None,
                 selected_hover_color: str | tuple[str, str] | None = None,
                 unselected_color: str | tuple[str, str] | None = None,
                 unselected_hover_color: str | tuple[str, str] | None = None,
                 text_color: str | tuple[str, str] | None = None,
                 text_color_disabled: str | tuple[str, str] | None = None,
                 background_corner_colors: tuple[str | tuple[str, str], ...] | None = None,

                 font: CTkFont | tuple | None = None,
                 values: list[str] | None = None,
                 variable: tkinter.StringVar | None = None,
                 dynamic_resizing: bool = True,
                 command: Callable[[str], None] | None = None,
                 state: Literal["normal", "disabled"] = "normal",
                 orientation: Literal["horizontal", "vertical"] = "horizontal") -> None:

        super().__init__(master=master, bg_color=bg_color, width=width, height=height)

        self._sb_fg_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["fg_color"] if fg_color is None else self._check_color_type(fg_color)

        self._sb_selected_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["selected_color"] if selected_color is None else self._check_color_type(selected_color)
        self._sb_selected_hover_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["selected_hover_color"] if selected_hover_color is None else self._check_color_type(selected_hover_color)

        self._sb_unselected_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["unselected_color"] if unselected_color is None else self._check_color_type(unselected_color)
        self._sb_unselected_hover_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["unselected_hover_color"] if unselected_hover_color is None else self._check_color_type(unselected_hover_color)

        self._sb_text_color: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["text_color"] if text_color is None else self._check_color_type(text_color)
        self._sb_text_color_disabled: str | tuple[str, str] = ThemeManager.theme["CTkSegmentedButton"]["text_color_disabled"] if text_color_disabled is None else self._check_color_type(text_color_disabled)

        self._sb_corner_radius: int = ThemeManager.theme["CTkSegmentedButton"]["corner_radius"] if corner_radius is None else corner_radius
        self._sb_border_width: int = ThemeManager.theme["CTkSegmentedButton"]["border_width"] if border_width is None else border_width

        self._background_corner_colors: tuple[str | tuple[str, str], ...] | None = background_corner_colors  # rendering options for DrawEngine

        self._command: Callable[[str], None] | None = command
        self._font: CTkFont | tuple = CTkFont() if font is None else font
        self._state: Literal["normal", "disabled"] = state
        self._orientation: Literal["horizontal", "vertical"] = orientation.lower()

        self._values: list[str] = ["CTkSegmentedButton"] if values is None else values
        self._buttons_dict: dict[str, CTkButton] = {}  # mapped from value to button object

        self._dynamic_resizing: bool = dynamic_resizing
        if not self._dynamic_resizing:
            self.grid_propagate(False)

        self._check_unique_values(self._values)
        self._current_value: str = ""
        if len(self._values) > 0:
            self._create_buttons_from_values()
            self._create_button_grid()

        self._variable: tkinter.StringVar | None = variable
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self.set(self._variable.get(), from_variable_callback=True)

        super().configure(corner_radius=self._sb_corner_radius, fg_color="transparent")

    def destroy(self) -> None:
        if self._variable is not None:  # remove old callback
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        for button in self._buttons_dict.values():
            button.configure(height=height)

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    def _get_index_by_value(self, value: str) -> int:
        for index, value_from_list in enumerate(self._values):
            if value_from_list == value:
                return index

        raise ValueError(f"CTkSegmentedButton does not contain value '{value}'")

    def _configure_button_corners_for_index(self, index: int) -> None:
        if index == 0 and len(self._values) == 1:
            if self._background_corner_colors is None:
                self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._bg_color, self._bg_color, self._bg_color, self._bg_color))
            else:
                self._buttons_dict[self._values[index]].configure(background_corner_colors=self._background_corner_colors)

        elif index == 0:
            if self._background_corner_colors is None:
                if self._orientation == "vertical":
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._bg_color, self._bg_color, self._sb_fg_color, self._sb_fg_color))
                else:
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._bg_color, self._sb_fg_color, self._sb_fg_color, self._bg_color))
            else:
                if self._orientation == "vertical":
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._background_corner_colors[0], self._background_corner_colors[1], self._sb_fg_color, self._sb_fg_color))
                else:
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._background_corner_colors[0], self._sb_fg_color, self._sb_fg_color, self._background_corner_colors[3]))

        elif index == len(self._values) - 1:
            if self._background_corner_colors is None:
                if self._orientation == "vertical":
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._sb_fg_color, self._sb_fg_color, self._bg_color, self._bg_color))
                else:
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._sb_fg_color, self._bg_color, self._bg_color, self._sb_fg_color))
            else:
                if self._orientation == "vertical":
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._sb_fg_color, self._sb_fg_color, self._background_corner_colors[2], self._background_corner_colors[3]))
                else:
                    self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._sb_fg_color, self._background_corner_colors[1], self._background_corner_colors[2], self._sb_fg_color))

        else:
            self._buttons_dict[self._values[index]].configure(background_corner_colors=(self._sb_fg_color, self._sb_fg_color, self._sb_fg_color, self._sb_fg_color))

    def _unselect_button_by_value(self, value: str) -> None:
        if value in self._buttons_dict:
            self._buttons_dict[value].configure(fg_color=self._sb_unselected_color,
                                                hover_color=self._sb_unselected_hover_color)

    def _select_button_by_value(self, value: str) -> None:
        if self._current_value is not None and self._current_value != "":
            self._unselect_button_by_value(self._current_value)

        self._current_value = value

        self._buttons_dict[value].configure(fg_color=self._sb_selected_color,
                                            hover_color=self._sb_selected_hover_color)

    def _create_button(self, value: str) -> CTkButton:
        new_button = CTkButton(self,
                               width=0,
                               height=self._current_height,
                               corner_radius=self._sb_corner_radius,
                               border_width=self._sb_border_width,
                               fg_color=self._sb_unselected_color,
                               border_color=self._sb_fg_color,
                               hover_color=self._sb_unselected_hover_color,
                               text_color=self._sb_text_color,
                               text_color_disabled=self._sb_text_color_disabled,
                               text=value,
                               font=self._font,
                               state=self._state,
                               command=lambda v=value: self.set(v, from_button_callback=True),
                               background_corner_colors=None,
                               round_width_to_even_numbers=False,
                               round_height_to_even_numbers=False)  # DrawEngine rendering option (so that theres no gap between buttons)

        return new_button

    @staticmethod
    def _check_unique_values(values: list[str]) -> None:
        """ raises exception if values are not unique """
        if len(values) != len(set(values)):
            raise ValueError("CTkSegmentedButton values are not unique")

    def _create_button_grid(self) -> None:
        number_of_columns, number_of_rows = self.grid_size()
        if self._orientation == "vertical":
            # remove minsize from every grid cell in the first column
            for n in range(number_of_rows):
                self.grid_rowconfigure(n, weight=1, minsize=0)
            self.grid_columnconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_rowconfigure(index, weight=1, minsize=self._current_height)
                self._buttons_dict[value].grid(row=index, column=0, sticky="nsew")
        else:
            # remove minsize from every grid cell in the first row
            for n in range(number_of_columns):
                self.grid_columnconfigure(n, weight=1, minsize=0)
            self.grid_rowconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_columnconfigure(index, weight=1, minsize=self._current_height)
                self._buttons_dict[value].grid(row=0, column=index, sticky="nsew")

    def _create_buttons_from_values(self) -> None:
        assert len(self._buttons_dict) == 0
        assert len(self._values) > 0

        for index, value in enumerate(self._values):
            self._buttons_dict[value] = self._create_button(value)
            self._configure_button_corners_for_index(index)

    def configure(self, **kwargs: Any) -> None:
        if "width" in kwargs:
            super().configure(width=kwargs.pop("width"))

        if "height" in kwargs:
            super().configure(height=kwargs.pop("height"))

        if "corner_radius" in kwargs:
            self._sb_corner_radius = kwargs.pop("corner_radius")
            super().configure(corner_radius=self._sb_corner_radius)
            for button in self._buttons_dict.values():
                button.configure(corner_radius=self._sb_corner_radius)

        if "border_width" in kwargs:
            self._sb_border_width = kwargs.pop("border_width")
            for button in self._buttons_dict.values():
                button.configure(border_width=self._sb_border_width)

        if "bg_color" in kwargs:
            super().configure(bg_color=kwargs.pop("bg_color"))
            if len(self._buttons_dict) > 0:
                self._configure_button_corners_for_index(0)
            if len(self._buttons_dict) > 1:
                max_index = len(self._buttons_dict) - 1
                self._configure_button_corners_for_index(max_index)

        if "fg_color" in kwargs:
            self._sb_fg_color = self._check_color_type(kwargs.pop("fg_color"))
            for index, button in enumerate(self._buttons_dict.values()):
                button.configure(border_color=self._sb_fg_color)
                self._configure_button_corners_for_index(index)

        if "selected_color" in kwargs:
            self._sb_selected_color = self._check_color_type(kwargs.pop("selected_color"))
            if self._current_value in self._buttons_dict:
                self._buttons_dict[self._current_value].configure(fg_color=self._sb_selected_color)

        if "selected_hover_color" in kwargs:
            self._sb_selected_hover_color = self._check_color_type(kwargs.pop("selected_hover_color"))
            if self._current_value in self._buttons_dict:
                self._buttons_dict[self._current_value].configure(hover_color=self._sb_selected_hover_color)

        if "unselected_color" in kwargs:
            self._sb_unselected_color = self._check_color_type(kwargs.pop("unselected_color"))
            for value, button in self._buttons_dict.items():
                if value != self._current_value:
                    button.configure(fg_color=self._sb_unselected_color)

        if "unselected_hover_color" in kwargs:
            self._sb_unselected_hover_color = self._check_color_type(kwargs.pop("unselected_hover_color"))
            for value, button in self._buttons_dict.items():
                if value != self._current_value:
                    button.configure(hover_color=self._sb_unselected_hover_color)

        if "text_color" in kwargs:
            self._sb_text_color = self._check_color_type(kwargs.pop("text_color"))
            for button in self._buttons_dict.values():
                button.configure(text_color=self._sb_text_color)

        if "text_color_disabled" in kwargs:
            self._sb_text_color_disabled = self._check_color_type(kwargs.pop("text_color_disabled"))
            for button in self._buttons_dict.values():
                button.configure(text_color_disabled=self._sb_text_color_disabled)

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            for i in range(len(self._buttons_dict)):
                self._configure_button_corners_for_index(i)

        if "font" in kwargs:
            self._font = kwargs.pop("font")
            for button in self._buttons_dict.values():
                button.configure(font=self._font)

        if "values" in kwargs:
            for button in self._buttons_dict.values():
                button.destroy()
            self._buttons_dict.clear()
            self._values = kwargs.pop("values")

            self._check_unique_values(self._values)

            if len(self._values) > 0:
                self._create_buttons_from_values()
                self._create_button_grid()

            if self._current_value in self._values:
                self._select_button_by_value(self._current_value)

        if "variable" in kwargs:
            if self._variable is not None:  # remove old callback
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)

        if "dynamic_resizing" in kwargs:
            self._dynamic_resizing = kwargs.pop("dynamic_resizing")
            if not self._dynamic_resizing:
                self.grid_propagate(False)
            else:
                self.grid_propagate(True)

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            for button in self._buttons_dict.values():
                button.configure(state=self._state)

        check_kwargs_empty(kwargs, raise_error=True)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "corner_radius":
            return self._sb_corner_radius
        elif attribute_name == "border_width":
            return self._sb_border_width

        elif attribute_name == "fg_color":
            return self._sb_fg_color
        elif attribute_name == "selected_color":
            return self._sb_selected_color
        elif attribute_name == "selected_hover_color":
            return self._sb_selected_hover_color
        elif attribute_name == "unselected_color":
            return self._sb_unselected_color
        elif attribute_name == "unselected_hover_color":
            return self._sb_unselected_hover_color
        elif attribute_name == "text_color":
            return self._sb_text_color
        elif attribute_name == "text_color_disabled":
            return self._sb_text_color_disabled
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors

        elif attribute_name == "font":
            return self._font
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "dynamic_resizing":
            return self._dynamic_resizing
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "orientation":
            return self._orientation

        else:
            return super().cget(attribute_name)

    def set(self, value: str, from_variable_callback: bool = False, from_button_callback: bool = False) -> None:
        if value == self._current_value:
            return
        elif value in self._buttons_dict:
            self._select_button_by_value(value)

            if self._variable is not None and not from_variable_callback:
                self._variable_callback_blocked = True
                self._variable.set(value)
                self._variable_callback_blocked = False
        else:
            if self._current_value in self._buttons_dict:
                self._unselect_button_by_value(self._current_value)
            self._current_value = value

            if self._variable is not None and not from_variable_callback:
                self._variable_callback_blocked = True
                self._variable.set(value)
                self._variable_callback_blocked = False

        if from_button_callback:
            if self._command is not None:
                self._command(self._current_value)

    def get(self) -> str:
        return self._current_value

    def index(self, value: str | None = None) -> int:
        """ returns index of selected value, raises ValueError if the value is missing
        if the parameter is provided, returns the associated index or raises ValueError if no value is found """
        if value is None:
            return self._values.index(self._current_value)
        else:
            return self._values.index(value)

    def insert(self, index: int, value: str) -> None:
        if value not in self._buttons_dict:
            if value != "":
                self._values.insert(index, value)
                self._buttons_dict[value] = self._create_button(value)

                self._configure_button_corners_for_index(index)
                if index > 0:
                    self._configure_button_corners_for_index(index - 1)
                if index < len(self._buttons_dict) - 1:
                    self._configure_button_corners_for_index(index + 1)

                self._create_button_grid()

                if value == self._current_value:
                    self._select_button_by_value(self._current_value)
            else:
                raise ValueError("CTkSegmentedButton can not insert value ''")
        else:
            raise ValueError(f"CTkSegmentedButton can not insert value '{value}', already part of the values")

    def len(self) -> int:
        """ returns the number of defined buttons """
        return len(self._values)

    def move(self, new_index: int, value: str) -> None:
        if 0 <= new_index < len(self._values):
            if value in self._buttons_dict:
                self.delete(value)
                self.insert(new_index, value)
            else:
                raise ValueError(f"CTkSegmentedButton has no value named '{value}'")
        else:
            raise ValueError(f"CTkSegmentedButton new_index {new_index} not in range of value list with len {len(self._values)}")

    def delete(self, value: str) -> None:
        if value in self._buttons_dict:
            self._buttons_dict[value].destroy()
            self._buttons_dict.pop(value)
            index_to_remove = self._get_index_by_value(value)
            self._values.pop(index_to_remove)

            # removed index was outer right element
            if index_to_remove == len(self._buttons_dict) and len(self._buttons_dict) > 0:
                self._configure_button_corners_for_index(index_to_remove - 1)

            # removed index was outer left element
            if index_to_remove == 0 and len(self._buttons_dict) > 0:
                self._configure_button_corners_for_index(0)

            #if index_to_remove <= len(self._buttons_dict) - 1:
            #    self._configure_button_corners_for_index(index_to_remove)

            self._create_button_grid()
        else:
            raise ValueError(f"CTkSegmentedButton does not contain value '{value}'")

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        raise NotImplementedError

    def unbind(self, sequence: str, funcid: None = None) -> None:
        raise NotImplementedError
