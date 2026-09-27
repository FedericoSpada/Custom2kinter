from __future__ import annotations

import tkinter
import copy
from threading import Lock
from typing import Any, Callable
from typing_extensions import Literal, TypeAlias, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CanvasWithLabel
from .core_widget_classes.ctk_widget import CTkWidget, CTkWidgetArgs
from .core_rendering import BorderedRoundedRect, Arrow, Bar, Checkmark, RoundedRect, Star, Triangle
from .font import CTkFont, FontType
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors


SymbolType: TypeAlias = Literal["", "+", "x", "|", "/", "-", "\\", "^", ">", "v", "<",
                                "check", "circle", "rect", "play", "star"]


class CTkSymbolBoxThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    box_width: int
    box_height: int
    corner_radius: int
    border_width: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType | list[TransparentColorType]
    border_color: ColorType
    symbol_color: ColorType
    hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    hover: bool
    text: str
    font: FontType
    anchor: AnchorType
    justify: Literal["left", "center", "right"]
    compound: Literal["left", "right", "top", "bottom"]

class CTkSymbolBoxArgs(CTkSymbolBoxThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    values: list[SymbolType]
    textvariable: tkinter.StringVar | None
    variable: tkinter.StringVar | None
    pre_command: Callable[[int], Literal["break"] | None] | None
    command: Callable[[int], None] | None


class CTkSymbolBox(CTkWidget, CanvasWithLabel):
    """
    SymbolBox with rounded corners, border, variable support and hover effect.\n
    It can be seen as a "generalized CTkCheckBox" that displays a list of symbols in sequence.
    The user can advance in the list by clicking the widget with the left button,
    or they can go back with the right button.\n
    'fg_color' can be a list of colors which are used to color each symbol based on their index.\n
    Duplicates are accepted and properly managed. If 'values' contains just a single element,
    the widget behaves like a CTkButton when left-clicked.\n
    For detailed information check out the documentation.
    """

    #if set to True, first element is shown after the last,
    # otherwise user has to "scroll" in the opposite direction (Right-click)
    pacman_effect: bool = True

    animation_duration: int = 100  #[ms], set 0 to disable it

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkSymbolBoxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkSymbolBoxThemedArgs.__annotations__)
        self._theme_info: CTkSymbolBoxThemedArgs = ThemeManager.get_info("CTkSymbolBox", theme_key, **theme_args)

        #validity checks
        checked_fg_color = self._check_fg_color(self._theme_info.pop("fg_color"))
        check_colors(self._theme_info, CTkSymbolBoxThemedArgs)
        self._theme_info["fg_color"] = checked_fg_color

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=self._theme_info["width"],
                           height=self._theme_info["height"])

        # text and font
        self._textvariable: tkinter.StringVar | None = kwargs.pop("textvariable", None)
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_configure_callback(self._update_font)

        # functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._pre_command: Callable[[int], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[int], None] | None = kwargs.pop("command", None)
        self._variable: tkinter.Variable | None = kwargs.pop("variable", None)
        self._variable_callback_name: str | None = None
        self._block_value_propagation: Lock = Lock()
        self._values: list[str] = kwargs.pop("values", [])
        self._current_index: int = -1 if len(self._values) == 0 else 0
        self._current_value: SymbolType = "" if len(self._values) == 0 else self._values[0]
        self._click_animation_running: bool = False
        self._mouse_inside: bool = False

        CanvasWithLabel.__init__(self,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height),
                                 canvas_width=self._apply_scaling(self._theme_info["box_width"]),
                                 canvas_height=self._apply_scaling(self._theme_info["box_height"]))
        self._bind_targets.append(self._bg_canvas)

        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._arrow = Arrow(self._canvas, events_transparent=True)
        self._bar1 = Bar(self._canvas, events_transparent=True)
        self._bar2 = Bar(self._canvas, events_transparent=True)
        self._checkmark = Checkmark(self._canvas, events_transparent=True)
        self._rectcircle = RoundedRect(self._canvas, events_transparent=True)
        self._star = Star(self._canvas, events_transparent=True)
        self._triangle = Triangle(self._canvas, events_transparent=True)
        self._bind_targets.append(self._canvas)

        self._text_label.configure(text=self._theme_info["text"],
                                   font=self._apply_font_scaling(self._font),
                                   anchor=self._theme_info["anchor"],
                                   justify=self._theme_info["justify"],
                                   textvariable=self._textvariable)
        self._bind_targets.append(self._text_label)
        self._focus_target = self._text_label

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_bindings()
        self._set_cursor()
        self._update_geometry()
        self._draw(force_colors_update=True)

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback()

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<ButtonRelease-1>":
            self.bind("<ButtonRelease-1>", lambda _: self._on_release("top"))
        if sequence is None or sequence == "<ButtonRelease-3>":
            self.bind("<ButtonRelease-3>", lambda _: self._on_release("bottom"))

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._bg_canvas.configure(width=self._apply_scaling(self._desired_width),
                                  height=self._apply_scaling(self._desired_height))
        self._canvas.configure(width=self._apply_scaling(self._theme_info["box_width"]),
                               height=self._apply_scaling(self._theme_info["box_height"]))
        self._update_geometry()
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._bg_canvas.configure(width=self._apply_scaling(self._desired_width),
                                  height=self._apply_scaling(self._desired_height))

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._bg_canvas.grid_forget()
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nsew")

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring = self._rounded_rect.update(self._apply_scaling(self._theme_info["box_width"]),
                                                        self._apply_scaling(self._theme_info["box_height"]),
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        self._draw_symbol(force_colors_update)

        if force_colors_update or requires_recoloring:
            self._rounded_rect.raise_()
            self._arrow.raise_()
            self._bar1.raise_()
            self._bar2.raise_()
            self._checkmark.raise_()
            self._rectcircle.raise_()
            self._star.raise_()
            self._triangle.raise_()

            bg_color = self._apply_appearance_mode(self._bg_color)
            fg_color = self._get_fg_color()

            self._bg_canvas.configure(bg=bg_color)
            self._canvas.configure(bg=bg_color)

            if self._state != tkinter.NORMAL:
                disabled_color = self._apply_appearance_mode(self._theme_info["text_color_disabled"])
                main_color = disabled_color if fg_color != "transparent" else bg_color
                border_color = disabled_color
                text_color = disabled_color
            else:
                text_color = self._apply_appearance_mode(self._theme_info["text_color"])
                if fg_color != "transparent":
                    main_color = border_color = self._apply_appearance_mode(fg_color)
                else:
                    main_color = bg_color
                    border_color = self._apply_appearance_mode(self._theme_info["border_color"])

            self._rounded_rect.set_main_color(main_color)
            self._rounded_rect.set_border_color(border_color)
            self._text_label.configure(fg=text_color, bg=bg_color)

    def _draw_symbol(self, force_colors_update: bool) -> None:
        width = self._apply_scaling(self._theme_info["box_width"])
        height = self._apply_scaling(self._theme_info["box_height"])
        color = self._apply_appearance_mode(self._theme_info["symbol_color"])

        if self._current_value == "+":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 0) or force_colors_update:
                self._bar1.set_color(color)
            if self._bar2.update(width / 2, height / 2, height * 0.6, 90) or force_colors_update:
                self._bar2.set_color(color)
        elif self._current_value == "x":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 45) or force_colors_update:
                self._bar1.set_color(color)
            if self._bar2.update(width / 2, height / 2, height * 0.6, -45) or force_colors_update:
                self._bar2.set_color(color)
        elif self._current_value == "|":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 0) or force_colors_update:
                self._bar1.set_color(color)
        elif self._current_value == "/":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 45) or force_colors_update:
                self._bar1.set_color(color)
        elif self._current_value == "-":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 90) or force_colors_update:
                self._bar1.set_color(color)
        elif self._current_value == "\\":
            if self._bar1.update(width / 2, height / 2, height * 0.6, 135) or force_colors_update:
                self._bar1.set_color(color)
        elif self._current_value == "^":
            if self._arrow.update(width / 2, height / 2, height * 0.6, 0) or force_colors_update:
                self._arrow.set_color(color)
        elif self._current_value == ">":
            if self._arrow.update(width / 2, height / 2, height * 0.6, 90) or force_colors_update:
                self._arrow.set_color(color)
        elif self._current_value == "v":
            if self._arrow.update(width / 2, height / 2, height * 0.6, 180) or force_colors_update:
                self._arrow.set_color(color)
        elif self._current_value == "<":
            if self._arrow.update(width / 2, height / 2, height * 0.6, 270) or force_colors_update:
                self._arrow.set_color(color)
        elif self._current_value == "check":
            if self._checkmark.update(width / 2, height / 2, height * 0.6) or force_colors_update:
                self._checkmark.set_color(color)
        elif self._current_value == "circle":
            if self._rectcircle.update(width * 0.275, height * 0.275, width * 0.45, height * 0.45, 1e12) or force_colors_update:
                self._rectcircle.set_color(color)
        elif self._current_value == "rect":
            if self._rectcircle.update(width * 0.275, height * 0.275, width * 0.45, height * 0.45, 0) or force_colors_update:
                self._rectcircle.set_color(color)
        elif self._current_value == "play":
            if self._triangle.update(width / 2, height / 2, height / 2, 90) or force_colors_update:
                self._triangle.set_color(color)
        elif self._current_value == "star":
            if self._star.update(width / 2, height * 0.47, height * 0.6) or force_colors_update:
                self._star.set_color(color)

        if self._current_value not in ("^", ">", "v", "<"):
            self._arrow.delete()
        if self._current_value not in ("+", "x", "|", "/", "-", "\\"):
            self._bar1.delete()
        if self._current_value not in ("+", "x"):
            self._bar2.delete()
        if self._current_value != "check":
            self._checkmark.delete()
        if self._current_value not in ("circle", "rect"):
            self._rectcircle.delete()
        if self._current_value != "play":
            self._triangle.delete()
        if self._current_value not in ("star", "plane"):
            self._star.delete()

    def _check_fg_color(self, fg_color: TransparentColorType | list[TransparentColorType]) -> list[TransparentColorType]:
        #force fg_color to be a list
        if isinstance(fg_color, (str, tuple)):
            fg_color = [fg_color]
        else:
            #it can be ambiguous only if it contains exactly 2 elements,
            # which is usually done to specify a different color based on the appearance mode
            if len(fg_color) == 2:
                #if at least one element is itself a list or tuple, the provided value is already a list of colors
                for elem in fg_color:
                    if isinstance(elem, (list, tuple)):
                        break
                #otherwise, we treat it like a single color that changes based on the mode
                else:
                    fg_color = [fg_color]
        return fg_color

    def _get_fg_color(self) -> TransparentColorType:
        fg_colors = self._theme_info["fg_color"]

        #if "no symbol" is active, use transparent color in case just one color has been provided for all symbols
        if self._current_value == "" and len(fg_colors) == 1:
            color = "transparent"
        else:
            color = fg_colors[max(0, min(self._current_index, len(fg_colors) - 1))]
        return color

    def _update_geometry(self, *_: Any) -> None:
        super()._update_geometry(self._theme_info["compound"],
                                 self._apply_scaling(self._theme_info["internal_spacing"]))

    def _set_cursor(self, *_: Any) -> None:
        super()._set_cursor("normal" if self._state != tkinter.NORMAL else "clickable")

    def _variable_callback(self, *_: str) -> None:
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self.set(self._variable.get())

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = True
        if self._theme_info["hover"] and self._state == tkinter.NORMAL:
            hover_color = self._apply_appearance_mode(self._theme_info["hover_color"])

            self._rounded_rect.set_main_color(hover_color)
            if self._get_fg_color() != "transparent":
                self._rounded_rect.set_border_color(hover_color)

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = False
        self._click_animation_running = False

        if self._state == tkinter.NORMAL:
            fg_color = self._get_fg_color()
            if fg_color != "transparent":
                fg_color = self._apply_appearance_mode(fg_color)
                self._rounded_rect.set_main_color(fg_color)
                self._rounded_rect.set_border_color(fg_color)
            else:
                self._rounded_rect.set_main_color(self._apply_appearance_mode(self._bg_color))
                self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))

    def _click_animation(self) -> None:
        if self._click_animation_running:
            self._on_enter()

    def _on_release(self, direction: Literal["top", "bottom"]) -> None:
        if self._mouse_inside and self._state == tkinter.NORMAL:
            #if the number of symbols is exactly one, we treat this widget as if it were a CTkButton
            if len(self._values) == 1:
                if direction == "top":
                    if self.animation_duration > 0:
                        # change color with .on_leave() and back to normal after some time with click_animation()
                        self._on_leave()
                        self._click_animation_running = True
                        self.after(self.animation_duration, self._click_animation)
                    self.invoke(direction)
            else:
                self.invoke(direction)

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        self._font.remove_configure_callback(self._update_font)
        super().destroy()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkSymbolBoxArgs]) -> None:
        require_geometry = False

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_fg_color(kwargs.pop("fg_color"))
            require_redraw = True

        check_colors(kwargs, CTkSymbolBoxThemedArgs)

        if "box_width" in kwargs:
            self._theme_info["box_width"] = kwargs.pop("box_width")
            self._canvas.configure(width=self._apply_scaling(self._theme_info["box_width"]))
            require_redraw = True

        if "box_height" in kwargs:
            self._theme_info["box_height"] = kwargs.pop("box_height")
            self._canvas.configure(height=self._apply_scaling(self._theme_info["box_height"]))
            require_redraw = True

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "internal_spacing" in kwargs:
            self._theme_info["internal_spacing"] = kwargs.pop("internal_spacing")
            require_geometry = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = kwargs.pop("border_color")
            require_redraw = True

        if "symbol_color" in kwargs:
            self._theme_info["symbol_color"] = kwargs.pop("symbol_color")
            require_redraw = True

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = kwargs.pop("hover_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = kwargs.pop("text_color")
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = kwargs.pop("text_color_disabled")
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "text" in kwargs:
            self._theme_info["text"] = kwargs.pop("text")
            self._text_label.configure(text=self._theme_info["text"])
            require_geometry = True

        if "font" in kwargs:
            self._font.remove_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_configure_callback(self._update_font)
            self._update_font()

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._text_label.configure(anchor=self._theme_info["anchor"])

        if "justify" in kwargs:
            self._theme_info["justify"] = kwargs.pop("justify")
            self._text_label.configure(justify=self._theme_info["justify"])

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            require_geometry = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            try:
                self._current_index = self._values.index(self._current_value)
            except ValueError:
                self._current_index = -1
            require_redraw = True

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)
            require_geometry = True

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

        if require_geometry:
            self._update_geometry()
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info and attribute_name not in CTkWidgetArgs.__annotations__:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def set(self, value: SymbolType | None = None, index: int | None = None) -> None:
        """ Changes the content to the desired value or index,
        regardless of the widget's state and admissible values. """
        if value is not None:
            self._current_value = value
            try:
                self._current_index = self._values.index(value)
            except ValueError:
                self._current_index = -1
        elif index is not None:
            self._current_index = index
            self._current_value = self._values[index]
        self._draw(force_colors_update=True)

        if self._variable is not None and not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self._variable.set(self._current_value)

    def invoke(self, direction: Literal["top", "bottom"]) -> None:
        """ If the widget is not disabled, changes the active symbol by showing
        the next or previous one with respect to the currently active symbol.\n
        Can be called to simulate the user who clicks on the widget. """
        if self._state == tkinter.NORMAL:
            new_index = self._current_index + (1 if direction == "top" else -1)
            if self.pacman_effect and self._values:
                new_index = new_index % len(self._values)
            else:
                new_index = max(0, min(new_index, len(self._values) - 1))

            retval = "" if self._pre_command is None else self._pre_command(new_index)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                self.set(index=new_index)

                if self._command is not None:
                    self._command(new_index)

    def get(self, index: int | None = None) -> SymbolType:
        """ Returns the current selected symbol.\n
        If an index is provided, returns the symbol in that position. """
        if index is None:
            return self._current_value
        else:
            return self._values[index]

    def index(self, value: SymbolType | None = None) -> int:
        """ Returns index of active symbol, raises ValueError if the symbol is missing.\n
        If the parameter is provided, returns the associated index or raises ValueError if the symbol is not found. """
        if value is None:
            if self._current_index < 0:
                raise ValueError(f"Symbol '{self._current_value}' not in 'values' list")
            return self._current_index
        else:
            return self._values.index(value)
