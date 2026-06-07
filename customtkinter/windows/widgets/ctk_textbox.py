from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack


from .core_widget_classes import CTkContainer, CTkScrollable, CTkWidget, TextLike
from .core_rendering import CTkCanvas, BorderedRoundedRect
from .font import CTkFont, FontType
from .ctk_scrollbar import CTkScrollbar, CTkScrollbarArgs
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkTextboxThemedArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    border_color: ColorType
    text_color: ColorType
    font: FontType
    activate_scrollbars: bool
    scrollbar: CTkScrollbarArgs

#Explanations can be found here: https://tkdocs.com/shipman/text.html
class ValidTkTextArgs(TypedDict, total=False):
    state: Literal["normal", "disabled"]
    undo: bool
    autoseparators: bool
    maxundo: int
    wrap: Literal["none", "char", "word"]
    cursor: str
    insertofftime: int
    insertontime: int
    insertborderwidth: float | str
    insertwidth: float | str
    selectbackground: str
    selectforeground: str
    selectborderwidth: float | str
    spacing1: float | str
    spacing2: float | str
    spacing3: float | str
    tabs: float | str | tuple[float | str, ...]
    exportselection: bool
    takefocus: bool
    #--- Configure only ---
    xscrollcommand: str | Callable[[float, float], None]
    yscrollcommand: str | Callable[[float, float], None]

class CTkTextboxArgs(CTkTextboxThemedArgs, ValidTkTextArgs, total=False):
    xscrollincrement: int  # [characters]
    yscrollincrement: int  # [lines]


