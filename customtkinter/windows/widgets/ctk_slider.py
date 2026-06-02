from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor, get_width_height_from_orientation


class CTkSliderThemedArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    length: int
    button_length: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: ColorType
    button_color: ColorType
    button_hover_color: ColorType
    border_color: TransparentColorType
    progress_color: TransparentColorType
    hover: bool

class CTkSliderArgs(CTkSliderThemedArgs, total=False):
    state: Literal["normal", "disabled"]
    from_: int | float
    to: int | float
    number_of_steps: int | None
    scroll_step: float | None
    variable: tkinter.IntVar | tkinter.DoubleVar | None
    command: Callable[[float], None] | None


class CTkSlider(CTkWidget):
    """
    Slider with rounded corners, border, number of steps, variable support, vertical orientation.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkSliderArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkSliderThemedArgs.__annotations__)
        self._theme_info: CTkSliderThemedArgs = ThemeManager.get_info("CTkSlider", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("border_color", "progress_color", "bg_color"))

        # set default dimensions according to orientation
        width, height = get_width_height_from_orientation(self._theme_info["orientation"],
                                                          self._theme_info["thickness"],
                                                          self._theme_info["length"])

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=width,
                         height=height)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", "normal")
        self._command: Callable[[float], None] | None = kwargs.pop("command", None)
        self._variable: tkinter.IntVar | tkinter.DoubleVar = kwargs.pop("variable", None)
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None
        self._value: float = 0.5  # initial value of slider in percent
        self._from: int | float = kwargs.pop("from_", 0.0)
        self._to: int | float = kwargs.pop("to", 1.0)
        self._number_of_steps: int | None = kwargs.pop("number_of_steps", None)
        self._scroll_step: float = kwargs.pop("scroll_step", (1 / (20 if self._number_of_steps is None else self._number_of_steps)))
        self._output_value: float = self._from + (self._value * (self._to - self._from))
        self._hover_state: bool = False
        self._motion_center_offset: float = 0.0

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._progress_bar = RoundedRect(self._canvas, events_transparent=True)
        self._slider = RoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_bindings()
        self._set_cursor()
        self._draw(force_colors_update=True)

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set(self._variable.get(), from_variable_callback=True)
            self._variable_callback_blocked = False

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._rounded_rect.bind("<Button-1>", self._clicked)
            self._slider.bind("<Button-1>", self._clicked_slider)
        if sequence is None or sequence == "<B1-Motion>":
            self._canvas.bind("<B1-Motion>", self._on_motion)
        if "linux" in sys.platform:
            if sequence is None or sequence == "<Button-4>":
                self._canvas.bind("<Button-4>", self._mouse_scroll_event)
            if sequence is None or sequence == "<Button-5>":
                self._canvas.bind("<Button-5>", self._mouse_scroll_event)
        else:
            if sequence is None or sequence == "<MouseWheel>":
                self._canvas.bind("<MouseWheel>", self._mouse_scroll_event)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def destroy(self) -> None:
        # remove variable_callback from variable callbacks if variable exists
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _set_cursor(self) -> None:
        cursor = get_proper_cursor("normal" if self._state != tkinter.NORMAL else "clickable")
        if cursor is not None:
            self.configure(cursor=cursor)

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring_1 = self._rounded_rect.update(self._current_width,
                                                          self._current_height,
                                                          self._apply_scaling(self._theme_info["corner_radius"]),
                                                          self._apply_scaling(self._theme_info["border_width"]))

        info = self._rounded_rect.info.get
        corner_radius = info("corner_radius", 0)
        border_width = info("border_width", 0)
        button_length = self._apply_scaling(self._theme_info["button_length"]) + 2 * corner_radius
        spacing = max(0, info("flat_spacing", 0) - corner_radius)

        if self._theme_info["orientation"] == "horizontal":
            button_x_start = spacing + (self._current_width - button_length - 2 * spacing) * self._value
            button_y_start = 0
            button_width = button_length
            button_height = self._current_height

            progress_x_start = border_width
            progress_y_start = border_width
            progress_width = button_x_start + button_width - progress_x_start - 1
            progress_height = info("inner_height", 0)
        else:
            button_x_start = 0
            button_y_start = spacing + (self._current_height - button_length- 2 * spacing) * (1 - self._value)
            button_width = self._current_width
            button_height = button_length

            progress_x_start = border_width
            progress_y_start = button_y_start + 1
            progress_width = info("inner_width", 0)
            progress_height = border_width + info("inner_height", 0) - progress_y_start

        requires_recoloring_2 = self._progress_bar.update(progress_x_start, progress_y_start,
                                                          progress_width, progress_height,
                                                          info("inner_corner_radius", 0))

        requires_recoloring_3 = self._slider.update(button_x_start, button_y_start,
                                                    button_width, button_height,
                                                    corner_radius)

        if force_colors_update or requires_recoloring_1 or requires_recoloring_2 or requires_recoloring_3:
            self._rounded_rect.raise_()
            self._progress_bar.raise_()
            self._slider.raise_()

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self._theme_info["fg_color"]))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"], if_transparent=self._bg_color))
            self._progress_bar.set_color(self._apply_appearance_mode(self._theme_info["progress_color"], if_transparent=self._theme_info["fg_color"]))

            if self._hover_state:
                self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))
            else:
                self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_color"]))

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkSliderArgs]) -> None:
        if "thickness" in kwargs:
            self._theme_info["thickness"] = kwargs.pop("thickness")
            kwargs["width" if self._theme_info["orientation"] == "vertical" else "height"] = self._theme_info["thickness"]

        if "length" in kwargs:
            self._theme_info["length"] = kwargs.pop("length")
            kwargs["height" if self._theme_info["orientation"] == "vertical" else "width"] = self._theme_info["length"]

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "button_length" in kwargs:
            self._theme_info["button_length"] = kwargs.pop("button_length")
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"), transparency=True)
            require_redraw = True

        if "progress_color" in kwargs:
            self._theme_info["progress_color"] = self._check_color_type(kwargs.pop("progress_color"), transparency=True)
            require_redraw = True

        if "button_color" in kwargs:
            self._theme_info["button_color"] = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._theme_info["button_hover_color"] = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "from_" in kwargs:
            self._from = kwargs.pop("from_")

        if "to" in kwargs:
            self._to = kwargs.pop("to")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "number_of_steps" in kwargs:
            self._number_of_steps = kwargs.pop("number_of_steps")

        if "scroll_step" in kwargs:
            self._scroll_step = kwargs.pop("scroll_step")

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)

        if "orientation" in kwargs:
            self._theme_info["orientation"] = kwargs.pop("orientation").lower()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "from_":
            return self._from
        elif attribute_name == "to":
            return self._to
        elif attribute_name == "number_of_steps":
            return self._number_of_steps
        elif attribute_name == "scroll_step":
            return self._scroll_step
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _update_value(self, value: float) -> None:
        value = max(0.0, min(1.0, value))
        self.set(self._from + (value * (self._to - self._from)))

        if self._command is not None:
            self._command(self._output_value)

    def _clicked(self, event: tkinter.Event) -> None:
        if self._theme_info["orientation"] == "horizontal":
            button_length = self._slider.info["width"]
            length = self._current_width
            sign = -1.0
        else:
            button_length = self._slider.info["height"]
            length = self._current_height
            sign = +1.0
        info = self._rounded_rect.info.get
        spacing = max(0, info("flat_spacing", 0) - info("corner_radius", 0))
        self._motion_center_offset = sign * (button_length / 2) / (length - 2 * spacing - button_length)
        self._on_motion(event)

    def _get_value_from_event(self, event: tkinter.Event) -> float:
        info = self._rounded_rect.info.get
        spacing = max(0, info("flat_spacing", 0) - info("corner_radius", 0))
        if self._theme_info["orientation"] == "horizontal":
            value = (event.x - spacing) / (self._current_width - 2 * spacing - self._slider.info["width"])
        else:
            value = 1.0 - ((event.y - spacing) / (self._current_height - 2 * spacing - self._slider.info["height"]))
        return value

    def _clicked_slider(self, event: tkinter.Event) -> None:
        clicked_value = self._get_value_from_event(event)
        self._motion_center_offset = self._value - clicked_value

    def _on_motion(self, event: tkinter.Event) -> None:
        if self._state == tkinter.NORMAL:
            new_center = self._get_value_from_event(event) + self._motion_center_offset
            self._update_value(new_center)

    def _mouse_scroll_event(self, event: tkinter.Event) -> None:
        delta = self._scroll_step
        #condition for both Linux and others OS
        if event.delta < 0 or event.num == 5:
            delta = -delta

        self._update_value(self._value + delta)

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        if self._theme_info["hover"] and self._state == tkinter.NORMAL:
            self._hover_state = True
            self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._hover_state = False
        self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_color"]))

    def _round_to_step_size(self, value: float) -> float:
        if self._number_of_steps is not None:
            step_size = (self._to - self._from) / self._number_of_steps
            value = self._to - (round((self._to - value) / step_size) * step_size)
            return value
        else:
            return value

    def set(self, output_value: int | float, from_variable_callback: bool = False) -> None:
        low = min(self._from, self._to)
        high = max(self._from, self._to)
        output_value = max(low, min(output_value, high))

        self._output_value = self._round_to_step_size(output_value)
        self._value = (self._output_value - self._from) / (self._to - self._from)

        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._output_value) if isinstance(self._variable, tkinter.IntVar) else self._output_value)
            self._variable_callback_blocked = False

    def get(self) -> float:
        return self._output_value

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)
