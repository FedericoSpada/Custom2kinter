from __future__ import annotations

import tkinter
from abc import ABC
from typing import Any, Callable
from typing_extensions import Literal

from ..core_rendering import CTkCanvas
from ..utility import get_proper_cursor


class EntryLike(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._entry = tkinter.Entry(*args, **kwargs)

    def _set_regardless(self, text: str) -> None:
        state = self._entry.cget("state")
        if state != tkinter.NORMAL:
            self._entry.configure(state=tkinter.NORMAL)

        self._entry.delete(0, "end")
        self._entry.insert(0, text)

        if state != tkinter.NORMAL:
            self._entry.configure(state=state)

    def cursor_index(self, index: str | int) -> int:
        #different name to avoid clashing with other methods
        return self._entry.index(index)

    def delete(self, first_index: str | int, last_index: str | int | None = None) -> None:
        self._entry.delete(first_index, last_index)

    def get(self) -> str:
        return self._entry.get()

    def icursor(self, index: str | int) -> None:
        return self._entry.icursor(index)

    def insert(self, index: str | int, string: str) -> None:
        return self._entry.insert(index, string)

    def selection_adjust(self, index: str | int) -> None:
        return self._entry.selection_adjust(index)

    def selection_clear(self) -> None:
        return self._entry.selection_clear()

    def selection_from(self, index: str | int) -> None:
        return self._entry.selection_from(index)

    def selection_present(self) -> bool:
        return self._entry.selection_present()

    def selection_range(self, start: str | int, end: str | int) -> None:
        return self._entry.selection_range(start, end)

    def selection_to(self, index: str | int) -> None:
        return self._entry.selection_to(index)

    select_adjust = selection_adjust
    select_clear = selection_clear
    select_from = selection_from
    select_present = selection_present
    select_range = selection_range
    select_to = selection_to

    def xview(self, *args: Any) -> tuple[float | float] | None:
        return self._entry.xview(*args)

    def xview_moveto(self, fraction: float) -> None:
        return self._entry.xview_moveto(fraction)

    def xview_scroll(self, number: int | float | str, what: Literal["unit", "pages", "pixels"]) -> None:
        return self._entry.xview_scroll(number, what)


class TextLike(ABC):
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._text = tkinter.Text(*args, **kwargs)

    def bbox(self, index: str | float) -> tuple[int, int, int, int] | None:
        return self._text.bbox(index)

    def compare(self,
                index1: str | float,
                op: Literal["<", "<=", "==", ">=", ">", "!=", ],
                index2: str | float) -> bool:
        return self._text.compare(index1, op, index2)

    def delete(self, index1: str | float, index2: str | float | None = None) -> None:
        return self._text.delete(index1, index2)

    def dlineinfo(self, index: str | float) -> tuple[int, int, int, int, int] | None:
        return self._text.dlineinfo(index)

    def edit_modified(self, arg: None = None) -> bool:
        return self._text.edit_modified(arg)

    def edit_redo(self) -> None:
        return self._text.edit_redo()

    def edit_reset(self) -> None:
        return self._text.edit_reset()

    def edit_separator(self) -> None:
        return self._text.edit_separator()

    def edit_undo(self) -> None:
        return self._text.edit_undo()

    def get(self, index1: str | float, index2: str | float | None = None) -> str:
        return self._text.get(index1, index2)

    def image_create(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_cget(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_configure(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def image_names(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding images is forbidden, because would be incompatible with scaling")

    def index(self, index: str | float) -> str:
        return self._text.index(index)

    def insert(self, index: str | float, chars: str, *args: Any) -> None:
        return self._text.insert(index, chars, *args)

    def mark_gravity(self, mark: str, gravity: Literal["left", "right"] | None = None) -> Literal["left", "right"] | None:
        return self._text.mark_gravity(mark, gravity)

    def mark_names(self) -> tuple[str, ...]:
        return self._text.mark_names()

    def mark_next(self, index: str | float) -> str | None:
        return self._text.mark_next(index)

    def mark_previous(self, index: str | float) -> str | None:
        return self._text.mark_previous(index)

    def mark_set(self, mark: str, index: str | float) -> None:
        return self._text.mark_set(mark, index)

    def mark_unset(self, *marks: str) -> None:
        return self._text.mark_unset(*marks)

    def scan_dragto(self, x: int, y: int) -> None:
        return self._text.scan_dragto(x, y)

    def scan_mark(self, x: int, y: int) -> None:
        return self._text.scan_mark(x, y)

    def search(self, pattern: str, index: str | float, *args: Any, **kwargs: Any) -> str:
        return self._text.search(pattern, index, *args, **kwargs)

    def see(self, index: str | float) -> None:
        return self._text.see(index)

    def tag_add(self, tagName: str, index1: str | float, index2: str | float | None = None) -> None:
        return self._text.tag_add(tagName, index1, index2)

    def tag_bind(self,
                 tagName: str,
                 sequence: str | None,
                 func: Callable[[tkinter.Event], None] | None = None,
                 add: str | bool = True) -> str:
        return self._text.tag_bind(tagName, sequence, func, add)

    def tag_unbind(self, tagName: str, sequence: str, funcid: str | None = None) -> None:
        return self._text.tag_unbind(tagName, sequence, funcid)

    def tag_cget(self, tagName: str, option: str) -> Any:
        return self._text.tag_cget(tagName, option)

    def tag_configure(self, tagName: str, **kwargs: Any) -> Any:
        return self._text.tag_configure(tagName, **kwargs)

    tag_config = tag_configure

    def tag_delete(self, *tagNames: str) -> None:
        return self._text.tag_delete(*tagNames)

    def tag_lower(self, tagName: str, belowThis: str | None = None) -> None:
        return self._text.tag_lower(tagName, belowThis)

    def tag_raise(self, tagName: str, aboveThis: str | None = None) -> None:
        return self._text.tag_raise(tagName, aboveThis)

    def tag_names(self, index: str | float | None = None) -> tuple[str, ...]:
        return self._text.tag_names(index)

    def tag_nextrange(self,
                      tagName: str,
                      index1: str | float,
                      index2: str | float | None = None) -> tuple[str, str]:
        return self._text.tag_nextrange(tagName, index1, index2)

    def tag_prevrange(self,
                      tagName: str,
                      index1: str | float,
                      index2: str | float | None = None) -> tuple[str, str]:
        return self._text.tag_prevrange(tagName, index1, index2)

    def tag_ranges(self, tagName: str) -> tuple[str, ...]:
        return self._text.tag_ranges(tagName)

    def tag_remove(self, tagName: str, index1: str | float, index2: str | float | None = None) -> None:
        return self._text.tag_remove(tagName, index1, index2)

    def window_cget(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_configure(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_create(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def window_names(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("embedding widgets is forbidden, would probably cause all kinds of problems ;)")

    def xview(self, *args: Any) -> tuple[float | float] | None:
        return self._text.xview(*args)

    def xview_moveto(self, fraction: float) -> None:
        return self._text.xview_moveto(fraction)

    def xview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._text.xview_scroll(number, what)

    def yview(self, *args: Any) -> tuple[float | float] | None:
        return self._text.yview(*args)

    def yview_moveto(self, fraction: float) -> None:
        return self._text.yview_moveto(fraction)

    def yview_scroll(self, number: int, what: Literal["units", "pages"]) -> None:
        return self._text.yview_scroll(number, what)


class CanvasWithLabel(ABC):
    def __init__(self, width: int, height: int, canvas_width: int, canvas_height: int) -> None:
        self._bg_canvas = CTkCanvas(master=self,
                                    width=width,
                                    height=height)
        self._bg_canvas.grid(row=0, column=0, rowspan=3, columnspan=3, sticky="nsew")

        self._canvas = CTkCanvas(master=self,
                                 width=canvas_width,
                                 height=canvas_height)

        self._text_label = tkinter.Label(master=self, borderwidth=0, padx=0, pady=0)

    def _update_geometry(self, compound: str, widget_label_spacing: int) -> None:
        # configure grid system (1x3 or 3x1)

        if not self._text_label.cget("text") and not self._text_label.cget("textvariable"):
            if isinstance(self, tkinter.Misc):
                self.grid_rowconfigure(0, weight=1)
                self.grid_rowconfigure((1, 2), weight=0, minsize=0)
                self.grid_columnconfigure(0, weight=1)
                self.grid_columnconfigure((1, 2), weight=0, minsize=0)
            self._canvas.grid(row=0, column=0)
            self._text_label.grid_forget()

        else:
            if compound in ("left", "right"):
                if isinstance(self, tkinter.Frame):
                    self.grid_columnconfigure(0, weight=0 if compound == "left" else 1)
                    self.grid_columnconfigure(1, weight=0, minsize=widget_label_spacing)
                    self.grid_columnconfigure(2, weight=1 if compound == "left" else 0)
                    self.grid_rowconfigure(0, weight=1)
                    self.grid_rowconfigure((1, 2), weight=0, minsize=0)
            else:
                if isinstance(self, tkinter.Frame):
                    self.grid_rowconfigure(0, weight=0 if compound == "top" else 1)
                    self.grid_rowconfigure(1, weight=0, minsize=widget_label_spacing)
                    self.grid_rowconfigure(2, weight=1 if compound == "top" else 0)
                    self.grid_columnconfigure(0, weight=1)
                    self.grid_columnconfigure((1, 2), weight=0, minsize=0)

            if compound == "left":
                self._canvas.grid(row=0, column=0, sticky="e")
                self._text_label.grid(row=0, column=2, sticky="ew")
            elif compound == "right":
                self._text_label.grid(row=0, column=0, sticky="ew")
                self._canvas.grid(row=0, column=2, sticky="w")
            elif compound == "top":
                self._canvas.grid(row=0, column=0, sticky="s")
                self._text_label.grid(row=2, column=0, sticky="ns")
            else:
                self._text_label.grid(row=0, column=0, sticky="ns")
                self._canvas.grid(row=2, column=0, sticky="n")

    def _set_cursor(self, mode: Literal["normal", "clickable"]) -> None:
        if cursor := get_proper_cursor(mode):
            self._canvas.configure(cursor=cursor)
            self._text_label.configure(cursor=cursor)
