from __future__ import annotations

import tkinter
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget, EntryLike
from .core_widget_classes.dropdown_menu import DropdownMenu, DropdownMenuArgs
from .core_rendering import CTkCanvas, BorderedRoundedRect, Arrow
from .font import CTkFont, FontType
from .theme import ColorType, TransparentColorType, ThemeManager
from .ctk_entry import ValidTkEntryArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor


class CTkComboBoxThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: TransparentColorType
    fg_color: ColorType
    border_color: ColorType
    button_color: ColorType
    button_hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    placeholder_text_color: ColorType
    placeholder_text: str  #not used in "type" mode or if a variable is provided
    hover: bool
    font: FontType
    justify: Literal["left", "center", "right"]
    compound: Literal["left", "right"]
    dropdown: DropdownMenuArgs

class CTkComboBoxArgs(CTkComboBoxThemedArgs, ValidTkEntryArgs, total=False, closed=True):
    mode: Literal["replace", "toggle", "type", "command"]
    state: Literal["normal", "disabled", "readonly"]
    values: list[str]
    separator: str  #used only in "toggle" mode
    variable: tkinter.StringVar | None
    command: Callable[[str], None] | None


class CTkComboBox(CTkWidget, EntryLike):
    """
    Combobox with dropdown menu, rounded corners, border, variable support.
    It behaves differently based on the mode:
    - "replace": content is replaced when a value is selected from the Dropdown Menu;
    - "toggle": selected value is added if missing or removed if already present;
    - "type": values in the Dropdown menu are used as placeholder_text to indicate a different usage of the content;
    - "command": just the command function is invoked.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkComboBoxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkComboBoxThemedArgs.__annotations__)
        self._theme_info: CTkComboBoxThemedArgs = ThemeManager.get_info("CTkComboBox", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=self._theme_info["width"],
                           height=self._theme_info["height"])

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # functionality
        self._mode: Literal["replace", "toggle", "type", "command"] = kwargs.pop("mode", "replace")
        self._state: Literal["normal", "disabled", "readonly"] = kwargs.pop("state", tkinter.NORMAL)
        self._values: list[str] = kwargs.pop("values", [])
        self._separator: str = kwargs.pop("separator", " ")
        self._type: str = self._values[0] if self._mode == "type" and self._values else ""
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._variable: tkinter.StringVar | None = kwargs.pop("variable", None)
        self._applied_button_width: int = -1
        self._close_on_next_click: bool = False
        self._placeholder_text_active: bool = False
        self._has_focus: bool = False

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

        self._dropdown_menu = DropdownMenu(master=self,
                                           values=self._values,
                                           command=self._dropdown_callback,
                                           **self._theme_info["dropdown"])

        EntryLike.__init__(self,
                           master=self,
                           state=self._state,
                           width=1,
                           bd=0,
                           justify=self._theme_info["justify"],
                           highlightthickness=0,
                           font=self._apply_font_scaling(self._font),
                           **pop_from_dict_by_iterable(kwargs, ValidTkEntryArgs.__annotations__))
        self._bind_targets.append(self._entry)
        self._focus_target = self._entry

        if self._variable is not None:
            self._entry.configure(textvariable=self._variable)
        elif self._mode == "replace" and self._theme_info["placeholder_text"] == "":
            # insert default value
            if len(self._values) > 0:
                self._set_regardless(self._values[0])

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._activate_placeholder()
        self._create_bindings()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._rounded_rect.bind("<Enter>", self._on_enter, section=self._theme_info["compound"])
        if sequence is None or sequence == "<Leave>":
            self._rounded_rect.bind("<Leave>", self._on_leave, section=self._theme_info["compound"])
        if sequence is None or sequence == "<Button-1>":
            self._rounded_rect.bind("<Button-1>", self.invoke, section=self._theme_info["compound"])
        if sequence is None or sequence == "<FocusIn>":
            self._entry.bind("<FocusIn>", self._on_focus_in)
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", self._on_focus_out)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        # change entry font size and canvas sizes
        self._entry.configure(font=self._apply_font_scaling(self._font))
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
        self._entry.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        compound = self._theme_info["compound"]
        not_compound = "left" if compound == "right" else "right"
        left_section_width = self._current_width - self._current_height if compound == "right" else self._current_height

        requires_recoloring_1 = self._rounded_rect.update(self._current_width,
                                                          self._current_height,
                                                          self._apply_scaling(self._theme_info["corner_radius"]),
                                                          self._apply_scaling(self._theme_info["border_width"]),
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
            border_color = self._apply_appearance_mode(self._theme_info["border_color"])
            button_color = self._apply_appearance_mode(self._theme_info["button_color"])
            text_color = self._apply_appearance_mode(self._theme_info["text_color"])
            text_color_disabled = self._apply_appearance_mode(self._theme_info["text_color_disabled"])

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(fg_color, not_compound)
            self._rounded_rect.set_border_color(border_color, not_compound)
            self._rounded_rect.set_main_color(button_color, compound)
            self._rounded_rect.set_border_color(button_color, compound)
            self._arrow.set_color(text_color_disabled if self._state == tkinter.DISABLED else text_color)

            if self._placeholder_text_active:
                text_color = self._apply_appearance_mode(self._theme_info["placeholder_text_color"])

            self._entry.configure(bg=fg_color,
                                  fg=text_color,
                                  readonlybackground=fg_color,
                                  disabledbackground=fg_color,
                                  disabledforeground=text_color_disabled,
                                  highlightcolor=fg_color,
                                  insertbackground=text_color)

    def _update_geometry(self) -> None:
        compound = self._theme_info["compound"]
        self._applied_button_width = self._rounded_rect.info.get(f"{compound}_section_width", 0)

        spacing = self._rounded_rect.info.get("inscribed_spacing", 0)
        border_spacing = self._apply_scaling(self._theme_info["border_spacing"])
        padx = (spacing + border_spacing,
                self._applied_button_width + border_spacing)

        self._entry.grid(row=0, column=0, sticky="ew",
                         padx=padx if compound == "right" else padx[::-1],
                         pady=spacing)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkComboBoxArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
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

        if "placeholder_text_color" in kwargs:
            self._theme_info["placeholder_text_color"] = self._check_color_type(kwargs.pop("placeholder_text_color"))
            require_redraw = True

        if "placeholder_text" in kwargs:
            self._theme_info["placeholder_text"] = kwargs.pop("placeholder_text")
            if self._mode != "type" and self._placeholder_text_active:
                self._set_regardless(self._theme_info["placeholder_text"])

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "justify" in kwargs:
            self._theme_info["justify"] = kwargs.pop("justify")
            self._entry.configure(justify=self._theme_info["justify"])

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            self._create_bindings()
            self._applied_button_width = -1
            require_redraw = True

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._dropdown_menu.configure(values=self._values)

        if "separator" in kwargs:
            string = self.get()
            values = string.split(self._separator) if string else []
            self._separator = kwargs.pop("separator")
            if self._mode == "toggle":
                self.set(self._separator.join(values))

        if "mode" in kwargs:
            self._mode = kwargs.pop("mode")
            if self._mode == "type" and self._values:
                self._type = self._values[0]
                if self._placeholder_text_active:
                    self._set_regardless(self._type)
            else:
                self._type = ""

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._entry.configure(state=self._state)
            require_redraw = True

        if "variable" in kwargs:
            self._variable = kwargs.pop("variable")
            self._entry.configure(textvariable=self._variable)
            self._deactivate_placeholder()
            self._activate_placeholder()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "dropdown" in kwargs:
            self._dropdown_menu.configure(**kwargs.pop("dropdown"))

        self._entry.configure(**pop_from_dict_by_iterable(kwargs, ValidTkEntryArgs.__annotations__))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "mode":
            return self._mode
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "separator":
            return self._separator
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name in ValidTkEntryArgs.__annotations__:
            return self._entry.cget(attribute_name)
        elif attribute_name.startswith("dropdown_"):
            self._dropdown_menu.cget(attribute_name.removeprefix("dropdown_"))
        else:
            return super().cget(attribute_name)

    def _activate_placeholder(self) -> None:
        if self._entry.get() == "" and self._variable is None and not self._has_focus:
            self._placeholder_text_active = True

            text_color = self._apply_appearance_mode(self._theme_info["placeholder_text_color"])
            self._entry.configure(fg=text_color, disabledforeground=text_color)
            self._set_regardless(self._type if self._mode == "type" else self._theme_info["placeholder_text"])

    def _deactivate_placeholder(self) -> None:
        if self._placeholder_text_active:
            self._placeholder_text_active = False

            self._entry.configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                                  disabledforeground=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
            self._set_regardless("")

    def _on_focus_in(self, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            self._has_focus = True
            self._deactivate_placeholder()

    def _on_focus_out(self, _: tkinter.Event | None = None) -> None:
        self._has_focus = False
        self._activate_placeholder()

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._close_on_next_click = self._dropdown_menu.is_open()
        if self._state != tkinter.DISABLED and len(self._values) > 0:
            cursor = get_proper_cursor("clickable")
            if cursor is not None:
                self._canvas.configure(cursor=cursor)

            if self._theme_info["hover"]:
                # set color of button parts to hover color
                color = self._apply_appearance_mode(self._theme_info["button_hover_color"])
                self._rounded_rect.set_main_color(color, self._theme_info["compound"])
                self._rounded_rect.set_border_color(color, self._theme_info["compound"])

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        cursor = get_proper_cursor("normal")
        if cursor is not None:
            self._canvas.configure(cursor=cursor)

        # restore color of button parts
        color = self._apply_appearance_mode(self._theme_info["button_color"])
        self._rounded_rect.set_main_color(color, self._theme_info["compound"])
        self._rounded_rect.set_border_color(color, self._theme_info["compound"])

    def _dropdown_callback(self, value: str) -> None:
        if self._mode == "replace":
            self.set(value)

        elif self._mode == "toggle":
            string = self.get()
            values = string.split(self._separator) if string else []
            try:
                values.remove(value)
            except ValueError:
                values.append(value)
            self.set(self._separator.join(values))

        elif self._mode == "type":
            self._type = value
            if self._placeholder_text_active:
                self._set_regardless(value)

        #in command mode, just invoke the function
        if self._command is not None:
            self._command(value)

        #in toggle mode, re-open the menu to allow the user
        # to click multiple values consecutively
        if self._mode == "toggle":
            self._close_on_next_click = False
            self.invoke()

    def delete(self, first_index: str | int, last_index: str | int | None = None) -> None:
        self._entry.delete(first_index, last_index)
        self._activate_placeholder()

    def insert(self, index: str | int, string: str) -> None:
        self._deactivate_placeholder()
        return self._entry.insert(index, string)

    def set(self, value: str) -> None:
        """ Changes the content to the desired value, regardless of the widget's state and admissible values. """
        self._deactivate_placeholder()
        self._set_regardless(value)
        if value == "":
            self._activate_placeholder()

    def get(self, index: int | None = None) -> str:
        """ Returns the current value.\n
        If an index is provided, returns the value in that position. """
        if index is not None:
            return self._values[index]
        elif self._placeholder_text_active:
            return ""
        else:
            return self._entry.get()

    def set_type(self, value: str) -> None:
        """ For 'type' mode, changes the active type to the desired value,
        regardless of the widget's state and admissible values. """
        if self._mode == "type":
            self._type = value
            if self._placeholder_text_active:
                self._set_regardless(value)

    def get_type(self) -> str:
        """ For 'type' mode, returns the current type. """
        if self._mode == "type":
            return self._type
        else:
            return ""

    def index(self, value: str | None = None) -> int:
        """ Returns index of selected value, raises ValueError if the value is missing.\n
        If the parameter is provided, returns the associated index or raises ValueError if no value is found. """
        if value is None:
            value = self.get()
        return self._values.index(value)

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """ Toggles the visibility status of the dropdown menu if the widget is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        if self._close_on_next_click:
            self._dropdown_menu.close()
            self._close_on_next_click = False
        elif self._state != tkinter.DISABLED and len(self._values) > 0:
            self._dropdown_menu.open(self.winfo_rootx(),
                                     self.winfo_rooty() + self._current_height)
            self._close_on_next_click = True