class CTkTextbox(CTkWidget, CTkScrollable, TextLike):
    """
    Textbox with x and y scrollbars, rounded corners, and all text features of tkinter.Text widget.
    Scrollbars only appear when they are needed. Text is wrapped on line end by default,
    set wrap='none' to disable automatic line wrapping.
    For detailed information check out the documentation.
    """

    scrollbar_update_time: int = 200  # interval in [ms], to check if scrollbars are needed

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkTextboxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkTextboxThemedArgs.__annotations__)
        self._theme_info: CTkTextboxThemedArgs = ThemeManager.get_info("CTkTextbox", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=self._theme_info["width"],
                           height=self._theme_info["height"])
        CTkScrollable.__init__(self, self.winfo_toplevel())

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)
        self._tagged_fonts: dict[str, CTkFont] = {}

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
        self._rounded_rect = BorderedRoundedRect(self._canvas)

        TextLike.__init__(self,
                          master=self,
                          width=0,
                          height=0,
                          padx=0,
                          pady=0,
                          highlightthickness=0,
                          font=self._apply_font_scaling(self._font),
                          relief="flat",
                          **pop_from_dict_by_iterable(kwargs, ValidTkTextArgs.__annotations__))
        self._bind_targets.append(self._text)
        self._focus_target = self._text

        #tk.Text has built-in bindings to the scroll event.
        # To avoid scrolling the widget when inside a scrollable parent, we rearrange the
        # firing order so that we can return "break", which prevents the normal behavior.
        # We could have used .bind_class("Text", "<MouseWheel>" lambda _: "break"), but it
        # would apply to all tk.Text objects, not only this one.
        tags = self._text.bindtags()
        self._text.bindtags((tags[0], tags[2], tags[3], tags[1]))

        # scrollbars
        scrollbar_kwargs = self._theme_info["scrollbar"]
        scrollbar_kwargs["bg_color"] = self._theme_info["fg_color"]
        scrollbar_kwargs["length"] = 0

        self._hide_hor_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "horizontal"
        self._hor_scrollbar = CTkScrollbar(self,
                                           command=self._text.xview,
                                           scrollincrement=kwargs.pop("xscrollincrement", 5),
                                           **scrollbar_kwargs)

        self._hide_ver_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "vertical"
        self._ver_scrollbar = CTkScrollbar(self,
                                           command=self._text.yview,
                                           scrollincrement=kwargs.pop("yscrollincrement", 3),
                                           **scrollbar_kwargs)

        self._text.configure(xscrollcommand=self._hor_scrollbar.set, yscrollcommand=self._ver_scrollbar.set)

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._loop_after_id: str = self.after(50, self._check_if_scrollbars_needed, True)
        self._draw(force_colors_update=True)

    def _check_if_scrollbars_needed(self, continue_loop: bool = False) -> None:
        if self._theme_info["activate_scrollbars"]:
            new_hide_hor_scrollbar = self._text.xview() == (0.0, 1.0) #horizontal scrollbar not needed
            new_hide_ver_scrollbar = self._text.yview() == (0.0, 1.0) #vertical scrollbar not needed
        else:
            new_hide_hor_scrollbar = True
            new_hide_ver_scrollbar = True

        if new_hide_hor_scrollbar != self._hide_hor_scrollbar or new_hide_ver_scrollbar != self._hide_ver_scrollbar:
            self._hide_hor_scrollbar = new_hide_hor_scrollbar
            self._hide_ver_scrollbar = new_hide_ver_scrollbar
            self._update_geometry()

        if self._text.winfo_exists() and continue_loop:
            self._loop_after_id = self.after(self.scrollbar_update_time, self._check_if_scrollbars_needed, True)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._text.configure(font=self._apply_font_scaling(self._font))
        for tag_name, tag_font in self._tagged_fonts.items():
            self._text.tag_configure(tag_name, font=self._apply_font_scaling(tag_font))
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
        self._text.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")

    def _on_scroll(self,
                   event: tkinter.Event,
                   is_up: bool,
                   normalized_delta: int,
                   modifier: Literal["", "shift", "ctrl"]) -> str | None:
        if modifier == "shift":
            self._hor_scrollbar.view_scroll(-normalized_delta, "units")
        else:
            self._ver_scrollbar.view_scroll(-normalized_delta, "units")
        #"break" is returned so that the normal scroll behavior of the tk.Text widget is avoided
        return "break"

    def destroy(self) -> None:
        self.after_cancel(self._loop_after_id)
        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._rounded_rect.info["spacings_changed"]:
            self._update_geometry()

        if force_colors_update or requires_recoloring:
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color)
            text_color = self._apply_appearance_mode(self._theme_info["text_color"])

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))
            self._rounded_rect.set_main_color(fg_color)
            self._text.configure(fg=text_color, bg=fg_color, insertbackground=text_color)

    def _update_geometry(self) -> None:
        info = self._rounded_rect.info.get
        border_spacing = self._apply_scaling(self._theme_info["border_spacing"])
        inscribed_spacing = info("inscribed_spacing", 0)
        textbox_spacing = inscribed_spacing + border_spacing
        scrollbar_spacing = (info("flat_spacing", 0) + inscribed_spacing) / 2 + border_spacing
        scrollbar_border = info("border_width", 0) + border_spacing
        delta_spacing = max(0, scrollbar_spacing - textbox_spacing)

        # configure 2x2 grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=textbox_spacing)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=textbox_spacing)

        self._text.grid(row=0, column=0, sticky="nsew",
                        padx=(textbox_spacing, 0),
                        pady=(textbox_spacing, 0))

        if not self._hide_hor_scrollbar:
            self._hor_scrollbar.grid(row=1, column=0, sticky="ew",
                                     pady=(border_spacing, scrollbar_border),
                                     padx=(scrollbar_spacing, delta_spacing),
                                     apply_scaling=False)
        else:
            self._hor_scrollbar.grid_forget()

        if not self._hide_ver_scrollbar:
            self._ver_scrollbar.grid(row=0, column=1, sticky="ns",
                                     padx=(border_spacing, scrollbar_border),
                                     pady=(scrollbar_spacing, delta_spacing),
                                     apply_scaling=False)
        else:
            self._ver_scrollbar.grid_forget()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkTextboxArgs]) -> None:
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
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            self._hor_scrollbar.configure(bg_color=self._theme_info["fg_color"])
            self._ver_scrollbar.configure(bg_color=self._theme_info["fg_color"])
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "activate_scrollbars" in kwargs:
            self._theme_info["activate_scrollbars"] = kwargs.pop("activate_scrollbars")

        if "xscrollincrement" in kwargs:
            self._hor_scrollbar.configure(scrollincrement=kwargs.pop("xscrollincrement"))

        if "yscrollincrement" in kwargs:
            self._ver_scrollbar.configure(scrollincrement=kwargs.pop("yscrollincrement"))

        if "scrollbar" in kwargs:
            scrollbar_kwargs = kwargs.pop("scrollbar")
            self._hor_scrollbar.configure(**scrollbar_kwargs)
            self._ver_scrollbar.configure(**scrollbar_kwargs)

        self._text.configure(**pop_from_dict_by_iterable(kwargs, ValidTkTextArgs.__annotations__))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "xscrollincrement":
            return self._hor_scrollbar.cget("scrollincrement")
        elif attribute_name == "yscrollincrement":
            return self._ver_scrollbar.cget("scrollincrement")
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("scrollbar_"):
            return self._ver_scrollbar.cget(attribute_name.removeprefix("scrollbar_"))
        elif attribute_name in ValidTkTextArgs.__annotations__:
            return self._text.cget(attribute_name)
        else:
            return super().cget(attribute_name)

    def edit_redo(self) -> None:
        retval = super().edit_redo()
        self._check_if_scrollbars_needed()
        return retval

    def edit_undo(self) -> None:
        retval = super().edit_undo()
        self._check_if_scrollbars_needed()
        return retval

    def tag_configure(self, tagName: str, font: FontType | None = None, **kwargs: Any) -> Any:
        if font is not None:
            if font:
                self._tagged_fonts[tagName] = CTkFont.from_parameter(font)
                kwargs["font"] = self._apply_font_scaling(self._tagged_fonts[tagName])
            else:
                self._tagged_fonts.pop(tagName, None)
                kwargs["font"] = ""
        return super().tag_configure(tagName, **kwargs)

    def xview(self, *args: Any) -> None:
        return self._hor_scrollbar.view(*args)

    def xview_moveto(self, fraction: float) -> None:
        return self._hor_scrollbar.view_moveto(fraction)

    def xview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._hor_scrollbar.view_scroll(number, what)

    def yview(self, *args: Any) -> None:
        return self._ver_scrollbar.view(*args)

    def yview_moveto(self, fraction: float) -> None:
        return self._ver_scrollbar.view_moveto(fraction)

    def yview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._ver_scrollbar.view_scroll(number, what)
