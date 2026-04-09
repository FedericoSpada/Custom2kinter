from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack


from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .font.ctk_font import CTkFont, CTkFontArgs
from .ctk_scrollbar import CTkScrollbar, CTkScrollbarArgs
from .theme import ThemeManager
from .utility import pop_from_dict_by_set


class CTkTextboxArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    font: CTkFontArgs | CTkFont | tuple | str
    activate_scrollbars: bool
    scrollbar: CTkScrollbarArgs


class CTkTextbox(CTkBaseClass):
    """
    Textbox with x and y scrollbars, rounded corners, and all text features of tkinter.Text widget.
    Scrollbars only appear when they are needed. Text is wrapped on line end by default,
    set wrap='none' to disable automatic line wrapping.
    For detailed information check out the documentation.

    Detailed methods and parameters of the underlaying tkinter.Text widget can be found here:
    https://anzeljg.github.io/rin2/book2/2405/docs/tkinter/text.html
    (most of them are implemented here too)
    """

    _scrollbar_update_time: int = 200  # interval in ms, to check if scrollbars are needed

    # attributes that are passed to and managed by the tkinter textbox only:
    _valid_tk_text_attributes: set[str] = {"autoseparators", "cursor", "exportselection",
                                           "insertborderwidth", "insertofftime", "insertontime", "insertwidth",
                                           "maxundo", "padx", "pady", "selectborderwidth", "spacing1",
                                           "spacing2", "spacing3", "state", "tabs", "takefocus", "undo", "wrap",
                                           "xscrollcommand", "yscrollcommand"}

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkTextboxArgs]) -> None:

        textbox_kwargs = pop_from_dict_by_set(kwargs, self._valid_tk_text_attributes)

        self._theme_info: CTkTextboxArgs = ThemeManager.get_info("CTkTextbox", theme_key, **kwargs)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

        # transfer basic functionality (_bg_color, size, __appearance_mode, scaling) to CTkBaseClass
        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
        self._draw_engine = DrawEngine(self._canvas)

        self._textbox = tkinter.Text(self,
                                     fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                                     width=0,
                                     height=0,
                                     font=self._apply_font_scaling(self._font),
                                     highlightthickness=0,
                                     relief="flat",
                                     insertbackground=self._apply_appearance_mode(self._theme_info["text_color"]),
                                     **textbox_kwargs)

        # scrollbars
        scrollbar_kwargs = self._theme_info["scrollbar"]
        scrollbar_kwargs["fg_color"] = self._theme_info["fg_color"]
        scrollbar_kwargs["border_spacing"] = 0
        scrollbar_kwargs["thickness"] = 8
        scrollbar_kwargs["lenght"] = 0

        self._hide_y_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "vertical"
        self._y_scrollbar = CTkScrollbar(self, command=self._textbox.yview, **scrollbar_kwargs)

        self._hide_x_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "horizontal"
        self._x_scrollbar = CTkScrollbar(self, command=self._textbox.xview, **scrollbar_kwargs)

        self._textbox.configure(xscrollcommand=self._x_scrollbar.set, yscrollcommand=self._y_scrollbar.set)

        self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)

        self.after(50, self._check_if_scrollbars_needed, None, True)
        self._draw()

    def _create_grid_for_text_and_scrollbars(self,
                                             re_grid_textbox: bool = False,
                                             re_grid_x_scrollbar: bool = False,
                                             re_grid_y_scrollbar: bool = False) -> None:
        border = self._theme_info["border_width"] + self._theme_info["border_spacing"]
        spacing = max(self._theme_info["corner_radius"], border)

        # configure 2x2 grid
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0, minsize=self._apply_widget_scaling(spacing))
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=self._apply_widget_scaling(spacing))

        if re_grid_textbox:
            self._textbox.grid(row=0, column=0, rowspan=1, columnspan=1, sticky="nsew",
                               padx=(self._apply_widget_scaling(spacing), 0),
                               pady=(self._apply_widget_scaling(spacing), 0))

        if re_grid_x_scrollbar:
            if not self._hide_x_scrollbar and self._theme_info["activate_scrollbars"]:
                self._x_scrollbar.grid(row=1, column=0, rowspan=1, columnspan=1, sticky="ewn",
                                       pady=(3, border), padx=(spacing, 0))  # scrollbar grid method without scaling
            else:
                self._x_scrollbar.grid_forget()

        if re_grid_y_scrollbar:
            if not self._hide_y_scrollbar and self._theme_info["activate_scrollbars"]:
                self._y_scrollbar.grid(row=0, column=1, rowspan=1, columnspan=1, sticky="nsw",
                                       padx=(3, border), pady=(spacing, 0))  # scrollbar grid method without scaling
            else:
                self._y_scrollbar.grid_forget()

    def _check_if_scrollbars_needed(self, _: tkinter.Event | None = None, continue_loop: bool = False) -> None:
        """ Method hides or places the scrollbars if they are needed on key release event of tkinter.text widget """

        if self._theme_info["activate_scrollbars"]:
            if self._textbox.xview() != (0.0, 1.0) and not self._x_scrollbar.winfo_ismapped():  # x scrollbar needed
                self._hide_x_scrollbar = False
                self._create_grid_for_text_and_scrollbars(re_grid_x_scrollbar=True)
            elif self._textbox.xview() == (0.0, 1.0) and self._x_scrollbar.winfo_ismapped():  # x scrollbar not needed
                self._hide_x_scrollbar = True
                self._create_grid_for_text_and_scrollbars(re_grid_x_scrollbar=True)

            if self._textbox.yview() != (0.0, 1.0) and not self._y_scrollbar.winfo_ismapped():  # y scrollbar needed
                self._hide_y_scrollbar = False
                self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)
            elif self._textbox.yview() == (0.0, 1.0) and self._y_scrollbar.winfo_ismapped():  # y scrollbar not needed
                self._hide_y_scrollbar = True
                self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)
        else:
            self._hide_x_scrollbar = False
            self._hide_x_scrollbar = False
            self._create_grid_for_text_and_scrollbars(re_grid_y_scrollbar=True)

        if self._textbox.winfo_exists() and continue_loop is True:
            self.after(self._scrollbar_update_time, lambda: self._check_if_scrollbars_needed(continue_loop=True))

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._textbox.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._textbox.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, rowspan=2, columnspan=2, sticky="nsew")

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                              self._apply_widget_scaling(self._theme_info["border_width"]))

        if no_color_updates is False or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"])
            text_color = self._apply_appearance_mode(self._theme_info["text_color"])
            border_color = self._apply_appearance_mode(self._theme_info["border_color"])

            if self._theme_info["fg_color"] == "transparent":
                self._canvas.itemconfig("inner_parts", fill=bg_color, outline=bg_color)
                self._textbox.configure(fg=text_color, bg=bg_color, insertbackground=text_color)
                self._x_scrollbar.configure(fg_color=self._bg_color)
                self._y_scrollbar.configure(fg_color=self._bg_color)
            else:
                self._canvas.itemconfig("inner_parts", fill=fg_color, outline=fg_color)
                self._textbox.configure(fg=text_color, bg=fg_color, insertbackground=text_color)
                self._x_scrollbar.configure(fg_color=self._theme_info["fg_color"])
                self._y_scrollbar.configure(fg_color=self._theme_info["fg_color"])

            self._canvas.itemconfig("border_parts", fill=border_color, outline=border_color)
            self._canvas.configure(bg=bg_color)

        self._canvas.tag_lower("inner_parts")
        self._canvas.tag_lower("border_parts")

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkTextboxArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._create_grid_for_text_and_scrollbars(re_grid_textbox=True, re_grid_x_scrollbar=True, re_grid_y_scrollbar=True)
            require_redraw = True

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "scrollbar" in kwargs:
            self._theme_info["scrollbar"] = kwargs.pop("scrollbar")
            self._x_scrollbar.configure(**self._theme_info["scrollbar"])
            self._y_scrollbar.configure(**self._theme_info["scrollbar"])

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        self._textbox.configure(**pop_from_dict_by_set(kwargs, self._valid_tk_text_attributes))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name in self._valid_tk_text_attributes:
            return self._textbox.cget(attribute_name)  # cget of tkinter.Text
        else:
            return super().cget(attribute_name)

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Text """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._textbox.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Label and tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._textbox.unbind(sequence, None)

    def focus(self) -> None:
        return self._textbox.focus()

    def focus_set(self) -> None:
        return self._textbox.focus_set()

    def focus_force(self) -> None:
        return self._textbox.focus_force()

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

    def tag_config(self, tagName: str, **kwargs: Any) -> Any:
        if "font" in kwargs:
            raise AttributeError("'font' option forbidden, because would be incompatible with scaling")
        return self._textbox.tag_config(tagName, **kwargs)

    def tag_configure(self, tagName: str, **kwargs: Any) -> Any:
        if "font" in kwargs:
            raise AttributeError("'font' option forbidden, because would be incompatible with scaling")
        return self._textbox.tag_configure(tagName, **kwargs)

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
