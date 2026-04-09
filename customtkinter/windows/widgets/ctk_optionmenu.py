from __future__ import annotations

import tkinter
import sys
import copy
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_widget_classes.dropdown_menu import DropdownMenu, DropdownMenuArgs
from .core_rendering import CTkCanvas, DrawEngine
from .font.ctk_font import CTkFont, CTkFontArgs
from .theme import ThemeManager


class CTkOptionMenuArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    button_color: str | tuple[str, str]
    button_hover_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    text_color_disabled: str | tuple[str, str]
    hover: bool
    dynamic_resizing: bool
    font: CTkFontArgs | CTkFont | tuple | str
    anchor: str  #center or combination of n, e, s, w
    dropdown: DropdownMenuArgs


class CTkOptionMenu(CTkBaseClass):
    """
    Optionmenu with rounded corners, dropdown menu, variable support, command.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 state: Literal["normal", "disabled"] = "normal",
                 values: list[str] | None = None,
                 variable: tkinter.StringVar | None = None,
                 command: Callable[[str], None] | None = None,
                 **kwargs: Unpack[CTkOptionMenuArgs]) -> None:

        self._theme_info: CTkOptionMenuArgs = ThemeManager.get_info("CTkOptionMenu", theme_key, **kwargs)

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
        self._command: Callable[[str], None] | None = command
        self._variable: tkinter.StringVar | None = variable
        self._variable_callback_blocked: bool = False
        self._variable_callback_name: str | None = None
        self._values: list[str] = ["CTkOptionMenu"] if values is None else values
        self._current_value: str = "CTkOptionMenu" if len(self._values) == 0 else self._values[0]

        self._dropdown_menu = DropdownMenu(master=self,
                                           values=self._values,
                                           command=self._dropdown_callback,
                                           **self._theme_info["dropdown"])
        self._close_on_next_click: bool = False

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._draw_engine = DrawEngine(self._canvas)

        self._text_label = tkinter.Label(master=self,
                                         font=self._apply_font_scaling(self._font),
                                         anchor=self._theme_info["anchor"],
                                         padx=0,
                                         pady=0,
                                         borderwidth=1,
                                         text=self._current_value)

        if self._cursor_manipulation_enabled:
            if sys.platform == "darwin":
                self.configure(cursor="pointinghand")
            elif sys.platform.startswith("win"):
                self.configure(cursor="hand2")

        self._create_grid()
        if not self._theme_info["dynamic_resizing"]:
            self.grid_propagate(False)

        self._create_bindings()
        self._draw()  # initial draw

        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._current_value = self._variable.get()
            self._text_label.configure(text=self._current_value)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<Button-1>":
            self._canvas.bind("<Button-1>", self._clicked)
            self._text_label.bind("<Button-1>", self._clicked)

    def _create_grid(self) -> None:
        self._canvas.grid(row=0, column=0, sticky="nsew")

        left_section_width = self._current_width - self._current_height
        self._text_label.grid(row=0, column=0, sticky="ew",
                              padx=(max(self._apply_widget_scaling(self._theme_info["corner_radius"]), self._apply_widget_scaling(3)),
                                    max(self._apply_widget_scaling(self._current_width - left_section_width + 3), self._apply_widget_scaling(3))))

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        # change label font size and grid padding
        self._text_label.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid()
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nsew")

    def destroy(self) -> None:
        if self._variable is not None:  # remove old callback
            self._variable.trace_remove("write", self._variable_callback_name)

        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        left_section_width = self._current_width - self._current_height
        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border_vertical_split(self._apply_widget_scaling(self._current_width),
                                                                                             self._apply_widget_scaling(self._current_height),
                                                                                             self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                                             0,
                                                                                             self._apply_widget_scaling(left_section_width))

        requires_recoloring_2 = self._draw_engine.draw_dropdown_arrow(self._apply_widget_scaling(self._current_width - (self._current_height / 2)),
                                                                      self._apply_widget_scaling(self._current_height / 2),
                                                                      self._apply_widget_scaling(self._current_height / 3))

        if no_color_updates is False or requires_recoloring or requires_recoloring_2:
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
            button_color = self._apply_appearance_mode(self._theme_info["button_color"])
            text_color = self._apply_appearance_mode(self._theme_info["text_color"])

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            self._canvas.itemconfig("inner_parts_left", outline=fg_color, fill=fg_color)
            self._canvas.itemconfig("inner_parts_right", outline=button_color, fill=button_color)

            self._text_label.configure(fg=text_color)

            if self._state == tkinter.DISABLED:
                self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
                self._canvas.itemconfig("dropdown_arrow",
                                        fill=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
            else:
                self._text_label.configure(fg=text_color)
                self._canvas.itemconfig("dropdown_arrow", fill=text_color)

            self._text_label.configure(bg=fg_color)

        self._canvas.update_idletasks()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkOptionMenuArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "button_color" in kwargs:
            self._theme_info["button_color"] = self._check_color_type(kwargs.pop("button_color"))
            require_redraw = True

        if "button_hover_color" in kwargs:
            self._theme_info["button_hover_color"] = self._check_color_type(kwargs.pop("button_hover_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "dropdown" in kwargs:
            self._dropdown_menu.configure(**kwargs.pop("dropdown"))

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._dropdown_menu.configure(values=self._values)

        if "variable" in kwargs:
            if self._variable is not None:  # remove old callback
                self._variable.trace_remove("write", self._variable_callback_name)
            self._variable = kwargs.pop("variable")
            if self._variable is not None and self._variable != "":
                self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
                self._current_value = self._variable.get()
                self._text_label.configure(text=self._current_value)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "dynamic_resizing" in kwargs:
            self._theme_info["dynamic_resizing"] = kwargs.pop("dynamic_resizing")
            if not self._theme_info["dynamic_resizing"]:
                self.grid_propagate(False)
            else:
                self.grid_propagate(True)

        if "anchor" in kwargs:
            self._text_label.configure(anchor=kwargs.pop("anchor"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("dropdown_"):
            return self._dropdown_menu.cget(attribute_name.removeprefix("dropdown_"))
        else:
            return super().cget(attribute_name)

    def _open_dropdown_menu(self) -> None:
        self._dropdown_menu.open(self.winfo_rootx(),
                                 self.winfo_rooty() + self._apply_widget_scaling(self._current_height + 0))
        self._close_on_next_click = True

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._close_on_next_click = self._dropdown_menu.is_open()
        if self._theme_info["hover"] is True and self._state == tkinter.NORMAL and len(self._values) > 0:
            # set color of inner button parts to hover color
            self._canvas.itemconfig("inner_parts_right",
                                    outline=self._apply_appearance_mode(self._theme_info["button_hover_color"]),
                                    fill=self._apply_appearance_mode(self._theme_info["button_hover_color"]))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        # set color of inner button parts
        self._canvas.itemconfig("inner_parts_right",
                                outline=self._apply_appearance_mode(self._theme_info["button_color"]),
                                fill=self._apply_appearance_mode(self._theme_info["button_color"]))

    def _variable_callback(self, *_: str) -> None:
        if not self._variable_callback_blocked:
            self._current_value = self._variable.get()
            self._text_label.configure(text=self._current_value)

    def _dropdown_callback(self, value: str) -> None:
        self._current_value = value
        self._text_label.configure(text=self._current_value)

        if self._variable is not None:
            self._variable_callback_blocked = True
            self._variable.set(self._current_value)
            self._variable_callback_blocked = False

        if self._command is not None:
            self._command(self._current_value)

    def set(self, value: str) -> None:
        self._current_value = value
        self._text_label.configure(text=self._current_value)

        if self._variable is not None:
            self._variable_callback_blocked = True
            self._variable.set(self._current_value)
            self._variable_callback_blocked = False

    def get(self) -> str:
        return self._current_value

    def index(self, value: str | None = None) -> int:
        """ returns index of selected value, raises ValueError if the value is missing
        if the parameter is provided, returns the associated index or raises ValueError if no value is found """
        if value is None:
            return self._values.index(self._current_value)
        else:
            return self._values.index(value)

    def _clicked(self, _: tkinter.Event | None = None) -> None:
        if self._close_on_next_click:
            self._dropdown_menu.close()
            self._close_on_next_click = False
        elif self._state is not tkinter.DISABLED and len(self._values) > 0:
            self._open_dropdown_menu()

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas and tkinter.Label"""
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
