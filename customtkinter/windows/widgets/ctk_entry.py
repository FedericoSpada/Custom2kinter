from __future__ import annotations

import tkinter
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect
from .font import CTkFont, FontType
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_set


class CTkEntryArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    border_color: ColorType
    text_color: ColorType
    placeholder_text_color: ColorType
    placeholder_text: str
    font: FontType


class CTkEntry(CTkWidget):
    """
    Entry with rounded corners, border, textvariable support, focus and placeholder.
    For detailed information check out the documentation.
    """

    # attributes that are passed to and managed by the tkinter entry only:
    _valid_tk_entry_attributes: set[str] = {"exportselection", "insertborderwidth", "insertofftime",
                                            "insertontime", "insertwidth", "justify", "selectborderwidth",
                                            "show", "takefocus", "validate", "validatecommand", "xscrollcommand"}

    def __init__(self,
                 master: CTkContainer,
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
        self._is_focused: bool = False
        self._placeholder_text_active: bool = False
        self._pre_placeholder_arguments: dict[str, Any] = {}  # some set arguments of the entry will be changed for placeholder and then set back

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nsew")
        self._rounded_rect = BorderedRoundedRect(self._canvas)

        self._entry = tkinter.Entry(master=self,
                                    bd=0,
                                    width=1,
                                    highlightthickness=0,
                                    font=self._apply_font_scaling(self._font),
                                    state=self._state,
                                    textvariable=self._textvariable,
                                    **entry_kwargs)
        self._bind_targets.append(self._entry)
        self._focus_target = self._entry

        self._activate_placeholder()
        self._create_bindings()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<FocusIn>":
            self._entry.bind("<FocusIn>", self._entry_focus_in)
        if sequence is None or sequence == "<FocusOut>":
            self._entry.bind("<FocusOut>", self._entry_focus_out)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._entry.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._entry.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(column=0, row=0, sticky="nswe")

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._rounded_rect.info["spacings_changed"]:
            self._update_geometry()

        if force_colors_update or requires_recoloring:
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color)
            if self._placeholder_text_active:
                text_color = self._apply_appearance_mode(self._theme_info["placeholder_text_color"])
            else:
                text_color = self._apply_appearance_mode(self._theme_info["text_color"])

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(fg_color)
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))
            self._entry.configure(bg=fg_color, disabledbackground=fg_color, readonlybackground=fg_color, highlightcolor=fg_color)
            self._entry.configure(fg=text_color, disabledforeground=text_color, insertbackground=text_color)

    def _update_geometry(self) -> None:
        spacing = self._rounded_rect.info.get("inscribed_spacing", 0)
        border_spacing = self._apply_scaling(self._theme_info["border_spacing"])
        self._entry.grid(row=0, column=0, sticky="nsew", padx=spacing + border_spacing, pady=spacing)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkEntryArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

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
            self._textvariable = kwargs.pop("textvariable")
            self._entry.configure(textvariable=self._textvariable)
            self._deactivate_placeholder()
            self._activate_placeholder()

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
        super().configure(require_redraw=require_redraw, **kwargs)

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
            return super().cget(attribute_name)

    def _activate_placeholder(self) -> None:
        if self._entry.get() == "" and self._textvariable is None and not self._is_focused:
            self._placeholder_text_active = True

            self._pre_placeholder_arguments = {"show": self._entry.cget("show")}
            self._entry.config(fg=self._apply_appearance_mode(self._theme_info["placeholder_text_color"]),
                               disabledforeground=self._apply_appearance_mode(self._theme_info["placeholder_text_color"]),
                               show="")
            self._entry.delete(0, tkinter.END)
            self._entry.insert(0, self._theme_info["placeholder_text"])

    def _deactivate_placeholder(self) -> None:
        if self._placeholder_text_active:
            self._placeholder_text_active = False

            self._entry.config(fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                               disabledforeground=self._apply_appearance_mode(self._theme_info["text_color"]))
            self._entry.delete(0, tkinter.END)
            self._entry.configure(**self._pre_placeholder_arguments)

    def _entry_focus_out(self, _: tkinter.Event | None = None) -> None:
        self._is_focused = False
        self._activate_placeholder()

    def _entry_focus_in(self, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            self._is_focused = True
            self._deactivate_placeholder()

    def delete(self, first_index: str | int, last_index: str | int | None = None) -> None:
        self._entry.delete(first_index, last_index)
        self._activate_placeholder()

    def insert(self, index: str | int, string: str) -> None:
        self._deactivate_placeholder()
        return self._entry.insert(index, string)

    def set(self, string: str) -> None:
        """ Changes the content to the desired value, regardless of the widget's state. """
        if self._state == tkinter.NORMAL:
            self._entry.delete(0, tkinter.END)
            self.insert(0, string)
        else:
            self._entry.configure(state=tkinter.NORMAL)
            self._entry.delete(0, tkinter.END)
            self.insert(0, string)
            self._entry.configure(state=self._state)

    def get(self) -> str:
        if self._placeholder_text_active:
            return ""
        else:
            return self._entry.get()

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
