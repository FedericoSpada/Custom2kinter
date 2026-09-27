from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkToggleable, CanvasWithLabel
from .core_widget_classes.ctk_widget import CTkWidget, CTkWidgetArgs
from .core_rendering import BorderedRoundedRect, Checkmark
from .font import CTkFont, FontType
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors


class CTkCheckBoxThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    box_width: int
    box_height: int
    corner_radius: int
    border_width: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color: ColorType
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

class CTkCheckBoxArgs(CTkCheckBoxThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    onvalue: int | float | str | bool
    offvalue: int | float | str | bool
    textvariable: tkinter.StringVar | None
    variable: tkinter.Variable | None
    pre_command: Callable[[int | float | str | bool], Literal["break"] | None] | None
    command: Callable[[int | float | str | bool], None] | None


class CTkCheckBox(CTkWidget, CTkToggleable, CanvasWithLabel):
    """
    Checkbox with rounded corners, border, variable support and hover effect.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkCheckBoxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkCheckBoxThemedArgs.__annotations__)
        self._theme_info: CTkCheckBoxThemedArgs = ThemeManager.get_info("CTkCheckBox", theme_key, **theme_args)

        #validity checks
        check_colors(self._theme_info, CTkCheckBoxThemedArgs)

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=self._theme_info["width"],
                           height=self._theme_info["height"])
        CTkToggleable.__init__(self)

        # text and font
        self._textvariable: tkinter.StringVar | None = kwargs.pop("textvariable", None)
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_configure_callback(self._update_font)

        # functionality
        self._state = kwargs.pop("state", tkinter.NORMAL)
        self._pre_command = kwargs.pop("pre_command", None)
        self._command = kwargs.pop("command", None)
        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")

        CanvasWithLabel.__init__(self,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height),
                                 canvas_width=self._apply_scaling(self._theme_info["box_width"]),
                                 canvas_height=self._apply_scaling(self._theme_info["box_height"]))
        self._bind_targets.append(self._bg_canvas)

        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._checkmark = Checkmark(self._canvas, events_transparent=True)
        self._bind_targets.append(self._canvas)

        self._text_label.configure(text=self._theme_info["text"],
                                   font=self._apply_font_scaling(self._font),
                                   anchor=self._theme_info["anchor"],
                                   justify=self._theme_info["justify"],
                                   textvariable=self._textvariable)
        self._bind_targets.append(self._text_label)
        self._focus_target = self._text_label

        self._create_bindings()
        self._set_cursor()
        self._update_geometry()
        self._draw(force_colors_update=True)
        self._update_variable(kwargs.pop("variable", None))

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self.bind("<Button-1>", self.invoke)

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

        width = self._apply_scaling(self._theme_info["box_width"])
        height = self._apply_scaling(self._theme_info["box_height"])

        requires_recoloring = self._rounded_rect.update(width,
                                                        height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._check_state:
            if self._checkmark.update(width / 2, height / 2, height * 0.6) or force_colors_update:
                self._checkmark.set_color(self._apply_appearance_mode(self._theme_info["symbol_color"]))
        else:
            self._checkmark.delete()

        if force_colors_update or requires_recoloring:
            self._rounded_rect.raise_()
            self._checkmark.raise_()

            bg_color = self._apply_appearance_mode(self._bg_color)

            self._bg_canvas.configure(bg=bg_color)
            self._canvas.configure(bg=bg_color)

            if self._state != tkinter.NORMAL:
                disabled_color = self._apply_appearance_mode(self._theme_info["text_color_disabled"])
                main_color = disabled_color if self._check_state else bg_color
                border_color = disabled_color
                text_color = disabled_color
            else:
                text_color = self._apply_appearance_mode(self._theme_info["text_color"])
                if self._check_state:
                    main_color = border_color = self._apply_appearance_mode(self._theme_info["fg_color"])
                else:
                    main_color = bg_color
                    border_color = self._apply_appearance_mode(self._theme_info["border_color"])

            self._rounded_rect.set_main_color(main_color)
            self._rounded_rect.set_border_color(border_color)
            self._text_label.configure(fg=text_color, bg=bg_color)

    def _update_geometry(self, *_: Any) -> None:
        super()._update_geometry(self._theme_info["compound"],
                                 self._apply_scaling(self._theme_info["internal_spacing"]))

    def _set_cursor(self, *_: Any) -> None:
        super()._set_cursor("normal" if self._state != tkinter.NORMAL else "clickable")

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        if self._theme_info["hover"] and self._state == tkinter.NORMAL:
            hover_color = self._apply_appearance_mode(self._theme_info["hover_color"])

            self._rounded_rect.set_main_color(hover_color)
            if self._check_state:
                self._rounded_rect.set_border_color(hover_color)

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            if self._check_state:
                fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
                self._rounded_rect.set_main_color(fg_color)
                self._rounded_rect.set_border_color(fg_color)
            else:
                self._rounded_rect.set_main_color(self._apply_appearance_mode(self._bg_color))
                self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))

    def destroy(self) -> None:
        self._font.remove_configure_callback(self._update_font)
        CTkToggleable.destroy(self)
        CTkWidget.destroy(self)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkCheckBoxArgs]) -> None:
        require_new_state = False
        require_geometry = False

        check_colors(kwargs, CTkCheckBoxThemedArgs)

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

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = kwargs.pop("fg_color")
            require_redraw = True

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = kwargs.pop("hover_color")
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = kwargs.pop("border_color")
            require_redraw = True

        if "symbol_color" in kwargs:
            self._theme_info["symbol_color"] = kwargs.pop("symbol_color")
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = kwargs.pop("text_color")
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = kwargs.pop("text_color_disabled")
            require_redraw = True

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

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)
            require_geometry = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
            require_new_state = True

        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")
            require_new_state = True

        if "variable" in kwargs:
            self._update_variable(kwargs.pop("variable"))
            require_new_state = False  #already changed in _update_variable()

        if require_new_state and self._variable is not None:
            self._check_state = self._variable.get() == self._onvalue
            require_redraw = True
        if require_geometry:
            self._update_geometry()
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "onvalue":
            return self._onvalue
        elif attribute_name == "offvalue":
            return self._offvalue
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

    def set(self, value: int | float | str | bool | None = None, state: bool | None = None) -> None:
        super().set(value, state)
        self._draw(force_colors_update=True)
