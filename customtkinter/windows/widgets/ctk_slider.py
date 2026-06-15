from __future__ import annotations

import tkinter
from functools import partial
from threading import Lock
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkScrollable, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import ColorType, TransparentColorType, ThemeManager
from .ctk_tooltip import CTkToolTip, CTkToolTipThemedArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor, get_width_height_from_orientation


class CTkSliderThemedArgs(TypedDict, total=False, closed=True):
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
    show_value: bool
    tooltip: CTkToolTipThemedArgs

class CTkSliderArgs(CTkSliderThemedArgs, total=False, closed=True):
    mode: Literal["single", "in_range", "out_range", "any_range"]
    state: Literal["normal", "disabled"]
    from_: int | float
    to: int | float
    number_of_steps: int | None
    format: str  #the syntax is explained here: https://docs.python.org/3/library/string.html#formatstrings
    scrollincrement: float | None
    variable1: tkinter.IntVar | tkinter.DoubleVar | None
    variable2: tkinter.IntVar | tkinter.DoubleVar | None
    command: Callable[[float], None] | Callable[[float, float], None] | None


class CTkSlider(CTkWidget, CTkScrollable):
    """
    Slider with rounded corners, border, number of steps, variable support, vertical orientation.
    Number of buttons and possible values depends on the mode:
    - "single": 1 button with the highlighted part towards left/bottom and no additional limits;
    - "in_range": 2 buttons with the highlighted part in the middle.
                  The buttons can never swap positions, so it is guaranteed that value1 <= value2;
    - "out_range": 2 buttons with the highlighted part going outwards.
                   The buttons can never swap positions, so it is guaranteed that value1 <= value2;
    - "any_range": 2 buttons which can swap positions. If value1 <= value2, it behaves like "in_range",
                   otherwise like "out_range".
    For detailed information check out the documentation.
    """

    # If set to True, when the user moves a slider, the other slider is moved too based on the key pressed:
    # - "shift": in the same direction, so as to preserve the distance between the sliders;
    # - "ctrl": in the opposite direction, so as to maintain the center in the same place (zoom effect).
    enable_combo_movements: bool = True

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

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=width,
                           height=height)
        CTkScrollable.__init__(self, self.winfo_toplevel())

        #functionality
        self._mode: Literal["single", "in_range", "out_range", "any_range"] = kwargs.pop("mode", "single")
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._command: Callable[[float], None] | Callable[[float, float], None] | None = kwargs.pop("command", None)
        self._variables: list[tkinter.IntVar | tkinter.DoubleVar | None] = [kwargs.pop("variable1", None), kwargs.pop("variable2", None)]
        self._variable_callback_names: list[str | None] = [None, None]
        self._values: list[float] = [0.0, 1.0]
        self._from: int | float = kwargs.pop("from_", 0.0)
        self._to: int | float = kwargs.pop("to", 1.0)
        self._number_of_steps: int | None = kwargs.pop("number_of_steps", None)
        self._format: str = kwargs.pop("format", "{:.2f}")
        self._scrollincrement: float = kwargs.pop("scrollincrement", (1 / (20 if self._number_of_steps is None else self._number_of_steps)))
        self._output_values: list[float] = [self._from, self._to]
        self._target_slider: int | None = None
        self._motion_center_offset: float = 0.0
        self._block_value_propagation: Lock = Lock()

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._progress_bar = RoundedRect(self._canvas, events_transparent=True)
        self._sliders: list[RoundedRect] = [RoundedRect(self._canvas), RoundedRect(self._canvas)]
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        self._create_bindings()
        self._tooltip = CTkToolTip(self,
                                   mode="live_mouse",
                                   close_on_interaction=False,
                                   text=self._get_tt_text,
                                   **self._theme_info["tooltip"])

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._set_cursor()
        self._draw(force_colors_update=True)

        for n, variable in enumerate(self._variables):
            if variable is not None:
                self._variable_callback_names[n] = variable.trace_add("write", partial(self._variable_callback, n))
                self._variable_callback(n)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._rounded_rect.bind("<Button-1>", self._clicked)
            for slider in self._sliders:
                slider.bind("<Button-1>", self._clicked_slider)
        if sequence is None or sequence == "<ButtonRelease-1>":
            self._canvas.bind("<ButtonRelease-1>", self._on_release)
        if sequence is None or sequence == "<B1-Motion>":
            self._canvas.bind("<B1-Motion>", self._on_motion)
        if self._mode != "single":
            if sequence is None or sequence == "<Motion>":
                self._canvas.bind("<Motion>", self._on_enter)

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
        for variable, callback_name in zip(self._variables, self._variable_callback_names):
            if variable is not None:
                variable.trace_remove("write", callback_name)

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
            button1_x_start = spacing + (self._current_width - button_length - 2 * spacing) * self._values[0]
            button2_x_start = spacing + (self._current_width - button_length - 2 * spacing) * self._values[1]
            button1_y_start = button2_y_start = 0
            button_width = button_length
            button_height = self._current_height

            progress_x_start = min(button1_x_start, button2_x_start) + 1
            progress_y_start = border_width
            progress_width = max(button1_x_start, button2_x_start) - 1 + button_width - progress_x_start
            progress_height = info("inner_height", 0)
        else:
            button1_x_start = button2_x_start = 0
            button1_y_start = spacing + (self._current_height - button_length- 2 * spacing) * (1 - self._values[0])
            button2_y_start = spacing + (self._current_height - button_length- 2 * spacing) * (1 - self._values[1])
            button_width = self._current_width
            button_height = button_length

            progress_x_start = border_width
            progress_y_start = min(button1_y_start, button2_y_start) + 1
            progress_width = info("inner_width", 0)
            progress_height = max(button1_y_start, button2_y_start) - 1 + button_height - progress_y_start

        requires_recoloring_2 = self._progress_bar.update(progress_x_start, progress_y_start,
                                                          progress_width, progress_height,
                                                          info("inner_corner_radius", 0))

        if self._mode != "single":
            requires_recoloring_3 = self._sliders[0].update(button1_x_start, button1_y_start,
                                                            button_width, button_height,
                                                            corner_radius)
        else:
            requires_recoloring_3 = False
            self._sliders[0].delete()

        requires_recoloring_4 = self._sliders[1].update(button2_x_start, button2_y_start,
                                                        button_width, button_height,
                                                        corner_radius)

        update_colors = force_colors_update or requires_recoloring_1 or requires_recoloring_2 or requires_recoloring_3 or requires_recoloring_4

        if update_colors or self._mode == "any_range":
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
            progress_color = self._apply_appearance_mode(self._theme_info["progress_color"], if_transparent=self._theme_info["fg_color"])

            if self._mode == "out_range" or (self._mode == "any_range" and self._values[0] > self._values[1]):
                self._rounded_rect.set_main_color(progress_color)
                self._progress_bar.set_color(fg_color)
            else:
                self._rounded_rect.set_main_color(fg_color)
                self._progress_bar.set_color(progress_color)

        if update_colors:
            self._rounded_rect.raise_()
            self._progress_bar.raise_()
            self._sliders[0].raise_()
            self._sliders[1].raise_()

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"], if_transparent=self._bg_color))

            button_color = self._apply_appearance_mode(self._theme_info["button_color"])
            if self._target_slider is not None and self._theme_info["hover"]:
                self._sliders[self._target_slider].set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))
                self._sliders[1 - self._target_slider].set_color(button_color)
            else:
                for slider in self._sliders:
                    slider.set_color(button_color)

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

        if "mode" in kwargs:
            new_mode = kwargs.pop("mode")
            if self._mode == "single" and new_mode != "single":
                self._create_bindings()
            self._mode = new_mode
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

        if "format" in kwargs:
            self._format = kwargs.pop("format")
            if self._tooltip.is_open():
                self._tooltip.show()

        if "scrollincrement" in kwargs:
            self._scrollincrement = kwargs.pop("scrollincrement")

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "show_value" in kwargs:
            self._theme_info["show_value"] = kwargs.pop("show_value")
            if not self._theme_info["show_value"]:
                self._tooltip.close()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        for n in range(2):
            if f"variable{n+1}" in kwargs:
                if self._variables[n] is not None:
                    self._variables[n].trace_remove("write", self._variable_callback_names[n])
                self._variables[n] = kwargs.pop(f"variable{n+1}")
                if self._variables[n] is not None:
                    self._variable_callback_names[n] = self._variables[n].trace_add("write", partial(self._variable_callback, n))
                    self._variable_callback(n)

        if "orientation" in kwargs:
            self._theme_info["orientation"] = kwargs.pop("orientation").lower()
            require_redraw = True

        if "tooltip" in kwargs:
            self._tooltip.configure(**kwargs.pop("tooltip"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "mode":
            return self._mode
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "from_":
            return self._from
        elif attribute_name == "to":
            return self._to
        elif attribute_name == "number_of_steps":
            return self._number_of_steps
        elif attribute_name == "format":
            return self._format
        elif attribute_name == "scrollincrement":
            return self._scrollincrement
        elif attribute_name == "variable1":
            return self._variables[0]
        elif attribute_name == "variable2":
            return self._variables[1]
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("tooltip_"):
            return self._tooltip.cget(attribute_name.removeprefix("tooltip_"))
        else:
            return super().cget(attribute_name)

    def _variable_callback(self, n: int, *_: str) -> None:
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                if n == 0:
                    self.set(output_value1=self._variables[n].get())
                else:
                    self.set(output_value2=self._variables[n].get())

    def _update_value(self, value: float, modifier: Literal["", "shift", "ctrl"]) -> None:
        value = max(0.0, min(value, 1.0))

        if modifier and self._mode != "single" and self.enable_combo_movements:
            delta = value - self._values[self._target_slider]
            other_value = self._values[1 - self._target_slider]
            #clamp delta to respect other slider's boundaries
            if delta >= 0:
                delta = min(delta, (1.0 - other_value) if modifier == "shift" else other_value)
            else:
                delta = max(delta, -other_value if modifier == "shift" else (other_value - 1.0))

            value = self._values[self._target_slider] + delta
            other_value += delta if modifier == "shift" else -delta
            other_value = self._from + (other_value * (self._to - self._from))
        else:
            other_value = None

        value = self._from + (value * (self._to - self._from))

        if self._target_slider == 0:
            self.set(output_value1=value, output_value2=other_value)
        elif self._target_slider == 1:
            self.set(output_value2=value, output_value1=other_value)

        if self._command is not None:
            if self._mode == "single":
                self._command(self._output_values[1])
            else:
                self._command(self._output_values[0], self._output_values[1])

    def _get_value_from_event(self, event: tkinter.Event) -> float:
        info = self._rounded_rect.info.get
        spacing = max(0, info("flat_spacing", 0) - info("corner_radius", 0))
        if self._theme_info["orientation"] == "horizontal":
            value = (event.x - spacing) / (self._current_width - 2 * spacing - self._sliders[1].info["width"])
        else:
            value = 1.0 - ((event.y - spacing) / (self._current_height - 2 * spacing - self._sliders[1].info["height"]))
        return value

    def _on_enter(self, event: tkinter.Event | None = None) -> None:
        #while scrolling, we avoid changing the target even if the current target gets further from the mouse
        if self._state == tkinter.NORMAL and not self.is_scroll_ongoing():
            #calculate target slider
            if self._mode == "single":
                new_target = 1
            else:
                value = self._get_value_from_event(event)
                if self._theme_info["orientation"] == "horizontal":
                    button_length = self._sliders[1].info["width"] / self._current_width
                else:
                    button_length = -self._sliders[1].info["height"] / self._current_height
                diff1 = abs(self._values[0] + button_length / 2 - value)
                diff2 = abs(self._values[1] + button_length / 2 - value)
                if diff1 == diff2:
                    new_target = 0 if value < self._values[0] else 1
                else:
                    new_target = 0 if diff1 < diff2 else 1

            #update colors only if the new target is different with respect to the current one
            if self._target_slider != new_target:
                self._target_slider = new_target
                if self._theme_info["hover"]:
                    self._sliders[self._target_slider].set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))
                    self._sliders[1 - self._target_slider].set_color(self._apply_appearance_mode(self._theme_info["button_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._tooltip.close()
        self._target_slider = None

        button_color = self._apply_appearance_mode(self._theme_info["button_color"])
        for slider in self._sliders:
            slider.set_color(button_color)

    def _clicked(self, event: tkinter.Event) -> None:
        if self._state == tkinter.NORMAL and self._target_slider is not None:
            if self._theme_info["orientation"] == "horizontal":
                button_length = self._sliders[self._target_slider].info["width"]
                length = self._current_width
                sign = -1.0
            else:
                button_length = self._sliders[self._target_slider].info["height"]
                length = self._current_height
                sign = +1.0
            info = self._rounded_rect.info.get
            spacing = max(0, info("flat_spacing", 0) - info("corner_radius", 0))
            self._motion_center_offset = sign * (button_length / 2) / (length - 2 * spacing - button_length)
            self._on_motion(event)

    def _clicked_slider(self, event: tkinter.Event) -> None:
        if self._state == tkinter.NORMAL and self._target_slider is not None:
            clicked_value = self._get_value_from_event(event)
            self._motion_center_offset = self._values[self._target_slider] - clicked_value
            if self._theme_info["show_value"]:
                self._tooltip.show()

    def _on_motion(self, event: tkinter.Event) -> None:
        if self._state == tkinter.NORMAL and self._target_slider is not None:
            new_center = self._get_value_from_event(event) + self._motion_center_offset
            if event.state & 0x1:
                modifier = "shift"
            elif event.state & 0x4:
                modifier = "ctrl"
            else:
                modifier = ""
            self._update_value(new_center, modifier)
            if self._theme_info["show_value"]:
                self._tooltip.show()

    def _on_release(self, _: tkinter.Event) -> None:
        if self._tooltip.cget("delay") < 0:
            self._tooltip.close()

    def _on_scroll(self,
                   event: tkinter.Event,
                   is_up: bool,
                   normalized_delta: int,
                   modifier: Literal["", "shift", "ctrl"]) -> str | None:
        if self._state == tkinter.NORMAL and self._target_slider is not None:
            delta = self._scrollincrement * abs(normalized_delta) * (1 if is_up else -1)
            self._update_value(self._values[self._target_slider] + delta, modifier)
            if self._tooltip.is_open():
                self._tooltip.show()

    def _round_to_step_size(self, value: float) -> float:
        if self._number_of_steps is not None:
            step_size = (self._to - self._from) / self._number_of_steps
            value = self._to - (round((self._to - value) / step_size) * step_size)
            return value
        else:
            return value

    def _get_tt_text(self) -> str:
        if self._target_slider is None:
            return ""
        else:
            return self._format.format(self._output_values[self._target_slider])

    def set(self,
            output_value1: float | tuple[float | float] | None = None,
            output_value2: float | None = None) -> None:
        """" Sets slider[s] to the provided value.\n
        For the 'single' mode, you can use any of the 2 arguments.\n
        For other modes, 'output_value1' is used for the slider that is usually associated with the minimum value,
        while 'output_value2' is used for the slider that is associated with the maximum value
        (they can be flipped in 'any_range' mode). """

        if isinstance(output_value1, tuple):
            output_value1, output_value2 = output_value1

        if self._mode == "single":
            #force to change _sliders[1] only
            output_value2 = output_value1 if output_value1 is not None else output_value2
            output_value1 = None
        elif self._mode != "any_range":
            #force sliders to not swap positions
            if output_value1 is not None and output_value2 is not None:
                if (output_value1 > output_value2) ^ (self._from > self._to):
                    output_value1 = output_value2 = (output_value1 + output_value2) / 2
            elif output_value1 is not None:
                if (output_value1 > self._output_values[1]) ^ (self._from > self._to):
                    output_value1 = self._output_values[1]
            elif output_value2 is not None:
                if (output_value2 < self._output_values[0]) ^ (self._from > self._to):
                    output_value2 = self._output_values[0]

        low = min(self._from, self._to)
        high = max(self._from, self._to)
        for n, value in enumerate((output_value1, output_value2)):
            if value is not None:
                value = max(low, min(value, high))
                self._output_values[n] = self._round_to_step_size(value)
                self._values[n] = (self._output_values[n] - self._from) / (self._to - self._from)

        self._draw()

        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                for n, variable in enumerate(self._variables):
                    if variable is not None:
                        value = self._output_values[1] if self._mode == "single" else self._output_values[n]
                        variable.set(round(value) if isinstance(variable, tkinter.IntVar) else value)

    def get(self) -> float | tuple[float, float]:
        """" Returns the current value of the slider[s].\n
        In 'single' mode, it is a single float number.\n
        For other modes, a tuple of 2 float numbers is returned, with the first element representing
        the minimum value of the range, and the second the maximum.
        If 'any_range' mode, the minimum value could be bigger than the maximum to indicate an "outside" range.
        For other modes, it is guaranteed that min <= max (if 'from_' <= 'to', otherwise the opposite is true). """
        if self._mode == "single":
            return self._output_values[1]
        else:
            return self._output_values[0], self._output_values[1]
