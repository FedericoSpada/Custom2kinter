from __future__ import annotations

import tkinter
import copy
from threading import Lock
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkScrollable, CTkWidget, EntryLike
from .core_rendering import CTkCanvas, BorderedRoundedRect, Arrow
from .font import CTkFont, FontType
from .theme import ColorType, TransparentColorType, ThemeManager
from .ctk_entry import ValidTkEntryArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor


class CTkSpinBoxThemedArgs(TypedDict, total=False, closed=True):
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
    hover: bool
    font: FontType
    justify: Literal["left", "center", "right"]
    compound: Literal["left", "right"]

class CTkSpinBoxArgs(CTkSpinBoxThemedArgs, ValidTkEntryArgs, total=False, closed=True):
    state: Literal["normal", "disabled", "readonly"]
    from_: int | float | None  #used as limit for the index if values is provided
    to: int | float | None     #used as limit for the index if values is provided
    values: list[int | float | str] | None
    format: str  #the syntax is explained here: https://docs.python.org/3/library/string.html#formatstrings
    buttonincrement: int | float
    scrollincrement: int | float
    variable: tkinter.IntVar | tkinter.DoubleVar | tkinter.StringVar | None
    command: Callable[[int | float | str], None] | None


class CTkSpinBox(CTkWidget, CTkScrollable, EntryLike):
    """
    SpinBox with up/down buttons, rounded corners, border, variable support.
    For detailed information check out the documentation.
    """

    repeated_increment_first_time: int = 400  # [ms], if negative, the continuous update with the button kept pressed is disabled
    repeated_increment_last_time: int = 20    # [ms]
    repeated_increment_factor: float = 0.8

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkSpinBoxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkSpinBoxThemedArgs.__annotations__)
        self._theme_info: CTkSpinBoxThemedArgs = ThemeManager.get_info("CTkSpinBox", theme_key, **theme_args)

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
        CTkScrollable.__init__(self, self.winfo_toplevel())

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # functionality
        self._state: Literal["normal", "disabled", "readonly"] = kwargs.pop("state", tkinter.NORMAL)
        self._from: int | float | None = kwargs.pop("from_", None)
        self._to: int | float | None = kwargs.pop("to", None)
        self._values: list[int | float | str] | None = kwargs.pop("values", None)
        self._buttonincrement: int | float
        self._scrollincrement: int | float
        self._command: Callable[[int | float | str], None] | None = kwargs.pop("command", None)
        self._variable: tkinter.IntVar | tkinter.DoubleVar | tkinter.StringVar | None = kwargs.pop("variable", None)
        self._support_variable: tkinter.StringVar | None = None
        self._variable_callback_name: str | None = None
        self._block_value_propagation: Lock = Lock()
        self._applied_button_width: int = -1
        self._after_id: str | None = None
        self._after_time: int = self.repeated_increment_first_time

        format_ = kwargs.pop("format", "{}")
        if "{}" in format_ and (self._from is not None or self._to is not None):
            format_ = format_.replace("{}", "{:f}" if isinstance(self._from, float) or isinstance(self._to, float) else "{:d}")
        self._format: str = format_

        buttonincrement = kwargs.pop("buttonincrement", None)
        scrollincrement = kwargs.pop("scrollincrement", None)
        if buttonincrement is None and scrollincrement is None:
            self._buttonincrement = 1
            self._scrollincrement = 1
        else:
            self._buttonincrement = buttonincrement if buttonincrement is not None else scrollincrement
            self._scrollincrement = scrollincrement if scrollincrement is not None else buttonincrement

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._arrow_up = Arrow(self._canvas, events_transparent=True)
        self._arrow_down = Arrow(self._canvas, events_transparent=True)

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

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._update_variable()
        self._create_bindings()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        compound = self._theme_info["compound"]
        if sequence is None or sequence == "<Enter>":
            self._rounded_rect.bind("<Enter>", lambda _: self._on_enter("top")   , section=f"top_{compound}")
            self._rounded_rect.bind("<Enter>", lambda _: self._on_enter("bottom"), section=f"bottom_{compound}")
        if sequence is None or sequence == "<Leave>":
            self._rounded_rect.bind("<Leave>", self._on_leave, section=compound)
        if sequence is None or sequence == "<Button-1>":
            self._rounded_rect.bind("<Button-1>", lambda _: self._clicked("top")   , section=f"top_{compound}")
            self._rounded_rect.bind("<Button-1>", lambda _: self._clicked("bottom"), section=f"bottom_{compound}")
        if sequence is None or sequence == "<ButtonRelease-1>":
            self._rounded_rect.bind("<ButtonRelease-1>", self._on_release, section=compound)
        #to force format if the user edits manually
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", lambda _: self.invoke("none"))
        if sequence is None or sequence == "<Return>":
            self._entry.bind("<Return>", lambda _: self.invoke("none"))

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
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

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
                                                          left_section_width=left_section_width,
                                                          top_section_height=self._current_height / 2)

        if compound == "right":
            button_middle_point = (self._rounded_rect.info.get("left_section_width", 0) + self._current_width) / 2
        else:
            button_middle_point = self._rounded_rect.info.get("left_section_width", 0) / 2
        requires_recoloring_2 = self._arrow_up.update(button_middle_point,
                                                      self._current_height * 0.33,
                                                      self._current_height / 3.5,
                                                      0)
        requires_recoloring_3 = self._arrow_down.update(button_middle_point,
                                                        self._current_height * 0.67,
                                                        self._current_height / 3.5,
                                                        180)

        if (self._rounded_rect.info["spacings_changed"] or
            abs(self._applied_button_width - self._rounded_rect.info.get(f"{compound}_section_width", 0)) > 1):
            self._update_geometry()

        if force_colors_update or requires_recoloring_1 or requires_recoloring_2 or requires_recoloring_3:
            self._rounded_rect.raise_()
            self._arrow_down.raise_()
            self._arrow_up.raise_()

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
            self._arrow_down.set_color(text_color_disabled if self._state == tkinter.DISABLED else text_color)
            self._arrow_up.set_color(text_color_disabled if self._state == tkinter.DISABLED else text_color)

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

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkSpinBoxArgs]) -> None:
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

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._entry.configure(state=self._state)
            require_redraw = True

        if "from_" in kwargs:
            self._from = kwargs.pop("from_")

        if "to" in kwargs:
            self._to = kwargs.pop("to")

        if "values" in kwargs:
            self._values = kwargs.pop("values")

        if "format" in kwargs:
            value = self.get()
            self._format = kwargs.pop("format")
            self.set(value)

        if "buttonincrement" in kwargs:
            self._buttonincrement = kwargs.pop("buttonincrement")

        if "scrollincrement" in kwargs:
            self._scrollincrement = kwargs.pop("scrollincrement")

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            self._update_variable()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        self._entry.configure(**pop_from_dict_by_iterable(kwargs, ValidTkEntryArgs.__annotations__))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "from_":
            return self._from
        elif attribute_name == "to":
            return self._to
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "format":
            return self._format
        elif attribute_name == "buttonincrement":
            return self._buttonincrement
        elif attribute_name == "scrollincrement":
            return self._scrollincrement
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name in ValidTkEntryArgs.__annotations__:
            return self._entry.cget(attribute_name)
        else:
            return super().cget(attribute_name)

    def _on_enter(self, button: Literal["top", "bottom"]) -> None:
        if self._state != tkinter.DISABLED:
            cursor = get_proper_cursor("clickable")
            if cursor is not None:
                self._canvas.configure(cursor=cursor)

            if self._theme_info["hover"]:
                # set color of button parts to hover color
                color = self._apply_appearance_mode(self._theme_info["button_hover_color"])
                section = f"{button}_{self._theme_info['compound']}"
                self._rounded_rect.set_main_color(color, section)
                self._rounded_rect.set_border_color(color, section)

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        cursor = get_proper_cursor("normal")
        if cursor is not None:
            self._canvas.configure(cursor=cursor)

        # restore color of button parts
        color = self._apply_appearance_mode(self._theme_info["button_color"])
        self._rounded_rect.set_main_color(color, self._theme_info["compound"])
        self._rounded_rect.set_border_color(color, self._theme_info["compound"])

    def _clicked(self, direction: Literal["top", "bottom"]) -> None:
        self.invoke(direction, "button")

        if self._after_time >= 0:
            self._after_id = self.after(self._after_time, self._clicked, direction)
            self._after_time = max(self.repeated_increment_last_time,
                                   int(self._after_time * self.repeated_increment_factor))

    def _on_release(self, *_) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None
            self._after_time = self.repeated_increment_first_time

    def _on_scroll(self,
                   event: tkinter.Event,
                   is_up: bool,
                   normalized_delta: int,
                   modifier: Literal["", "shift", "ctrl"]) -> str | None:
        self.invoke("top" if is_up else "bottom", "scroll")

    def set(self, value: int | float | str) -> None:
        """ Changes the content to the desired value, regardless of the widget's state and admissible values. """
        try:
            formatted_value = "" if value == "" else self._format.format(value)
        except ValueError:
            formatted_value = str(value)
        self._set_regardless(formatted_value)

    def get(self) -> int | float | str:
        """ Returns the current value.\n
        It tries to convert the Entry content from string to number based on the specified format,
        but if it fails, it returns the string unchanged. """
        value = self._entry.get()
        try:
            openidx = self._format.index("{")
            closeidx = self._format.index("}")
        except ValueError:
            format_type = ""
        else:
            format_type = self._format[closeidx-1:closeidx].lower() if closeidx-openidx > 1 else ""
            #remove constant strings placed before "{" and after "}"
            value = value.strip()
            value = value.removeprefix(self._format[:openidx].strip())
            value = value.removesuffix(self._format[closeidx+1:].strip())
            value = value.strip()

        if format_type not in ("c", "s"):
            try:
                #convert the str value back to a number based on the format_type
                if format_type == "%":
                    value = value.removesuffix("%")
                    value = float(value) / 100
                elif format_type in "efgn" or "." in value:
                    value = float(value)
                else:
                    if   format_type == "b": base = 2
                    elif format_type == "o": base = 8
                    elif format_type == "x": base = 16
                    else:                    base = 10
                    value = int(value, base)
            except ValueError:
                pass
        return value

    def invoke(self,
               direction: Literal["top", "bottom", "none"],
               type_: Literal["button", "scroll"] = "button") -> None:
        """ Changes the current value following the provided direction and using the proper step.
        If direction is 'none', the format is applied in case it is missing after an user edit.\n
        Can be called to simulate the user who clicks or scroll on the widget. """
        if self._state != tkinter.DISABLED:
            if direction == "none":
                delta = 0
            else:
                delta = self._scrollincrement if type_ == "scroll" else self._buttonincrement
                if direction == "bottom":
                    delta = -delta

            current_value = self.get()

            #values mode -> delta is applied to the index of the current value
            if self._values:
                try:
                    idx = self._values.index(current_value) + delta
                except ValueError:
                    if delta != 0:
                        new_value = self._values[-1 if direction == "bottom" else 0]
                    else:
                        new_value = current_value
                else:
                    low = 0 if self._from is None else self._from
                    high = 1e12 if self._to is None else self._to
                    idx = max(0, low, min(idx, high, len(self._values) - 1))
                    new_value = self._values[idx]
            #numeric mode
            else:
                #current value couldn't be converted to a number
                if isinstance(current_value, str):
                    new_value = 0.0
                else:
                    new_value = current_value + delta

                if self._from is not None and new_value < self._from:
                    new_value = self._from
                if self._to is not None and new_value > self._to:
                    new_value = self._to

            self.set(new_value)

            if self._command is not None:
                self._command(new_value)

    def _update_variable(self) -> None:
        if self._variable is None:
            self._entry.configure(textvariable=None)
            self._support_variable = None
        else:
            self._support_variable = tkinter.StringVar(value=self._format.format(self._variable.get()))
            self._entry.configure(textvariable=self._support_variable)
            self._support_variable.trace_add("write", self._support_variable_callback)
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)

    def _support_variable_callback(self, *_: Any) -> None:
        #called when the user edits the Entry manually.
        # converts the string to the proper type, which is then assigned to the original variable
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                value = self.get()
                try:
                    if isinstance(self._variable, tkinter.IntVar):
                        value = round(float(value))
                    elif isinstance(self._variable, tkinter.DoubleVar):
                        value = float(value)
                    else:
                        value = str(value)
                except ValueError:
                    pass
                else:
                    self._variable.set(value)

    def _variable_callback(self, *_: Any) -> None:
        #called when the original variable changes value.
        # converts the value to a string with the proper format, which is then assigned to the support variable
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                value = self._variable.get()
                self._support_variable.set("" if value == "" else self._format.format(value))
