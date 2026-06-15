from __future__ import annotations

import tkinter
from threading import Lock
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, Checkmark
from .font import CTkFont, FontType
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor


class CTkCheckBoxThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    checkbox_width: int
    checkbox_height: int
    corner_radius: int
    border_width: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color: ColorType
    border_color: ColorType
    checkmark_color: ColorType
    hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    hover: bool
    text: str
    font: FontType
    compound: Literal["left", "right", "top", "bottom"]

class CTkCheckBoxArgs(CTkCheckBoxThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    onvalue: int | float | str | bool
    offvalue: int | float | str | bool
    textvariable: tkinter.Variable | None
    variable: tkinter.Variable | None
    command: Callable[[], None] | None


class CTkCheckBox(CTkWidget):
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
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # text and font
        self._textvariable: tkinter.Variable | None = kwargs.pop("textvariable", None)
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._command: Callable[[], None] | None = kwargs.pop("command", None)
        self._check_state: bool = False
        self._onvalue: int | float | str | bool = kwargs.pop("onvalue", 1)
        self._offvalue: int | float | str | bool = kwargs.pop("offvalue", 0)
        self._variable: tkinter.Variable | None = kwargs.pop("variable", None)
        self._variable_callback_name: str | None = None
        self._block_value_propagation: Lock = Lock()

        self._bg_canvas = CTkCanvas(master=self,
                                    highlightthickness=0,
                                    width=self._apply_scaling(self._desired_width),
                                    height=self._apply_scaling(self._desired_height))
        self._bg_canvas.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nswe")

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._theme_info["checkbox_width"]),
                                 height=self._apply_scaling(self._theme_info["checkbox_height"]))
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._checkmark = Checkmark(self._canvas, events_transparent=True)
        self._bind_targets.append(self._canvas)

        self._text_label = tkinter.Label(master=self,
                                         bd=0,
                                         padx=0,
                                         pady=0,
                                         text=self._theme_info["text"],
                                         font=self._apply_font_scaling(self._font),
                                         textvariable=self._textvariable)
        self._bind_targets.append(self._text_label)
        self._focus_target = self._text_label

        # register variable callback and set state according to variable
        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._check_state = self._variable.get() == self._onvalue

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_bindings()
        self._set_cursor()
        self._update_geometry()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self.invoke)
            self._text_label.bind("<Button-1>", self.invoke)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._bg_canvas.configure(width=self._apply_scaling(self._desired_width),
                                  height=self._apply_scaling(self._desired_height))
        self._canvas.configure(width=self._apply_scaling(self._theme_info["checkbox_width"]),
                               height=self._apply_scaling(self._theme_info["checkbox_height"]))
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
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

    def destroy(self) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring = self._rounded_rect.update(self._apply_scaling(self._theme_info["checkbox_width"]),
                                                        self._apply_scaling(self._theme_info["checkbox_height"]),
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._check_state:
            if (self._checkmark.update(self._apply_scaling(self._theme_info["checkbox_width"] / 2),
                                       self._apply_scaling(self._theme_info["checkbox_height"] / 2),
                                       self._apply_scaling(self._theme_info["checkbox_height"] * 0.58)) or
                force_colors_update):
                self._checkmark.set_color(self._apply_appearance_mode(self._theme_info["checkmark_color"]))
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

    def _update_geometry(self) -> None:
        # configure grid system (1x3 or 3x1)

        if self._theme_info["text"] == "":
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure((1, 2), weight=0, minsize=0)
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure((1, 2), weight=0, minsize=0)
            self._canvas.grid(row=0, column=0)
            self._text_label.grid_forget()

        else:
            compound = self._theme_info["compound"]
            widget_label_spacing = self._apply_scaling(self._theme_info["internal_spacing"])

            if compound in ("left", "right"):
                self.grid_columnconfigure(0, weight=0 if compound == "left" else 1)
                self.grid_columnconfigure(1, weight=0, minsize=widget_label_spacing)
                self.grid_columnconfigure(2, weight=1 if compound == "left" else 0)
                self.grid_rowconfigure(0, weight=1)
                self.grid_rowconfigure((1, 2), weight=0, minsize=0)

                self._text_label.configure(justify=compound)
            else:
                self.grid_rowconfigure(0, weight=0 if compound == "top" else 1)
                self.grid_rowconfigure(1, weight=0, minsize=widget_label_spacing)
                self.grid_rowconfigure(2, weight=1 if compound == "top" else 0)
                self.grid_columnconfigure(0, weight=1)
                self.grid_columnconfigure((1, 2), weight=0, minsize=0)

                self._text_label.configure(justify=tkinter.CENTER)

            if compound == "left":
                self._canvas.grid(row=0, column=0, sticky="e")
                self._text_label.grid(row=0, column=2, sticky="w")
            elif compound == "right":
                self._text_label.grid(row=0, column=0, sticky="e")
                self._canvas.grid(row=0, column=2, sticky="w")
            elif compound == "top":
                self._canvas.grid(row=0, column=0, sticky="s")
                self._text_label.grid(row=2, column=0, sticky="n")
            else:
                self._text_label.grid(row=0, column=0, sticky="s")
                self._canvas.grid(row=2, column=0, sticky="n")

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkCheckBoxArgs]) -> None:
        require_new_state = False

        if "checkbox_width" in kwargs:
            self._theme_info["checkbox_width"] = kwargs.pop("checkbox_width")
            self._canvas.configure(width=self._apply_scaling(self._theme_info["checkbox_width"]))
            require_redraw = True

        if "checkbox_height" in kwargs:
            self._theme_info["checkbox_height"] = kwargs.pop("checkbox_height")
            self._canvas.configure(height=self._apply_scaling(self._theme_info["checkbox_height"]))
            require_redraw = True

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "internal_spacing" in kwargs:
            self._theme_info["internal_spacing"] = kwargs.pop("internal_spacing")
            self._update_geometry()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "checkmark_color" in kwargs:
            self._theme_info["checkmark_color"] = self._check_color_type(kwargs.pop("checkmark_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "text" in kwargs:
            self._theme_info["text"] = kwargs.pop("text")
            self._text_label.configure(text=self._theme_info["text"])
            self._update_geometry()

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            self._update_geometry()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
            require_new_state = True

        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")
            require_new_state = True

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None:
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                require_new_state = True

        if require_new_state and self._variable is not None:
            self._check_state = self._variable.get() == self._onvalue
            require_redraw = True
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
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _set_cursor(self) -> None:
        cursor = get_proper_cursor("normal" if self._state != tkinter.NORMAL else "clickable")
        if cursor is not None:
            self._canvas.configure(cursor=cursor)
            self._text_label.configure(cursor=cursor)

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

    def _variable_callback(self, *_: str) -> None:
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                if self._variable.get() == self._onvalue:
                    self.set(True)
                elif self._variable.get() == self._offvalue:
                    self.set(False)

    def set(self, state: bool) -> None:
        self._check_state = state
        self._draw(force_colors_update=True)

        if self._variable is not None and not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self._variable.set(self._onvalue if self._check_state else self._offvalue)

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """ Toggles the selection status if the widget is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        if self._state == tkinter.NORMAL:
            self.set(not self._check_state)

            if self._command is not None:
                self._command()

    def select(self) -> None:
        self.set(True)

    def deselect(self) -> None:
        self.set(False)

    def get(self) -> int | float | str | bool:
        return self._onvalue if self._check_state else self._offvalue
