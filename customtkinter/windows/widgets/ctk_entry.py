from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .font.ctk_font import CTkFont, CTkFontArgs
from .theme import ThemeManager
from .utility import pop_from_dict_by_set


class CTkEntryArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    placeholder_text_color: str | tuple[str, str]
    placeholder_text: str
    font: CTkFontArgs | CTkFont | tuple | str


class CTkEntry(CTkBaseClass):
    """
    Entry with rounded corners, border, textvariable support, focus and placeholder.
    For detailed information check out the documentation.
    """

    _minimum_x_padding: int = 6  # minimum padding between tkinter entry and frame border

    # attributes that are passed to and managed by the tkinter entry only:
    _valid_tk_entry_attributes: set[str] = {"exportselection", "insertborderwidth", "insertofftime",
                                            "insertontime", "insertwidth", "justify", "selectborderwidth",
                                            "show", "takefocus", "validate", "validatecommand", "xscrollcommand"}

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 textvariable: tkinter.StringVar | None = None,
                 state: Literal["normal", "disabled", "readonly"] = "normal",
                 **kwargs: Unpack[CTkEntryArgs]) -> None:

        entry_kwargs = pop_from_dict_by_set(kwargs, self._valid_tk_entry_attributes)

        self._theme_info: CTkEntryArgs = ThemeManager.get_info("CTkEntry", theme_key, **kwargs)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

        # transfer basic functionality (bg_color, size, appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # functionality
        self._state: Literal["normal", "disabled", "readonly"] = state
        self._textvariable: tkinter.StringVar | None = textvariable
        self._textvariable_callback_name: str = ""
        self._is_focused: bool = True
        self._placeholder_text_active: bool = False
        self._pre_placeholder_arguments: dict[str, Any] = {}  # some set arguments of the entry will be changed for placeholder and then set back

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        if self._textvariable is not None and self._textvariable != "":
            self._textvariable_callback_name = self._textvariable.trace_add("write", self._textvariable_callback)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._draw_engine = DrawEngine(self._canvas)

        self._entry = tkinter.Entry(master=self,
                                    bd=0,
                                    width=1,
                                    highlightthickness=0,
                                    font=self._apply_font_scaling(self._font),
                                    state=self._state,
                                    textvariable=self._textvariable,
                                    **entry_kwargs)

        self._create_grid()
        self._activate_placeholder()
        self._create_bindings()
        self._draw()

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<FocusIn>":
            self._entry.bind("<FocusIn>", self._entry_focus_in)
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", self._entry_focus_out)

    def _create_grid(self) -> None:
        self._canvas.grid(column=0, row=0, sticky="nswe")

        if self._theme_info["corner_radius"] >= self._minimum_x_padding:
            self._entry.grid(column=0, row=0, sticky="nswe",
                             padx=min(self._apply_widget_scaling(self._theme_info["corner_radius"]), round(self._apply_widget_scaling(self._current_height/2))),
                             pady=(self._apply_widget_scaling(self._theme_info["border_width"]), self._apply_widget_scaling(self._theme_info["border_width"] + 1)))
        else:
            self._entry.grid(column=0, row=0, sticky="nswe",
                             padx=self._apply_widget_scaling(self._minimum_x_padding),
                             pady=(self._apply_widget_scaling(self._theme_info["border_width"]), self._apply_widget_scaling(self._theme_info["border_width"] + 1)))

    def _textvariable_callback(self, *_: str) -> None:
        if self._textvariable.get() == "":
            self._activate_placeholder()

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width), height=self._apply_widget_scaling(self._desired_height))
        self._create_grid()
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._entry.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(column=0, row=0, sticky="nswe")

    def destroy(self) -> None:
        if self._textvariable is not None:
            self._textvariable.trace_remove("write", self._textvariable_callback_name)

        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                              self._apply_widget_scaling(self._theme_info["border_width"]))

        if requires_recoloring or no_color_updates is False:
            bg_color = self._apply_appearance_mode(self._bg_color)
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
            border_color = self._apply_appearance_mode(self._theme_info["border_color"])
            if self._placeholder_text_active:
                text_color = self._apply_appearance_mode(self._theme_info["placeholder_text_color"])
            else:
                text_color = self._apply_appearance_mode(self._theme_info["text_color"])

            self._canvas.configure(bg=bg_color)

            if fg_color == "transparent":
                self._canvas.itemconfig("inner_parts", fill=bg_color, outline=bg_color)
                self._entry.configure(bg=bg_color, disabledbackground=bg_color, readonlybackground=bg_color, highlightcolor=bg_color)
            else:
                self._canvas.itemconfig("inner_parts", fill=fg_color, outline=fg_color)
                self._entry.configure(bg=fg_color, disabledbackground=fg_color, readonlybackground=fg_color, highlightcolor=fg_color)

            self._canvas.itemconfig("border_parts", fill=border_color, outline=border_color)
            self._entry.config(fg=text_color, disabledforeground=text_color, insertbackground=text_color)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkEntryArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            self._create_grid()
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"))
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "placeholder_text_color" in kwargs:
            self._theme_info["placeholder_text_color"] = self._check_color_type(kwargs.pop("placeholder_text_color"))
            require_redraw = True

        if "textvariable" in kwargs:
            if self._textvariable is not None and self._textvariable != "":
                self._textvariable.trace_remove("write", self._textvariable_callback_name)  # remove old variable callback
            self._textvariable = kwargs.pop("textvariable")
            self._entry.configure(textvariable=self._textvariable)
            if self._textvariable is not None and self._textvariable != "":
                self._textvariable_callback_name = self._textvariable.trace_add("write", self._textvariable_callback)

        if "placeholder_text" in kwargs:
            self._theme_info["placeholder_text"] = kwargs.pop("placeholder_text")
            if self._placeholder_text_active:
                self._entry.delete(0, tkinter.END)
                self._entry.insert(0, self._theme_info["placeholder_text"])
            else:
                self._activate_placeholder()

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._entry.configure(state=self._state)

        if "show" in kwargs:
            if self._placeholder_text_active:
                self._pre_placeholder_arguments["show"] = kwargs.pop("show")  # remember show argument for when placeholder gets deactivated
            else:
                self._entry.configure(show=kwargs.pop("show"))

        self._entry.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_entry_attributes))  # configure Tkinter.Entry
        super().configure(require_redraw=require_redraw, **kwargs)  # configure CTkBaseClass

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "state":
            return self._state
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name in self._valid_tk_entry_attributes:
            return self._entry.cget(attribute_name)  # cget of tkinter.Entry
        else:
            return super().cget(attribute_name)  # cget of CTkBaseClass

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Entry """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._entry.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Entry """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._entry.unbind(sequence, None)  # unbind all callbacks for sequence
        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def _activate_placeholder(self) -> None:
        if self._entry.get() == "" and self._theme_info["placeholder_text"] is not None and (self._textvariable is None or self._textvariable == ""):
            self._placeholder_text_active = True

            self._pre_placeholder_arguments = {"show": self._entry.cget("show")}
            self._entry.config(fg=self._apply_appearance_mode(self._theme_info["placeholder_text_color"]),
                               disabledforeground=self._apply_appearance_mode(self._theme_info["placeholder_text_color"]),
                               show="")
            self._entry.delete(0, tkinter.END)
            self._entry.insert(0, self._theme_info["placeholder_text"])

    def _deactivate_placeholder(self) -> None:
        if self._placeholder_text_active and self._entry.cget("state") != "readonly":
            self._placeholder_text_active = False

            self._entry.config(fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                               disabledforeground=self._apply_appearance_mode(self._theme_info["text_color"]),)
            self._entry.delete(0, tkinter.END)
            for argument, value in self._pre_placeholder_arguments.items():
                self._entry[argument] = value

    def _entry_focus_out(self, _: tkinter.Event | None = None) -> None:
        self._activate_placeholder()
        self._is_focused = False

    def _entry_focus_in(self, _: tkinter.Event | None = None) -> None:
        self._deactivate_placeholder()
        self._is_focused = True

    def delete(self, first_index: str | int, last_index: str | int | None = None) -> None:
        self._entry.delete(first_index, last_index)

        if not self._is_focused and self._entry.get() == "":
            self._activate_placeholder()

    def insert(self, index: str | int, string: str) -> None:
        self._deactivate_placeholder()

        return self._entry.insert(index, string)

    def set(self, string: str) -> None:
        self._entry.delete(0, tkinter.END)
        self.insert(0, string)

    def get(self) -> str:
        if self._placeholder_text_active:
            return ""
        else:
            return self._entry.get()

    def focus(self) -> None:
        return self._entry.focus()

    def focus_set(self) -> None:
        return self._entry.focus_set()

    def focus_force(self) -> None:
        return self._entry.focus_force()

    def index(self, index: str | int) -> int:
        return self._entry.index(index)

    def icursor(self, index: str | int) -> None:
        return self._entry.icursor(index)

    def select_adjust(self, index: str | int) -> None:
        return self._entry.select_adjust(index)

    def selection_adjust(self, index: str | int) -> None:
        return self._entry.selection_adjust(index)

    def select_from(self, index: str | int) -> None:
        return self._entry.select_from(index)

    def selection_from(self, index: str | int) -> None:
        return self._entry.selection_from(index)

    def select_clear(self) -> None:
        return self._entry.select_clear()

    def selection_clear(self) -> None:
        return self._entry.selection_clear()

    def select_present(self) -> bool:
        return self._entry.select_present()

    def selection_present(self) -> bool:
        return self._entry.selection_present()

    def select_range(self, start: str | int, end: str | int) -> None:
        return self._entry.select_range(start, end)

    def selection_range(self, start: str | int, end: str | int) -> None:
        return self._entry.selection_range(start, end)

    def select_to(self, index: str | int) -> None:
        return self._entry.select_to(index)

    def selection_to(self, index: str | int) -> None:
        return self._entry.selection_to(index)

    def xview(self, index: str | int) -> None:
        return self._entry.xview(index)

    def xview_moveto(self, fraction: float) -> None:
        return self._entry.xview_moveto(fraction)

    def xview_scroll(self, number: int | float | str, what: Literal["unit", "pages", "pixels"]) -> None:
        return self._entry.xview_scroll(number, what)
