from __future__ import annotations

import tkinter
import copy
from functools import partial
from threading import Lock
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer
from .core_widget_classes.ctk_widget import CTkWidgetArgs
from .font.ctk_font import FontType
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame
from .ctk_button import CTkButton
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, first_value


class CTkSegmentedButtonThemedArgs(TypedDict, total=False, closed=True):
    orientation: Literal["horizontal", "vertical"]
    width: int
    height: int
    box_width: int   #minimum width for each segment
    box_height: int  #minimum height for each segment
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
    anchor: AnchorType

class CTkSegmentedButtonArgs(CTkSegmentedButtonThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    values: list[str]
    variable: tkinter.StringVar | None
    pre_command: Callable[[str], Literal["break"] | None] | None
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
                         corner_radius=0)

        # rendering options
        self._background_corner_colors: tuple[ColorType, ...] | None = kwargs.pop("background_corner_colors", None)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._pre_command: Callable[[str], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._values: list[str] = kwargs.pop("values", [])
        self._variable: tkinter.StringVar | None = kwargs.pop("variable", None)
        self._variable_callback_name: str | None = None
        self._block_value_propagation: Lock = Lock()
        self._buttons: dict[str, CTkButton] = {}
        self._selected_value: str = ""

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        if len(self._values) > 0:
            self._create_buttons_from_values()
            self._update_buttons_geometry()

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback()

    def _variable_callback(self, *_: str) -> None:
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self.set(self._variable.get())

    def _configure_corners_for_index(self, index: int) -> None:
        button = self._buttons[self._values[index]]

        fg_color = self._theme_sb_info["fg_color"]
        if self._background_corner_colors is None:
            corner_colors = (self._bg_color, self._bg_color, self._bg_color, self._bg_color)
        else:
            corner_colors = self._background_corner_colors

        #just one button
        if len(self._values) == 1:
            button.configure(background_corner_colors=corner_colors)

        #first button (left/top)
        elif index == 0:
            if self._theme_sb_info["orientation"] == "vertical":
                button.configure(background_corner_colors=(corner_colors[0], corner_colors[1], fg_color, fg_color))
            else:
                button.configure(background_corner_colors=(corner_colors[0], fg_color, fg_color, corner_colors[3]))

        #last button (right/bottom)
        elif index == len(self._values) - 1:
            if self._theme_sb_info["orientation"] == "vertical":
                button.configure(background_corner_colors=(fg_color, fg_color, corner_colors[2], corner_colors[3]))
            else:
                button.configure(background_corner_colors=(fg_color, corner_colors[1], corner_colors[2], fg_color))

        #button in the middle
        else:
            button.configure(background_corner_colors=(fg_color, fg_color, fg_color, fg_color))

    def _select_button_by_value(self, value: str) -> None:
        if self._selected_value in self._buttons:
            self._buttons[self._selected_value].configure(fg_color=self._theme_sb_info["unselected_color"],
                                                          hover_color=self._theme_sb_info["unselected_hover_color"])
        self._selected_value = value
        if value in self._buttons:
            self._buttons[value].configure(fg_color=self._theme_sb_info["selected_color"],
                                           hover_color=self._theme_sb_info["selected_hover_color"])

    def _create_button(self, value: str) -> CTkButton:
        new_button = CTkButton(self,
                               width=self._theme_sb_info["box_width"],
                               height=self._theme_sb_info["box_height"],
                               corner_radius=self._theme_sb_info["corner_radius"],
                               border_width=self._theme_sb_info["border_width"],
                               fg_color=self._theme_sb_info["unselected_color"],
                               border_color=self._theme_sb_info["fg_color"],
                               hover_color=self._theme_sb_info["unselected_hover_color"],
                               text_color=self._theme_sb_info["text_color"],
                               text_color_disabled=self._theme_sb_info["text_color_disabled"],
                               anchor=self._theme_sb_info["anchor"],
                               text=value,
                               font=self._theme_sb_info["font"],
                               state=self._state,
                               command=partial(self.invoke, value))
        return new_button

    def _create_buttons_from_values(self) -> None:
        if len(self._values) != len(set(self._values)):
            raise ValueError("CTkSegmentedButton values are not unique")

        for button in self._buttons.values():
            button.destroy()
        self._buttons.clear()
        for index, value in enumerate(self._values):
            self._buttons[value] = self._create_button(value)
            self._configure_corners_for_index(index)

    def _update_buttons_geometry(self) -> None:
        #clear previous settings
        n_cols, n_rows = self.grid_size()
        self.grid_columnconfigure(tuple(range(n_cols + 1)), weight=0)
        self.grid_rowconfigure(tuple(range(n_rows + 1)), weight=0)

        if self._theme_sb_info["orientation"] == "vertical":
            self.grid_columnconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_rowconfigure(index, weight=1)
                self._buttons[value].grid(row=index, column=0, sticky="nsew")
        else:
            self.grid_rowconfigure(0, weight=1)

            for index, value in enumerate(self._values):
                self.grid_columnconfigure(index, weight=1)
                self._buttons[value].grid(row=0, column=index, sticky="nsew")

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        super().destroy()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkSegmentedButtonArgs]) -> None:
        require_corners = False
        require_geometry = False
        button_kwargs = {}

        if "orientation" in kwargs:
            self._theme_sb_info["orientation"] = kwargs.pop("orientation")
            require_corners = True
            require_geometry = True

        if "box_width" in kwargs:
            self._theme_sb_info["box_width"] = kwargs.pop("box_width")
            button_kwargs["width"] = self._theme_sb_info["box_width"]

        if "box_height" in kwargs:
            self._theme_sb_info["box_height"] = kwargs.pop("box_height")
            button_kwargs["height"] = self._theme_sb_info["box_height"]

        if "corner_radius" in kwargs:
            self._theme_sb_info["corner_radius"] = kwargs.pop("corner_radius")
            button_kwargs["corner_radius"] = self._theme_sb_info["corner_radius"]

        if "border_width" in kwargs:
            self._theme_sb_info["border_width"] = kwargs.pop("border_width")
            button_kwargs["border_width"] = self._theme_sb_info["border_width"]

        if "bg_color" in kwargs:
            require_corners = True

        if "fg_color" in kwargs:
            self._theme_sb_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            button_kwargs["border_color"] = self._theme_sb_info["fg_color"]
            require_corners = True

        if "selected_color" in kwargs:
            self._theme_sb_info["selected_color"] = self._check_color_type(kwargs.pop("selected_color"))
            if self._selected_value in self._buttons:
                self._buttons[self._selected_value].configure(fg_color=self._theme_sb_info["selected_color"])

        if "selected_hover_color" in kwargs:
            self._theme_sb_info["selected_hover_color"] = self._check_color_type(kwargs.pop("selected_hover_color"))
            if self._selected_value in self._buttons:
                self._buttons[self._selected_value].configure(hover_color=self._theme_sb_info["selected_hover_color"])

        if "unselected_color" in kwargs:
            self._theme_sb_info["unselected_color"] = self._check_color_type(kwargs.pop("unselected_color"))
            for value, button in self._buttons.items():
                if value != self._selected_value:
                    button.configure(fg_color=self._theme_sb_info["unselected_color"])

        if "unselected_hover_color" in kwargs:
            self._theme_sb_info["unselected_hover_color"] = self._check_color_type(kwargs.pop("unselected_hover_color"))
            for value, button in self._buttons.items():
                if value != self._selected_value:
                    button.configure(hover_color=self._theme_sb_info["unselected_hover_color"])

        if "text_color" in kwargs:
            self._theme_sb_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            button_kwargs["text_color"] = self._theme_sb_info["text_color"]

        if "text_color_disabled" in kwargs:
            self._theme_sb_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            button_kwargs["text_color_disabled"] = self._theme_sb_info["text_color_disabled"]

        if "font" in kwargs:
            button_kwargs["font"] = kwargs.pop("font")

        if "anchor" in kwargs:
            self._theme_sb_info["anchor"] = kwargs.pop("anchor")
            button_kwargs["anchor"] = self._theme_sb_info["anchor"]

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            button_kwargs["state"] = self._state

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._create_buttons_from_values()
            require_geometry = True
            if self._selected_value in self._values:
                self._select_button_by_value(self._selected_value)

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._variable_callback()

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_corners = True

        for button in self._buttons.values():
            button.configure(**button_kwargs)
        super().configure(require_redraw=require_redraw, **kwargs)
        if require_corners:
            for n in range(len(self._buttons)):
                self._configure_corners_for_index(n)
        if require_geometry:
            self._update_buttons_geometry()

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name == "font":
            return first_value(self._buttons).cget("font")
        elif attribute_name in self._theme_sb_info and attribute_name not in CTkWidgetArgs.__annotations__:
            return self._theme_sb_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def button(self, name: str) -> CTkButton:
        """ Returns reference to the button with given name. """
        if name in self._buttons:
            return self._buttons[name]
        else:
            raise ValueError(f"CTkSegmentedButton has no value '{name}'")

    def set(self, value: str) -> None:
        """ Changes the selected value to the desired one, regardless of the widget's state and admissible values. """
        self._select_button_by_value(value)

        if self._variable is not None and not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self._variable.set(value)

    def invoke(self, value: str) -> None:
        """ Changes the active button following the provided value.\n
        Can be called to simulate the user who clicks on a specific button. """
        if self._state == tkinter.NORMAL and value != self._selected_value:
            retval = "" if self._pre_command is None else self._pre_command(value)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                self.set(value)

                if self._command is not None:
                    self._command(value)

    def get(self, index: int | None = None) -> str:
        """ Returns the current value.\n
        If an index is provided, returns the value in that position. """
        if index is None:
            return self._selected_value
        else:
            return self._values[index]

    def index(self, value: str | None = None) -> int:
        """ Returns index of selected value, raises ValueError if the value is missing.\n
        If the parameter is provided, returns the associated index or raises ValueError if the value is not found. """
        if value is None:
            value = self._selected_value
        return self._values.index(value)

    def len(self) -> int:
        """ Returns the number of defined buttons. """
        return len(self._values)

    def insert(self, index: int, value: str) -> None:
        """ Creates new button with given value at position index. """
        if value == "":
            raise ValueError("CTkSegmentedButton can not insert value ''")
        if value in self._buttons:
            raise ValueError(f"CTkSegmentedButton can not insert value '{value}', already part of the values")

        self._values.insert(index, value)
        self._buttons[value] = self._create_button(value)

        self._configure_corners_for_index(index)
        if index > 0:
            self._configure_corners_for_index(index - 1)
        if index < len(self._buttons) - 1:
            self._configure_corners_for_index(index + 1)

        self._update_buttons_geometry()

        if value == self._selected_value:
            self._select_button_by_value(self._selected_value)

    def add(self, value: str) -> None:
        """ Appends new button with given value. """
        self.insert(len(self._buttons), value)

    def delete(self, value: str) -> None:
        """ Deletes button by value. """
        if value not in self._buttons:
            raise ValueError(f"CTkSegmentedButton does not contain value '{value}'")

        was_first = value == self._values[0]
        was_last = value == self._values[-1]
        self._buttons.pop(value).destroy()
        self._values.remove(value)

        #there are still buttons
        if len(self._buttons) > 0:
            # removed button was first element (left or top)
            if was_first:
                self._configure_corners_for_index(0)
            # removed button was last element (right or bottom)
            if was_last == len(self._buttons):
                self._configure_corners_for_index(len(self._values) - 1)

        self._update_buttons_geometry()

    def move(self, new_index: int, value: str) -> None:
        if not 0 <= new_index < len(self._values):
            raise ValueError(f"CTkSegmentedButton new_index {new_index} not in range of value list with len {len(self._values)}")
        if value not in self._buttons:
            raise ValueError(f"CTkSegmentedButton has no value named '{value}'")

        self.delete(value)
        self.insert(new_index, value)
