from __future__ import annotations

import tkinter
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_widget_classes.dropdown_menu import DropdownMenu, DropdownMenuArgs
from .core_rendering import CTkCanvas, BorderedRoundedRect, Arrow
from .font import CTkFont, FontType
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor


class CTkOptionMenuThemedArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_spacing: int
    bg_color: TransparentColorType
    fg_color: ColorType
    button_color: ColorType
    button_hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    hover: bool
    font: FontType
    anchor: AnchorType
    compound: Literal["left", "right"]
    dropdown: DropdownMenuArgs

class CTkOptionMenuArgs(CTkOptionMenuThemedArgs, total=False):
    state: Literal["normal", "disabled"]
    values: list[str] | None
    variable: tkinter.StringVar | None
    command: Callable[[str], None] | None


class CTkOptionMenu(CTkWidget):
    """
    Optionmenu with rounded corners, dropdown menu, variable support, command.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkOptionMenuArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkOptionMenuThemedArgs.__annotations__)
        self._theme_info: CTkOptionMenuThemedArgs = ThemeManager.get_info("CTkOptionMenu", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", "normal")
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._variable: tkinter.StringVar | None = kwargs.pop("variable", None)
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None
        self._applied_button_width: int = -1
        self._values: list[str] = kwargs.pop("values", [])
        self._current_value: str = "" if len(self._values) == 0 else self._values[0]

        self._dropdown_menu = DropdownMenu(master=self,
                                           values=self._values,
                                           command=self._dropdown_callback,
                                           **self._theme_info["dropdown"])
        self._close_on_next_click: bool = False

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._arrow = Arrow(self._canvas, events_transparent=True)
        self._bind_targets.append(self._canvas)

        self._text_label = tkinter.Label(master=self,
                                         font=self._apply_font_scaling(self._font),
                                         anchor=self._theme_info["anchor"],
                                         padx=0,
                                         pady=0,
                                         borderwidth=1,
                                         text=self._current_value)
        self._bind_targets.append(self._text_label)
        self._focus_target = self._text_label

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_bindings()
        self._set_cursor()
        self._draw(force_colors_update=True)

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._current_value = self._variable.get()
            self._text_label.configure(text=self._current_value)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self.invoke)
            self._text_label.bind("<Button-1>", self.invoke)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        # change label font size and canvas sizes
        self._text_label.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _set_cursor(self) -> None:
        cursor = get_proper_cursor("normal" if self._state != tkinter.NORMAL else "clickable")
        if cursor is not None:
            self.configure(cursor=cursor)

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        compound = self._theme_info["compound"]
        not_compound = "left" if compound == "right" else "right"
        left_section_width = self._current_width - self._current_height if compound == "right" else self._current_height

        requires_recoloring_1 = self._rounded_rect.update(self._current_width,
                                                          self._current_height,
                                                          self._apply_scaling(self._theme_info["corner_radius"]),
                                                          0,
                                                          left_section_width=left_section_width)

        if compound == "right":
            button_middle_point = (self._rounded_rect.info.get("left_section_width", 0) + self._current_width) / 2
        else:
            button_middle_point = self._rounded_rect.info.get("left_section_width", 0) / 2
        requires_recoloring_2 = self._arrow.update(button_middle_point,
                                                   self._current_height / 2,
                                                   self._current_height / 3,
                                                   180)

        if (self._rounded_rect.info["spacings_changed"] or
            abs(self._applied_button_width - self._rounded_rect.info.get(f"{compound}_section_width", 0)) > 1):
            self._update_geometry()

        if force_colors_update or requires_recoloring_1 or requires_recoloring_2:
            self._rounded_rect.raise_()
            self._arrow.raise_()

            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
            button_color = self._apply_appearance_mode(self._theme_info["button_color"])
            if self._state != tkinter.NORMAL:
                text_color = self._apply_appearance_mode(self._theme_info["text_color_disabled"])
            else:
                text_color = self._apply_appearance_mode(self._theme_info["text_color"])

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(fg_color, not_compound)
            self._rounded_rect.set_main_color(button_color, compound)
            self._arrow.set_color(text_color)
            self._text_label.configure(fg=text_color, bg=fg_color)

        self._canvas.update_idletasks()

    def _update_geometry(self) -> None:
        compound = self._theme_info["compound"]
        self._applied_button_width = self._rounded_rect.info.get(f"{compound}_section_width", 0)

        spacing = self._rounded_rect.info.get("inscribed_spacing", 0)
        border_spacing = self._apply_scaling(self._theme_info["border_spacing"])
        padx=(spacing + border_spacing,
              self._applied_button_width + border_spacing)

        self._text_label.grid(row=0, column=0, sticky="nsew",
                              padx=padx if compound == "right" else padx[::-1],
                              pady=spacing)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkOptionMenuArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "button_color" in kwargs:
            self._theme_info["button_color"] = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._theme_info["button_hover_color"] = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._dropdown_menu.configure(values=self._values)

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._current_value = self._variable.get()
                self._text_label.configure(text=self._current_value)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._text_label.configure(anchor=self._theme_info["anchor"])

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            self._applied_button_width = -1
            require_redraw = True

        if "dropdown" in kwargs:
            self._dropdown_menu.configure(**kwargs.pop("dropdown"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("dropdown_"):
            return self._dropdown_menu.cget(attribute_name.removeprefix("dropdown_"))
        else:
            return super().cget(attribute_name)

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._close_on_next_click = self._dropdown_menu.is_open()
        if self._theme_info["hover"] and self._state == tkinter.NORMAL and len(self._values) > 0:
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]),
                                              self._theme_info["compound"])

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._rounded_rect.set_main_color(self._apply_appearance_mode(self._theme_info["button_color"]),
                                          self._theme_info["compound"])

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    def _dropdown_callback(self, value: str) -> None:
        self.set(value)
        if self._command is not None:
            self._command(self._current_value)

    def set(self, value: str, from_variable_callback: bool = False) -> None:
        """ Changes the content to the desired value, regardless of the widget's state and admissible values. """
        self._current_value = value
        self._text_label.configure(text=self._current_value)

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._current_value)
            self._variable_callback_blocked = False

    def get(self, index: int | None = None) -> str:
        """ Returns the current selected value.\n
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

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """ Toggles the visibility status of the dropdown menu if the widget is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        if self._close_on_next_click:
            self._dropdown_menu.close()
            self._close_on_next_click = False
        elif self._state == tkinter.NORMAL and len(self._values) > 0:
            self._dropdown_menu.open(self.winfo_rootx(),
                                     self.winfo_rooty() + self._current_height)
            self._close_on_next_click = True
