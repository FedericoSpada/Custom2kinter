from __future__ import annotations

import tkinter
import math
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .theme import ThemeManager


class CTkProgressBarArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    lenght: int
    corner_radius: int
    border_width: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    progress_color: str | tuple[str, str]


class CTkProgressBar(CTkBaseClass):
    """
    Progressbar with rounded corners, border, variable support,
    indeterminate mode, vertical orientation.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 mode: Literal["determinate", "indeterminate"] = "determinate",
                 determinate_speed: float = 1.0,
                 indeterminate_speed: float = 1.0,
                 variable: tkinter.DoubleVar | tkinter.IntVar | None = None,
                 **kwargs: Unpack[CTkProgressBarArgs]) -> None:

        self._theme_info: CTkProgressBarArgs = ThemeManager.get_info("CTkProgressBar", theme_key, **kwargs)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        # set default dimensions according to orientation
        if self._theme_info["orientation"] == "vertical":
            width = self._theme_info["thickness"]
            height = self._theme_info["lenght"]
        else:
            width = self._theme_info["lenght"]
            height = self._theme_info["thickness"]

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=width,
                         height=height)

        # control variable
        self._variable: tkinter.DoubleVar | tkinter.IntVar | None = variable
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None

        # functionality
        self._mode: Literal["determinate", "indeterminate"] = mode
        self._determinate_value: float = 0.5  # range 0-1
        self._determinate_speed: float = determinate_speed  # range 0-1
        self._indeterminate_value: float = 0.0  # range 0-inf
        self._indeterminate_width: float = 0.4  # range 0-1
        self._indeterminate_speed: float = indeterminate_speed  # range 0-1 to travel in 50ms
        self._loop_running: bool = False
        self._loop_after_id: str | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nswe")
        self._draw_engine = DrawEngine(self._canvas)

        self._draw()  # initial draw

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback_blocked = True
            self.set(self._variable.get(), from_variable_callback=True)
            self._variable_callback_blocked = False

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        super().destroy()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        if self._mode == "determinate":
            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                                          self._apply_widget_scaling(self._theme_info["border_width"]),
                                                                                          0,
                                                                                          self._determinate_value,
                                                                                          self._theme_info["orientation"])
        else:  # indeterminate mode
            progress_value = (math.sin(self._indeterminate_value * math.pi / 40) + 1) / 2
            progress_value_1 = min(1.0, progress_value + (self._indeterminate_width / 2))
            progress_value_2 = max(0.0, progress_value - (self._indeterminate_width / 2))

            requires_recoloring = self._draw_engine.draw_rounded_progress_bar_with_border(self._apply_widget_scaling(self._current_width),
                                                                                          self._apply_widget_scaling(self._current_height),
                                                                                          self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                                          self._apply_widget_scaling(self._theme_info["border_width"]),
                                                                                          progress_value_1,
                                                                                          progress_value_2,
                                                                                          self._theme_info["orientation"])

        if no_color_updates is False or requires_recoloring:
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["border_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["border_color"]))
            self._canvas.itemconfig("inner_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["fg_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["fg_color"]))
            self._canvas.itemconfig("progress_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["progress_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["progress_color"]))

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkProgressBarArgs]) -> None:
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
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self.set(self._variable.get(), from_variable_callback=True)

        if "mode" in kwargs:
            self._mode = kwargs.pop("mode")
            require_redraw = True

        if "determinate_speed" in kwargs:
            self._determinate_speed = kwargs.pop("determinate_speed")

        if "indeterminate_speed" in kwargs:
            self._indeterminate_speed = kwargs.pop("indeterminate_speed")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "mode":
            return self._mode
        elif attribute_name == "determinate_speed":
            return self._determinate_speed
        elif attribute_name == "indeterminate_speed":
            return self._indeterminate_speed
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self.set(self._variable.get(), from_variable_callback=True)

    def set(self, value: float, from_variable_callback: bool = False) -> None:
        """ set determinate value """
        self._determinate_value = value

        if self._determinate_value > 1.0:
            self._determinate_value = 1.0
        elif self._determinate_value < 0.0:
            self._determinate_value = 0.0

        self._draw(no_color_updates=True)

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(round(self._determinate_value) if isinstance(self._variable, tkinter.IntVar) else self._determinate_value)
            self._variable_callback_blocked = False

    def get(self) -> float:
        """ get determinate value """
        return self._determinate_value

    def start(self) -> None:
        """ start automatic mode """
        if not self._loop_running:
            self._loop_running = True
            self._internal_loop()

    def stop(self) -> None:
        """ stop automatic mode """
        if self._loop_after_id is not None:
            self.after_cancel(self._loop_after_id)
        self._loop_running = False

    def _internal_loop(self) -> None:
        if self._loop_running:
            if self._mode == "determinate":
                self._determinate_value += self._determinate_speed / 50.0
                if self._determinate_value > 1.0:
                    self._determinate_value -= 1.0
                self._draw()
                self._loop_after_id = self.after(20, self._internal_loop)
            else:
                self._indeterminate_value += self._indeterminate_speed
                self._draw()
                self._loop_after_id = self.after(20, self._internal_loop)

    def step(self) -> None:
        """ increase progress """
        if self._mode == "determinate":
            self._determinate_value += self._determinate_speed / 50.0
            if self._determinate_value > 1.0:
                self._determinate_value -= 1.0
            self._draw()
        else:
            self._indeterminate_value += self._indeterminate_speed
            self._draw()

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)

    def focus(self) -> None:
        return self._canvas.focus()

    def focus_set(self) -> None:
        return self._canvas.focus_set()

    def focus_force(self) -> None:
        return self._canvas.focus_force()
