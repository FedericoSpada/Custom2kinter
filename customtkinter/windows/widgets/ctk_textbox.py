from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack


from .core_widget_classes import CTkContainer, CTkWidget
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
    pass


class CTkTextbox(CTkWidget):
    """
    Textbox with x and y scrollbars, rounded corners, and all text features of tkinter.Text widget.
    Scrollbars only appear when they are needed. Text is wrapped on line end by default,
    set wrap='none' to disable automatic line wrapping.
    For detailed information check out the documentation.
    """

    _scrollbar_update_time: int = 200  # interval in ms, to check if scrollbars are needed

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

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

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

        self._textbox = tkinter.Text(self,
                                     width=0,
                                     height=0,
                                     padx=0,
                                     pady=0,
                                     highlightthickness=0,
                                     font=self._apply_font_scaling(self._font),
                                     relief="flat",
                                     **pop_from_dict_by_iterable(kwargs, ValidTkTextArgs.__annotations__))
        self._bind_targets.append(self._textbox)
        self._focus_target = self._textbox

        # scrollbars
        scrollbar_kwargs = self._theme_info["scrollbar"]
        scrollbar_kwargs["bg_color"] = self._theme_info["fg_color"]
        scrollbar_kwargs["length"] = 0

        self._hide_hor_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "horizontal"
        self._hor_scrollbar = CTkScrollbar(self, command=self._textbox.xview, **scrollbar_kwargs)

        self._hide_ver_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "vertical"
        self._ver_scrollbar = CTkScrollbar(self, command=self._textbox.yview, **scrollbar_kwargs)

        self._textbox.configure(xscrollcommand=self._hor_scrollbar.set, yscrollcommand=self._ver_scrollbar.set)

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._loop_after_id: str = self.after(50, self._check_if_scrollbars_needed, True)
        self._draw(force_colors_update=True)

    def _check_if_scrollbars_needed(self, continue_loop: bool = False) -> None:
        if self._theme_info["activate_scrollbars"]:
            new_hide_hor_scrollbar = self._textbox.xview() == (0.0, 1.0) #horizontal scrollbar not needed
            new_hide_ver_scrollbar = self._textbox.yview() == (0.0, 1.0) #vertical scrollbar not needed
        else:
            new_hide_hor_scrollbar = True
            new_hide_ver_scrollbar = True

        if new_hide_hor_scrollbar != self._hide_hor_scrollbar or new_hide_ver_scrollbar != self._hide_ver_scrollbar:
            self._hide_hor_scrollbar = new_hide_hor_scrollbar
            self._hide_ver_scrollbar = new_hide_ver_scrollbar
            self._update_geometry()

        if self._textbox.winfo_exists() and continue_loop:
            self._loop_after_id = self.after(self._scrollbar_update_time, self._check_if_scrollbars_needed, True)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._textbox.configure(font=self._apply_font_scaling(self._font))
        for tag_name, tag_font in self._tagged_fonts.items():
            self._textbox.tag_configure(tag_name, font=self._apply_font_scaling(tag_font))
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
        self._textbox.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")

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
            self._textbox.configure(fg=text_color, bg=fg_color, insertbackground=text_color)

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

        self._textbox.grid(row=0, column=0, sticky="nsew",
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

        if "scrollbar" in kwargs:
            scrollbar_kwargs = kwargs.pop("scrollbar")
            self._hor_scrollbar.configure(**scrollbar_kwargs)
            self._ver_scrollbar.configure(**scrollbar_kwargs)

        self._textbox.configure(**pop_from_dict_by_iterable(kwargs, ValidTkTextArgs.__annotations__))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("scrollbar_"):
            return self._ver_scrollbar.cget(attribute_name.removeprefix("scrollbar_"))
        elif attribute_name in ValidTkTextArgs.__annotations__:
            return self._textbox.cget(attribute_name)
        else:
            return super().cget(attribute_name)

    def insert(self, index: str | float, chars: str, *args: Any) -> None:
        return self._textbox.insert(index, chars, *args)

    def get(self, index1: str | float, index2: str | float | None = None) -> str:
        return self._textbox.get(index1, index2)

    def bbox(self, index: str | float) -> tuple[int, int, int, int] | None:
        return self._textbox.bbox(index)

    def compare(self,
                index1: str | float,
                op: Literal["<", "<=", "==", ">=", ">", "!=", ],
                index2: str | float) -> bool:
        return self._textbox.compare(index1, op, index2)

    def delete(self, index1: str | float, index2: str | float | None = None) -> None:
        return self._textbox.delete(index1, index2)

    def dlineinfo(self, index: str | float) -> tuple[int, int, int, int, int] | None:
        return self._textbox.dlineinfo(index)

    def edit_modified(self, arg: None = None) -> bool:
        return self._textbox.edit_modified(arg)

    def edit_redo(self) -> None:
        self._check_if_scrollbars_needed()
        return self._textbox.edit_redo()

    def edit_reset(self) -> None:
        return self._textbox.edit_reset()

    def edit_separator(self) -> None:
        return self._textbox.edit_separator()

    def edit_undo(self) -> None:
        self._check_if_scrollbars_needed()
        return self._textbox.edit_undo()

    def image_create(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_cget(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_configure(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_names(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def index(self, index: str | float) -> str:
        return self._textbox.index(index)

    def mark_gravity(self, mark: str, gravity: Literal["left", "right"] | None = None) -> Literal["left", "right"] | None:
        return self._textbox.mark_gravity(mark, gravity)

    def mark_names(self) -> tuple[str, ...]:
        return self._textbox.mark_names()

    def mark_next(self, index: str | float) -> str | None:
        return self._textbox.mark_next(index)

    def mark_previous(self, index: str | float) -> str | None:
        return self._textbox.mark_previous(index)

    def mark_set(self, mark: str, index: str | float) -> None:
        return self._textbox.mark_set(mark, index)

    def mark_unset(self, *marks: str) -> None:
        return self._textbox.mark_unset(*marks)

    def scan_dragto(self, x: int, y: int) -> None:
        return self._textbox.scan_dragto(x, y)

    def scan_mark(self, x: int, y: int) -> None:
        return self._textbox.scan_mark(x, y)

    def search(self, pattern: str, index: str | float, *args: Any, **kwargs: Any) -> str:
        return self._textbox.search(pattern, index, *args, **kwargs)

    def see(self, index: str | float) -> None:
        return self._textbox.see(index)

    def tag_add(self, tagName: str, index1: str | float, index2: str | float | None = None) -> None:
        return self._textbox.tag_add(tagName, index1, index2)

    def tag_bind(self,
                 tagName: str,
                 sequence: str | None,
                 func: Callable[[tkinter.Event], None] | None = None,
                 add: str | bool = True) -> str:
        return self._textbox.tag_bind(tagName, sequence, func, add)

    def tag_unbind(self, tagName: str, sequence: str, funcid: str | None = None) -> None:
        return self._textbox.tag_unbind(tagName, sequence, funcid)

    def tag_cget(self, tagName: str, option: str) -> Any:
        return self._textbox.tag_cget(tagName, option)

    def tag_configure(self, tagName: str, font: FontType | None = None, **kwargs: Any) -> Any:
        if font is not None:
            if font:
                self._tagged_fonts[tagName] = CTkFont.from_parameter(font)
                kwargs["font"] = self._apply_font_scaling(self._tagged_fonts[tagName])
            else:
                self._tagged_fonts.pop(tagName, None)
                kwargs["font"] = ""
        return self._textbox.tag_configure(tagName, **kwargs)

    tag_config = tag_configure

    def tag_delete(self, *tagNames: str) -> None:
        return self._textbox.tag_delete(*tagNames)

    def tag_lower(self, tagName: str, belowThis: str | None = None) -> None:
        return self._textbox.tag_lower(tagName, belowThis)

    def tag_raise(self, tagName: str, aboveThis: str | None = None) -> None:
        return self._textbox.tag_raise(tagName, aboveThis)

    def tag_names(self, index: str | float | None = None) -> tuple[str, ...]:
        return self._textbox.tag_names(index)

    def tag_nextrange(self,
                      tagName: str,
                      index1: str | float,
                      index2: str | float | None = None) -> tuple[str, str]:
        return self._textbox.tag_nextrange(tagName, index1, index2)

    def tag_prevrange(self,
                      tagName: str,
                      index1: str | float,
                      index2: str | float | None = None) -> tuple[str, str]:
        return self._textbox.tag_prevrange(tagName, index1, index2)

    def tag_ranges(self, tagName: str) -> tuple[str, ...]:
        return self._textbox.tag_ranges(tagName)

    def tag_remove(self, tagName: str, index1: str | float, index2: str | float | None = None) -> None:
        return self._textbox.tag_remove(tagName, index1, index2)

    def window_cget(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_configure(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_create(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_names(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def xview(self, *args: Any) -> None:
        return self._textbox.xview(*args)

    def xview_moveto(self, fraction: float) -> None:
        return self._textbox.xview_moveto(fraction)

    def xview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._textbox.xview_scroll(number, what)

    def yview(self, *args: Any) -> None:
        return self._textbox.yview(*args)

    def yview_moveto(self, fraction: float) -> None:
        return self._textbox.yview_moveto(fraction)

    def yview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._textbox.yview_scroll(number, what)
