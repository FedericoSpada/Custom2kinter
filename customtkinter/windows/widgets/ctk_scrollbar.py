from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .theme import ThemeManager


class CTkScrollbarArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    lenght: int
    minimum_pixel_length: int
    corner_radius: int
    border_spacing: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    button_color: str | tuple[str, str]
    button_hover_color: str | tuple[str, str]
    hover: bool


class CTkScrollbar(CTkBaseClass):
    """
    Scrollbar with rounded corners, configurable spacing.
    Connect to scrollable widget by passing .set() method and set command attribute.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 command: Callable[[str, int | float, str], None] | None = None,
                 **kwargs: Unpack[CTkScrollbarArgs]) -> None:

        self._theme_info: CTkScrollbarArgs = ThemeManager.get_info("CTkScrollbar", theme_key, **kwargs)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

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

        # functionality
        self._command: Callable[[str, int | float, str], None] | None = command
        self._start_value: float = 0.0  # 0 to 1
        self._end_value: float = 1.0  # 0 to 1
        self._motion_center_offset: float = 0.0
        self._hover_state: bool = False

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._draw_engine = DrawEngine(self._canvas)

        self._create_bindings()
        self._draw()

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None:
            self._canvas.tag_bind("border_parts", "<Button-1>", self._clicked)
            self._canvas.tag_bind("scrollbar_parts", "<Button-1>", self._clicked_scrollbar)
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

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _get_scrollbar_values_for_minimum_pixel_size(self) -> tuple[float, float]:
        # correct scrollbar float values if scrollbar is too small
        if self._theme_info["orientation"] == "vertical":
            scrollbar_pixel_length = (self._end_value - self._start_value) * self._current_height
            if scrollbar_pixel_length < self._theme_info["minimum_pixel_length"] and -scrollbar_pixel_length + self._current_height != 0:
                # calculate how much to increase the float interval values so that the scrollbar width is self.minimum_pixel_length
                interval_extend_factor = (-scrollbar_pixel_length + self._theme_info["minimum_pixel_length"]) / (-scrollbar_pixel_length + self._current_height)
                corrected_end_value = self._end_value + (1 - self._end_value) * interval_extend_factor
                corrected_start_value = self._start_value - self._start_value * interval_extend_factor
                return corrected_start_value, corrected_end_value
            else:
                return self._start_value, self._end_value

        else:
            scrollbar_pixel_length = (self._end_value - self._start_value) * self._current_width
            if scrollbar_pixel_length < self._theme_info["minimum_pixel_length"] and -scrollbar_pixel_length + self._current_width != 0:
                # calculate how much to increase the float interval values so that the scrollbar width is self.minimum_pixel_length
                interval_extend_factor = (-scrollbar_pixel_length + self._theme_info["minimum_pixel_length"]) / (-scrollbar_pixel_length + self._current_width)
                corrected_end_value = self._end_value + (1 - self._end_value) * interval_extend_factor
                corrected_start_value = self._start_value - self._start_value * interval_extend_factor
                return corrected_start_value, corrected_end_value
            else:
                return self._start_value, self._end_value

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        corrected_start_value, corrected_end_value = self._get_scrollbar_values_for_minimum_pixel_size()
        requires_recoloring = self._draw_engine.draw_rounded_scrollbar(self._apply_widget_scaling(self._current_width),
                                                                       self._apply_widget_scaling(self._current_height),
                                                                       self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                       self._apply_widget_scaling(self._theme_info["border_spacing"]),
                                                                       corrected_start_value,
                                                                       corrected_end_value,
                                                                       self._theme_info["orientation"])

        if no_color_updates is False or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])

            if self._hover_state is True:
                self._canvas.itemconfig("scrollbar_parts",
                                        fill=self._apply_appearance_mode(self._theme_info["button_hover_color"]),
                                        outline=self._apply_appearance_mode(self._theme_info["button_hover_color"]))
            else:
                self._canvas.itemconfig("scrollbar_parts",
                                        fill=self._apply_appearance_mode(self._theme_info["button_color"]),
                                        outline=self._apply_appearance_mode(self._theme_info["button_color"]))

            if fg_color == "transparent":
                self._canvas.configure(bg=bg_color)
                self._canvas.itemconfig("border_parts", fill=bg_color, outline=bg_color)
            else:
                self._canvas.configure(bg=fg_color)
                self._canvas.itemconfig("border_parts", fill=fg_color, outline=fg_color)

        self._canvas.update_idletasks()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkScrollbarArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
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
        if self._theme_info["hover"] is True:
            self._hover_state = True
            self._canvas.itemconfig("scrollbar_parts",
                                    outline=self._apply_appearance_mode(self._theme_info["button_hover_color"]),
                                    fill=self._apply_appearance_mode(self._theme_info["button_hover_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._hover_state = False
        self._canvas.itemconfig("scrollbar_parts",
                                outline=self._apply_appearance_mode(self._theme_info["button_color"]),
                                fill=self._apply_appearance_mode(self._theme_info["button_color"]))

    def _clicked(self, event: tkinter.Event) -> None:
        self._motion_center_offset = 0.0
        self._on_motion(event)

    def _clicked_scrollbar(self, event: tkinter.Event) -> None:
        if self._theme_info["orientation"] == "vertical":
            value = self._reverse_widget_scaling(((event.y - self._theme_info["border_spacing"]) / (self._current_height - 2 * self._theme_info["border_spacing"])))
        else:
            value = self._reverse_widget_scaling(((event.x - self._theme_info["border_spacing"]) / (self._current_width - 2 * self._theme_info["border_spacing"])))
        center = self._start_value + ((self._end_value - self._start_value) * 0.5)
        self._motion_center_offset = center - value

    def _on_motion(self, event: tkinter.Event) -> None:
        if self._theme_info["orientation"] == "vertical":
            value = self._reverse_widget_scaling(((event.y - self._theme_info["border_spacing"]) / (self._current_height - 2 * self._theme_info["border_spacing"])))+self._motion_center_offset
        else:
            value = self._reverse_widget_scaling(((event.x - self._theme_info["border_spacing"]) / (self._current_width - 2 * self._theme_info["border_spacing"])))+self._motion_center_offset

        current_scrollbar_length = self._end_value - self._start_value
        value = max(current_scrollbar_length / 2, min(value, 1 - (current_scrollbar_length / 2)))
        self._start_value = value - (current_scrollbar_length / 2)
        self._end_value = value + (current_scrollbar_length / 2)
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

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Canvas, restores internal callbacks """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)  # unbind all callbacks for sequence
        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def focus(self) -> None:
        return self._canvas.focus()

    def focus_set(self) -> None:
        return self._canvas.focus_set()

    def focus_force(self) -> None:
        return self._canvas.focus_force()
