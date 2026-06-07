from __future__ import annotations

import tkinter
import math
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_width_height_from_orientation


class CTkProgressBarThemedArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    length: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: ColorType
    border_color: ColorType
    progress_color: ColorType

class CTkProgressBarArgs(CTkProgressBarThemedArgs, total=False):
    mode: Literal["determinate", "indeterminate", "single_run"]
    progress_speed: float # [%/s]
    variable: tkinter.DoubleVar | tkinter.IntVar | None


class CTkProgressBar(CTkWidget):
    """
    Progressbar with rounded corners, border, variable support,
    indeterminate mode, vertical orientation.
    For detailed information check out the documentation.
    """

    update_time: int = 40  # interval in [ms], to update progress value

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkProgressBarArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkProgressBarThemedArgs.__annotations__)
        self._theme_info: CTkProgressBarThemedArgs = ThemeManager.get_info("CTkProgressBar", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        # set default dimensions according to orientation
        width, height = get_width_height_from_orientation(self._theme_info["orientation"],
                                                          self._theme_info["thickness"],
                                                          self._theme_info["length"])

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=width,
                         height=height)

        # control variable
        self._variable: tkinter.DoubleVar | tkinter.IntVar | None = kwargs.pop("variable", None)
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None
        self._is_intvar = isinstance(self._variable, tkinter.IntVar)

        # functionality
        self._mode: Literal["determinate", "indeterminate", "single_run"] = kwargs.pop("mode", "determinate")
        self._progress_speed: float = kwargs.pop("progress_speed", 0.5) # [%/s]
        self._value: float = 0.0 # range 0-1
        self._indeterminate_width: float = 0.4  # range 0-1
        self._loop_running: bool = False
        self._loop_after_id: str | None = None
        self._loop_prev_time: float = 0.0

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._progress_bar = RoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._draw(force_colors_update=True)

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback()

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
        self.stop()
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring_1 = self._rounded_rect.update(self._current_width,
                                                          self._current_height,
                                                          self._apply_scaling(self._theme_info["corner_radius"]),
                                                          self._apply_scaling(self._theme_info["border_width"]))

        info = self._rounded_rect.info.get
        x_start = y_start = info("border_width", 0)
        width = info("inner_width", 0)
        height = info("inner_height", 0)
        corner_radius = info("inner_corner_radius", 0)

        if self._mode == "indeterminate":
            progress_value = (1 - math.cos(2 * math.pi * self._value)) / 2
            progress_value_1 = max(0.0, progress_value - (self._indeterminate_width / 2))
            progress_value_2 = min(1.0, progress_value + (self._indeterminate_width / 2))
        else:
            progress_value_1 = 0.0
            if self._value == 0.0:
                progress_value_2 = 0.0
            else:
                #we correct the value so that the minimal length is 2 * corner_radius
                current_length = height if self._theme_info["orientation"] == "vertical" else width
                progress_value_2 = (self._value * (current_length - 2 * corner_radius) + 2 * corner_radius) / current_length

        if self._theme_info["orientation"] == "horizontal":
            x_start += width * progress_value_1
            width *= (progress_value_2 - progress_value_1)
        else:
            y_start += height * (1 - progress_value_2)
            height *= (progress_value_2 - progress_value_1)

        requires_recoloring_2 = self._progress_bar.update(x_start, y_start,
                                                          width, height,
                                                          corner_radius)

        if force_colors_update or requires_recoloring_1 or requires_recoloring_2:
            self._rounded_rect.raise_()
            self._progress_bar.raise_()

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self._theme_info["fg_color"]))
            self._progress_bar.set_color(self._apply_appearance_mode(self._theme_info["progress_color"]))

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkProgressBarArgs]) -> None:
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

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "progress_color" in kwargs:
            self._theme_info["progress_color"] = self._check_color_type(kwargs.pop("progress_color"))
            require_redraw = True

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._variable_callback()
            self._is_intvar = isinstance(self._variable, tkinter.IntVar)

        if "mode" in kwargs:
            self._mode = kwargs.pop("mode")
            require_redraw = True

        if "progress_speed" in kwargs:
            self._progress_speed = kwargs.pop("progress_speed")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "mode":
            return self._mode
        elif attribute_name == "progress_speed":
            return self._progress_speed
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            value = self._variable.get()
            self.set(value / 100 if self._is_intvar else value, from_variable_callback=True)

    def set(self, value: float, from_variable_callback: bool = False) -> None:
        """ Sets progress to specified value
        \nFor 'indeterminate' mode:
        -   0% -> completely on the left/bottom
        -  50% -> completely on the right/top
        - 100% -> again on the left/bottom, ready for a new cycle 
        \nFor other mode:
        -   0% -> completely on the left/bottom
        - 100% -> completely on the right/top """
        self._value = max(0.0, min(value, 1.0))

        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._value * 100) if self._is_intvar else self._value)
            self._variable_callback_blocked = False

    def step(self, increment: float) -> None:
        """ Increases progress by specified value (it can be negative) """
        self.set(self._value + increment)

    def get(self) -> float:
        """ Returns current progress value
        \nFor 'indeterminate' mode:
        -   0% -> completely on the left/bottom
        -  50% -> completely on the right/top
        - 100% -> again on the left/bottom, ready for a new cycle 
        \nFor other mode:
        -   0% -> completely on the left/bottom
        - 100% -> completely on the right/top """
        return self._value

    def start(self) -> None:
        """ Starts automatic mode from the current value """
        if not self._loop_running:
            self._loop_running = True
            self._internal_loop()

    def stop(self) -> None:
        """ Stops automatic mode """
        if self._loop_after_id is not None:
            self.after_cancel(self._loop_after_id)
            self._loop_after_id = None
        self._loop_running = False

    def _internal_loop(self) -> None:
        if self._loop_running:
            new_value = self._value + self._progress_speed * self.update_time / 1000.0
            if new_value > 1.0 and self._mode != "single_run":
                new_value -= 1.0

            self.set(new_value)

            if self._mode == "single_run" and self._value >= 1.0:
                self._loop_after_id = None
                self._loop_running = False
            else:
                self._loop_after_id = self.after(self.update_time, self._internal_loop)
