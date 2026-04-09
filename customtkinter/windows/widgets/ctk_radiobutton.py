from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .font.ctk_font import CTkFont, CTkFontArgs
from .theme import ThemeManager


class CTkRadioButtonArgs(TypedDict, total=False):
    width: int
    height: int
    radiobutton_width: int
    radiobutton_height: int
    corner_radius: int
    border_width_checked: int
    border_width_unchecked: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    text_color_disabled: str | tuple[str, str]
    hover_color: str | tuple[str, str]
    hover: bool
    text: str
    font: CTkFontArgs | CTkFont | tuple | str


class CTkRadioButton(CTkBaseClass):
    """
    Radiobutton with rounded corners, border, label, variable support, command.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 textvariable: tkinter.StringVar | None = None,
                 state: Literal["normal", "disabled"] = "normal",
                 value: int | float | str | bool = 0,
                 variable: tkinter.Variable | None = None,
                 command: Callable[[], None] | None = None,
                 **kwargs: Unpack[CTkRadioButtonArgs]) -> None:

        self._theme_info: CTkRadioButtonArgs = ThemeManager.get_info("CTkRadioButton", theme_key, **kwargs)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key == "bg_color")

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # functionality
        self._state: Literal["normal", "disabled"] = state
        self._command: Callable[[], None] | None = command
        self._value: int | float | str | bool = value
        self._textvariable: tkinter.StringVar | None = textvariable
        self._variable: tkinter.Variable | None = variable
        self._variable_callback_name: str | None = None
        self._variable_callback_blocked: bool = False
        self._check_state: bool = False

        # configure grid system (3x1)
        self.grid_columnconfigure(0, weight=0)
        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(6))
        self.grid_columnconfigure(2, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self._bg_canvas = CTkCanvas(master=self,
                                    highlightthickness=0,
                                    width=self._apply_widget_scaling(self._current_width),
                                    height=self._apply_widget_scaling(self._current_height))
        self._bg_canvas.grid(row=0, column=0, columnspan=3, sticky="nswe")

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._theme_info["radiobutton_width"]),
                                 height=self._apply_widget_scaling(self._theme_info["radiobutton_height"]))
        self._canvas.grid(row=0, column=0)
        self._draw_engine = DrawEngine(self._canvas)

        self._text_label = tkinter.Label(master=self,
                                         bd=0,
                                         padx=0,
                                         pady=0,
                                         text=self._theme_info["text"],
                                         justify=tkinter.LEFT,
                                         font=self._apply_font_scaling(self._font),
                                         textvariable=self._textvariable)
        self._text_label.grid(row=0, column=2, sticky="w")
        self._text_label["anchor"] = "w"

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._check_state = self._variable.get() == self._value

        self._create_bindings()
        self._set_cursor()
        self._draw()

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

        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(6))
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))
        self._canvas.configure(width=self._apply_widget_scaling(self._theme_info["radiobutton_width"]),
                               height=self._apply_widget_scaling(self._theme_info["radiobutton_height"]))
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._bg_canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                                  height=self._apply_widget_scaling(self._desired_height))

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

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        if self._check_state is True:
            requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._theme_info["radiobutton_width"]),
                                                                                  self._apply_widget_scaling(self._theme_info["radiobutton_height"]),
                                                                                  self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                                  self._apply_widget_scaling(self._theme_info["border_width_checked"]))
        else:
            requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._theme_info["radiobutton_width"]),
                                                                                  self._apply_widget_scaling(self._theme_info["radiobutton_height"]),
                                                                                  self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                                  self._apply_widget_scaling(self._theme_info["border_width_unchecked"]))

        if no_color_updates is False or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)

            self._bg_canvas.configure(bg=bg_color)
            self._canvas.configure(bg=bg_color)

            if self._check_state is False:
                self._canvas.itemconfig("border_parts",
                                        outline=self._apply_appearance_mode(self._theme_info["border_color"]),
                                        fill=self._apply_appearance_mode(self._theme_info["border_color"]))
            else:
                self._canvas.itemconfig("border_parts",
                                        outline=self._apply_appearance_mode(self._theme_info["fg_color"]),
                                        fill=self._apply_appearance_mode(self._theme_info["fg_color"]))

            self._canvas.itemconfig("inner_parts", outline=bg_color, fill=bg_color)

            if self._state == tkinter.DISABLED:
                self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
            else:
                self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]))

            self._text_label.configure(bg=bg_color)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkRadioButtonArgs]) -> None:
        require_new_state = False

        if "radiobutton_width" in kwargs:
            self._theme_info["radiobutton_width"] = kwargs.pop("radiobutton_width")
            self._canvas.configure(width=self._apply_widget_scaling(self._theme_info["radiobutton_width"]))
            require_redraw = True

        if "radiobutton_height" in kwargs:
            self._theme_info["radiobutton_height"] = kwargs.pop("radiobutton_height")
            self._canvas.configure(height=self._apply_widget_scaling(self._theme_info["radiobutton_height"]))
            require_redraw = True

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width_unchecked" in kwargs:
            self._theme_info["border_width_unchecked"] = kwargs.pop("border_width_unchecked")
            require_redraw = True

        if "border_width_checked" in kwargs:
            self._theme_info["border_width_checked"] = kwargs.pop("border_width_checked")
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = self._check_color_type(kwargs.pop("hover_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
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

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)

        if "variable" in kwargs:
            if self._variable is not None:
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                require_new_state = True

        if "value" in kwargs:
            self._value = kwargs.pop("value")
            require_new_state = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if require_new_state and self._variable is not None and self._variable != "":
            self._check_state = True if self._variable.get() == self._value else False
            require_redraw = True
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "value":
            return self._value
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _set_cursor(self) -> None:
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="arrow")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="arrow")

            elif self._state == tkinter.NORMAL:
                if sys.platform == "darwin":
                    self._canvas.configure(cursor="pointinghand")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="pointinghand")
                elif sys.platform.startswith("win"):
                    self._canvas.configure(cursor="hand2")
                    if self._text_label is not None:
                        self._text_label.configure(cursor="hand2")

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        if self._theme_info["hover"] is True and self._state == tkinter.NORMAL:
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["hover_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["hover_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        if self._check_state is True:
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["fg_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["fg_color"]))
        else:
            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["border_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["border_color"]))

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            if self._variable.get() == self._value:
                self.select(from_variable_callback=True)
            else:
                self.deselect(from_variable_callback=True)

    def set(self, state: bool, from_variable_callback: bool = False) -> None:
        self._check_state = state
        self._draw()

        if self._variable is not None and not from_variable_callback:
            self._variable_callback_blocked = True
            self._variable.set(self._value if self._check_state else "")
            self._variable_callback_blocked = False

    def invoke(self, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            if self._check_state is False:
                self.select()

            if self._command is not None:
                self._command()

    def select(self, from_variable_callback: bool = False) -> None:
        self.set(True, from_variable_callback)

    def deselect(self, from_variable_callback: bool = False) -> None:
        self.set(False, from_variable_callback)

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas and tkinter.Label """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, func, add=True)
        self._text_label.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
        self._text_label.unbind(sequence, None)
        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def focus(self) -> None:
        return self._text_label.focus()

    def focus_set(self) -> None:
        return self._text_label.focus_set()

    def focus_force(self) -> None:
        return self._text_label.focus_force()
