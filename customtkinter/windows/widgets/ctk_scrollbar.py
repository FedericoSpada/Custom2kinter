from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_width_height_from_orientation


class CTkScrollbarThemedArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    length: int
    minimum_pixel_length: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    button_color: ColorType
    button_hover_color: ColorType
    border_color: TransparentColorType
    hover: bool

class CTkScrollbarArgs(CTkScrollbarThemedArgs, total=False):
    command: Callable[[str, int | float, str], None] | None


class CTkScrollbar(CTkWidget):
    """
    Scrollbar with rounded corners, configurable spacing.
    Connect to scrollable widget by passing .set() method and set command attribute.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkScrollbarArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkScrollbarThemedArgs.__annotations__)
        self._theme_info: CTkScrollbarThemedArgs = ThemeManager.get_info("CTkScrollbar", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("border_color", "fg_color", "bg_color"))

        # set default dimensions according to orientation
        width, height = get_width_height_from_orientation(self._theme_info["orientation"],
                                                          self._theme_info["thickness"],
                                                          self._theme_info["length"])

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=width,
                         height=height)

        # functionality
        self._command: Callable[[str, int | float, str], None] | None = kwargs.pop("command", None)
        self._start_value: float = 0.0  # 0 to 1
        self._end_value: float = 1.0  # 0 to 1
        self._motion_center_offset: float = 0.0
        self._hover_state: bool = False

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._slider = RoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_bindings()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None:
            self._rounded_rect.bind("<Button-1>", self._clicked)
            self._slider.bind("<Button-1>", self._clicked_scrollbar)
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
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

    def _get_scrollbar_values_for_minimum_pixel_size(self) -> tuple[float, float]:
        # correct scrollbar float values if scrollbar is too small
        current_length = self._current_height if self._theme_info["orientation"] == "vertical" else self._current_width
        if current_length != 0:
            minimal_length = min(0.9, self._apply_scaling(float(self._theme_info["minimum_pixel_length"])) / current_length)
        else:
            minimal_length = 0
        actual_length = self._end_value - self._start_value

        #if actual length is less than the minimum one and there is space available
        if actual_length < minimal_length and actual_length < 1.0:
            #we change the values so that the new length  is exactly equal to the requested one.
            # the formula has been derived considering that the scrollbar gets bigger evenly
            # when in the middle, it extends only towards max when already at the min,
            # and it extends only towards min when already at the max
            corrected_start_value = self._start_value * (1.0 - minimal_length) / (1.0 - actual_length)
            corrected_end_value = corrected_start_value + minimal_length
            return corrected_start_value, corrected_end_value
        else:
            return self._start_value, self._end_value

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
        corrected_start_value, corrected_end_value = self._get_scrollbar_values_for_minimum_pixel_size()

        if self._theme_info["orientation"] == "horizontal":
            x_start += width * corrected_start_value
            width *= (corrected_end_value - corrected_start_value)
        else:
            y_start += height * corrected_start_value
            height *= (corrected_end_value - corrected_start_value)

        requires_recoloring_2 = self._slider.update(x_start, y_start,
                                                    width, height,
                                                    info("inner_corner_radius", 0))

        if force_colors_update or requires_recoloring_1 or requires_recoloring_2:
            self._rounded_rect.raise_()
            self._slider.raise_()

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"], if_transparent=self._bg_color))

            if self._hover_state:
                self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))
            else:
                self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_color"]))

        self._canvas.update_idletasks()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkScrollbarArgs]) -> None:
        if "thickness" in kwargs:
            self._theme_info["thickness"] = kwargs.pop("thickness")
            kwargs["width" if self._theme_info["orientation"] == "vertical" else "height"] = self._theme_info["thickness"]

        if "length" in kwargs:
            self._theme_info["length"] = kwargs.pop("length")
            kwargs["height" if self._theme_info["orientation"] == "vertical" else "width"] = self._theme_info["length"]

        if "minimum_pixel_length" in kwargs:
            self._theme_info["minimum_pixel_length"] = kwargs.pop("minimum_pixel_length")
            require_redraw = True

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "button_color" in kwargs:
            self._theme_info["button_color"] = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._theme_info["button_hover_color"] = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"), transparency=True)
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        if self._theme_info["hover"]:
            self._hover_state = True
            self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_hover_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._hover_state = False
        self._slider.set_color(self._apply_appearance_mode(self._theme_info["button_color"]))

    def _clicked(self, event: tkinter.Event) -> None:
        self._motion_center_offset = 0.0
        self._on_motion(event)

    def _get_value_from_event(self, event: tkinter.Event) -> float:
        spacing = self._rounded_rect.info.get("flat_spacing", 0)
        if self._theme_info["orientation"] == "vertical":
            value = (event.y - spacing) / (self._current_height - 2 * spacing)
        else:
            value = (event.x - spacing) / (self._current_width - 2 * spacing)
        return value

    def _clicked_scrollbar(self, event: tkinter.Event) -> None:
        clicked_value = self._get_value_from_event(event)
        current_center = (self._start_value + self._end_value) / 2
        self._motion_center_offset = current_center - clicked_value

    def _on_motion(self, event: tkinter.Event) -> None:
        half_length = (self._end_value - self._start_value) / 2
        new_center = self._get_value_from_event(event) + self._motion_center_offset
        new_center = max(half_length, min(1 - half_length, new_center))
        self._start_value = new_center - half_length
        self._end_value = new_center + half_length
        self._draw()

        if self._command is not None:
            self._command("moveto", self._start_value)

    def _mouse_scroll_event(self, event: tkinter.Event) -> None:
        if self._command is not None:
            if sys.platform.startswith("win"):
                delta = -int(event.delta/40)
            elif sys.platform == "darwin":
                delta = -event.delta
            else:
                delta = -1 if event.num == 4 else 1
            self._command("scroll", delta, "units")
        else:
            #empty space is divided in 20 steps
            delta = (1 - self._end_value + self._start_value) / 20
            #condition for both Linux and others OS
            if event.delta > 0 or event.num == 4:
                delta = -delta

            if self._start_value + delta < 0.0:
                self._end_value = self._end_value - self._start_value
                self._start_value = 0.0
            elif self._end_value + delta > 1.0:
                self._start_value = 1 - self._end_value + self._start_value
                self._end_value = 1.0
            else:
                self._start_value += delta
                self._end_value += delta
            self._draw()

    def set(self, start_value: float, end_value: float) -> None:
        self._start_value = float(start_value)
        self._end_value = float(end_value)
        self._draw()

    def get(self) -> tuple[float, float]:
        return self._start_value, self._end_value
