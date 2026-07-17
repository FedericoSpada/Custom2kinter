from __future__ import annotations

import tkinter
import copy
from functools import partial
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer
from .core_widget_classes.ctk_widget import CTkWidgetArgs
from .theme import ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame
from .ctk_symbolbox import CTkSymbolBox, CTkSymbolBoxThemedArgs, SymbolType
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, deep_update, first_value, get_proper_cursor


class CTkSectionViewThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int
    border_spacing: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color_header: TransparentColorType
    fg_color: TransparentColorType
    top_fg_color: ColorType
    hover_color: ColorType
    hover: bool
    open_symbol: SymbolType   #when clicked, the section will open
    close_symbol: SymbolType  #when clicked, the section will get closed
    symbol: CTkSymbolBoxThemedArgs

class CTkSectionViewArgs(CTkSectionViewThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    max_open: int  #"0" means no limit
    pre_command: Callable[[str], Literal["break"] | None] | None
    command: Callable[[str], None] | None


class CTkSectionView(CTkFrame):
    """
    A collection of frames that can be open/closed by the user, each one with a header
    frame that contains a name.
    It can be placed in a CTkScrollableFrame, allowing the user to open multiple
    sections and still see them all by scrolling.
    For detailed information check out the documentation.
    """

    _OPEN_INDEX: int = 0
    _CLOSE_INDEX: int = 1

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkSectionViewArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkSectionViewThemedArgs.__annotations__)
        self._theme_sv_info: CTkSectionViewThemedArgs = ThemeManager.get_info("CTkSectionView", theme_key, **theme_args)

        #validity checks
        for key in self._theme_sv_info:
            if "_color" in key:
                self._theme_sv_info[key] = self._check_color_type(self._theme_sv_info[key],
                                                                  transparency=key not in ("top_fg_color", "hover_color"))

        self._theme_sv_info["corner_radius"] = min(self._theme_sv_info["corner_radius"],
                                                   self._theme_sv_info["symbol"]["height"] / 2)

        super().__init__(master=master,
                         width=self._theme_sv_info["width"],
                         height=self._theme_sv_info["height"],
                         bg_color=self._theme_sv_info["bg_color"],
                         fg_color="transparent",
                         corner_radius=0)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._max_open: int = kwargs.pop("max_open", 1)
        self._pre_command: Callable[[str], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)

        self._symbols: dict[str, CTkSymbolBox] = {}
        self._header_frames: dict[str, CTkFrame] = {}
        self._section_frames: dict[str, CTkFrame] = {}
        self._visible_sections: list[str] = []  # list of section names in order of appearance
        self._open_sections: list[str] = [] # list of open section names in order of opening
        self._prev_fg_color: TransparentColorType = self._theme_sv_info["fg_color_header"]

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

    def _configure_corners_for_index(self, index: int) -> None:
        name = self._visible_sections[index]
        header = self._header_frames[name]
        section = self._section_frames[name]
        is_open = name in self._open_sections

        fg_color = header.get_fg_color()
        #header in the first position
        if index == 0:
            #just one closed section
            if len(self._visible_sections) == 1 and not is_open:
                header.configure(corner_radius=self._theme_sv_info["corner_radius"],
                                 background_corner_colors=(self._bg_color, self._bg_color, self._bg_color, self._bg_color))
            else:
                header.configure(corner_radius=self._theme_sv_info["corner_radius"],
                                 background_corner_colors=(self._bg_color, self._bg_color, fg_color, fg_color))
        #header in the last position and it is closed
        elif index == len(self._visible_sections) - 1 and not is_open:
            header.configure(corner_radius=self._theme_sv_info["corner_radius"],
                             background_corner_colors=(fg_color, fg_color, self._bg_color, self._bg_color))
        else:
            header.configure(corner_radius=0,
                             background_corner_colors=None)

        #section in last position
        if index == len(self._visible_sections) - 1:
            fg_color = section.get_fg_color()
            section.configure(corner_radius=self._theme_sv_info["corner_radius"],
                              background_corner_colors=(fg_color, fg_color, self._bg_color, self._bg_color))
        else:
            section.configure(corner_radius=0,
                              background_corner_colors=None)

    def _update_geometry(self) -> None:
        self.grid_columnconfigure(0, weight=1)
        border_spacing = self._theme_sv_info["border_spacing"]
        section_spacing = self._theme_sv_info["internal_spacing"]

        for n, name in enumerate(self._visible_sections):
            self._header_frames[name].grid(row=2 * n, column=0, sticky="nsew", pady=(0 if n == 0 else section_spacing, 0))
            self._update_section_geometry(name, n)

            self._header_frames[name].grid_columnconfigure(0, weight=1)
            self._symbols[name].grid(row=0, column=0, sticky="nsew", padx=border_spacing)

    def _update_section_geometry(self, name: str, index: int | None = None) -> None:
        if index is None:
            index = self._visible_sections.index(name)
        if name in self._open_sections:
            self._section_frames[name].grid(row=2 * index + 1, column=0, sticky="nsew")
        else:
            self._section_frames[name].grid_forget()

    def _on_enter(self, name: str, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL and self._theme_sv_info["hover"] and name in self._header_frames:
            self._prev_fg_color = self._header_frames[name].cget("fg_color")
            self._header_frames[name].configure(fg_color=self._theme_sv_info["hover_color"])
            self._configure_corners_for_index(self._visible_sections.index(name))

    def _on_leave(self, name: str, _: tkinter.Event | None = None) -> None:
        if self._theme_sv_info["hover"] and name in self._visible_sections:
            self._header_frames[name].configure(fg_color=self._prev_fg_color)
            self._configure_corners_for_index(self._visible_sections.index(name))

    def winfo_children(self) -> list[tkinter.Widget]:
        """ winfo_children of CTkSectionView without headers,
        because they are not children but part of the CTkSectionView itself """

        child_widgets = super().winfo_children()
        for frame in self._header_frames.values():
            try:
                child_widgets.remove(frame)
            except ValueError:
                pass
        return child_widgets

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkSectionViewArgs]) -> None:
        require_corners = False
        if "corner_radius" in kwargs:
            self._theme_sv_info["corner_radius"] = kwargs.pop("corner_radius")
            require_corners = True

        if "border_spacing" in kwargs:
            self._theme_sv_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "internal_spacing" in kwargs:
            self._theme_sv_info["internal_spacing"] = kwargs.pop("internal_spacing")
            self._update_geometry()

        if "fg_color_header" in kwargs:
            fg_color = self._check_color_type(kwargs.pop("fg_color_header"), transparency=True)
            self._theme_sv_info["fg_color_header"] = fg_color
            self._prev_fg_color = fg_color
            require_corners = True
            for header in self._header_frames.values():
                header.configure(fg_color=fg_color)

        if "fg_color" in kwargs:
            fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            self._theme_sv_info["fg_color"] = fg_color
            require_corners = True
            for section in self._section_frames.values():
                section.configure(fg_color=fg_color)

        if "hover_color" in kwargs:
            self._theme_sv_info["hover_color"] = self._check_color_type(kwargs.pop("hover_color"))

        if "hover" in kwargs:
            self._theme_sv_info["hover"] = kwargs.pop("hover")

        require_symbols = False
        if "open_symbol" in kwargs:
            self._theme_sv_info["open_symbol"] = kwargs.pop("open_symbol")
            require_symbols = True
        if "close_symbol" in kwargs:
            self._theme_sv_info["close_symbol"] = kwargs.pop("close_symbol")
            require_symbols = True
        if require_symbols:
            values = [self._theme_sv_info["open_symbol"], self._theme_sv_info["close_symbol"]]
            for name, symbol in self._symbols.items():
                symbol.configure(values=values)
                symbol.set(index=self._CLOSE_INDEX if name in self._open_sections else self._OPEN_INDEX)

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            for symbol in self._symbols.values():
                symbol.configure(state=self._state)
            if cursor := get_proper_cursor("normal" if self._state != tkinter.NORMAL else "clickable"):
                for header in self._header_frames.values():
                    header.configure(cursor=cursor)

        if "max_open" in kwargs:
            self._max_open = kwargs.pop("max_open")
            while len(self._open_sections) > self._max_open > 0:
                self.close(self._open_sections[0])

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "symbol" in kwargs:
            symbol_kwargs = kwargs.pop("symbol")
            deep_update(self._theme_sv_info["symbol"], symbol_kwargs)
            for symbol in self._symbols.values():
                symbol.configure(**symbol_kwargs)

        super().configure(require_redraw=require_redraw, **kwargs)
        if require_corners:
            for n in range(len(self._visible_sections)):
                self._configure_corners_for_index(n)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "max_open":
            return self._max_open
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_sv_info and attribute_name not in CTkWidgetArgs.__annotations__:
            return self._theme_sv_info[attribute_name]
        elif attribute_name.startswith("symbol_"):
            return first_value(self._symbols).cget(attribute_name.removeprefix("symbol_"))
        else:
            return super().cget(attribute_name)

    def section(self, name: str) -> CTkFrame:
        """ Returns reference to the section with given name. """
        if name in self._section_frames:
            return self._section_frames[name]
        else:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

    def header(self, name: str) -> CTkFrame:
        """ Returns reference to the section's header with given name. """
        if name in self._header_frames:
            return self._header_frames[name]
        else:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

    def symbol(self, name: str) -> CTkFrame:
        """ Returns reference to the CTkSymbolBox widget inside the section's header with given name. """
        if name in self._symbols:
            return self._symbols[name]
        else:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

    def insert(self, name: str, index: int | None = None) -> CTkFrame:
        """ Creates new section with given name and returns it.\n
        If an index is provided, the new section is placed at that position. """
        if name in self._section_frames:
            raise ValueError(f"CTkSectionView already has section named '{name}'")

        #create widgets
        header = CTkFrame(self,
                          width=0,
                          height=0,
                          border_width=0,
                          corner_radius=self._theme_sv_info["corner_radius"],
                          fg_color=self._theme_sv_info["fg_color_header"])
        symbol = CTkSymbolBox(header,
                              text=name,
                              values=[self._theme_sv_info["open_symbol"], self._theme_sv_info["close_symbol"]],
                              state=self._state,
                              hover=False,
                              pre_command=lambda _: "break", #status is only changed by calling set() directly
                              **self._theme_sv_info["symbol"])
        section = CTkFrame(self,
                           width=0,
                           height=10, #if frame is empty, some empty space will be visible
                           border_width=0,
                           corner_radius=self._theme_sv_info["corner_radius"],
                           fg_color=self._theme_sv_info["fg_color"],
                           top_fg_color=self._theme_sv_info["top_fg_color"])

        if cursor := get_proper_cursor("normal" if self._state != tkinter.NORMAL else "clickable"):
            header.configure(cursor=cursor)

        #memorize them
        self._header_frames[name] = header
        self._symbols[name] = symbol
        self._section_frames[name] = section

        #assign callbacks
        header.bind("<Enter>", partial(self._on_enter, name))
        header.bind("<Leave>", partial(self._on_leave, name))
        header.bind("<Button-1>", partial(self.invoke, name))
        symbol.bind("<Button-1>", partial(self.invoke, name))

        if index is not None:
            self.show(name, index)
        return section

    def add(self, name: str) -> CTkFrame:
        """ Appends new section with given name. """
        return self.insert(name, len(self._visible_sections))

    def delete(self, name: str) -> None:
        """ Deletes section by name. """
        self.hide(name)
        self._symbols.pop(name).destroy()
        self._header_frames.pop(name).destroy()
        self._section_frames.pop(name).destroy()

    def hide(self, name: str) -> None:
        """ Hides section by name.\n
        It is NOT deleted: it can be displayed again with show(). """
        if name not in self._section_frames:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

        if name in self._visible_sections:
            was_first = name == self._visible_sections[0]
            was_last = name == self._visible_sections[-1]
            self._visible_sections.remove(name)
            self._header_frames[name].grid_forget()
            if name in self._open_sections:
                self._open_sections.remove(name)
                self._section_frames[name].grid_forget()

            if self._visible_sections:
                if was_first:
                    self._configure_corners_for_index(0)
                if was_last:
                    self._configure_corners_for_index(len(self._visible_sections) - 1)

    def show(self, name: str, index: int | None = None) -> None:
        """ Shows a previously hidden section by name and place it at the provided position. """
        if name not in self._section_frames:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

        if name not in self._visible_sections:
            if index is None:
                index = len(self._visible_sections)
            elif not 0 <= index <= len(self._visible_sections):
                raise ValueError(f"CTkSectionView index {index} not in range of visible list with len {len(self._visible_sections)}")

            self._visible_sections.insert(index, name)
            self._symbols[name].set(index=self._CLOSE_INDEX if name in self._open_sections else self._OPEN_INDEX)

            self._configure_corners_for_index(index)
            if index > 0:
                self._configure_corners_for_index(index - 1)
            if index < len(self._visible_sections) - 1:
                self._configure_corners_for_index(index + 1)

            self._update_geometry()

    def move(self, new_index: int, name: str) -> None:
        """ Moves the section to specified position (it is shown if hidden). """
        self.hide(name)
        self.show(name, new_index)

    def open(self, name: str) -> None:
        """ Opens section by name. """
        if name not in self._section_frames:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

        if name not in self._open_sections:
            self._open_sections.append(name)
            self._symbols[name].set(index=self._CLOSE_INDEX)
            self._configure_corners_for_index(self._visible_sections.index(name))
            self._update_section_geometry(name)

            while len(self._open_sections) > self._max_open > 0:
                self.close(self._open_sections[0])

    def close(self, name: str) -> None:
        """ Closes section by name. """
        if name not in self._section_frames:
            raise ValueError(f"CTkSectionView has no section named '{name}'")

        if name in self._open_sections:
            self._open_sections.remove(name)
            self._symbols[name].set(index=self._OPEN_INDEX)
            self._configure_corners_for_index(self._visible_sections.index(name))
            self._update_section_geometry(name)

    def invoke(self, name: str, _: tkinter.Event | None = None) -> None:
        """ Toggles open status of the provided section.\n
        Can be called to simulate the user who clicks on a specific header. """
        if self._state == tkinter.NORMAL:
            retval = "" if self._pre_command is None else self._pre_command(name)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                if name not in self._open_sections:
                    self.open(name)
                else:
                    self.close(name)

                if self._command is not None:
                    self._command(name)

    def set(self,
            visible_sections: list[str] | None = None,
            open_sections: list[str] | None = None) -> None:
        """ Shows all sections in the provided order and/or changes open sections,
        regardless of the widget's state and admissible values. """
        if visible_sections is not None:
            for name in self._visible_sections:
                self._header_frames[name].grid_forget()
                self._section_frames[name].grid_forget()
            self._visible_sections.clear()
            self._visible_sections.extend(visible_sections)

        if open_sections is not None:
            self._open_sections.clear()
            self._open_sections.extend(open_sections)
        else:
            self._open_sections = [section for section in self._open_sections if section in self._visible_sections]

        for n in range(len(self._visible_sections)):
            self._configure_corners_for_index(n)
        for name, symbol in self._symbols.items():
            symbol.set(index=self._CLOSE_INDEX if name in self._open_sections else self._OPEN_INDEX)
        self._update_geometry()

    def get(self,
            index: int | None = None,
            what: Literal["all", "visible", "open"] = "all") -> str | list[str]:
        """ Returns the names of all/visible/open sections, in the order of creation/display/opening.\n
        If an index is provided, returns the visible section name in that position. """
        if index is not None:
            return self._visible_sections[index]
        elif what == "all":
            return list(self._section_frames.keys())
        elif what == "visible":
            return copy.copy(self._visible_sections)
        elif what == "open":
            return copy.copy(self._open_sections)
        else:
            raise ValueError(f"Option '{what}' unknown.")

    def index(self, name: str | None = None) -> int | list[int]:
        """ Returns the index of all open sections.\n
        If the parameter is provided, returns the associated index or raises ValueError if the section is not found. """
        if name is None:
            return [self._visible_sections.index(name) for name in self._open_sections]
        else:
            return self._visible_sections.index(name)

    def len(self, what: Literal["all", "visible", "open"] = "all") -> int:
        """ Returns the number of all/visible/open sections. """
        if what == "all":
            return len(self._section_frames)
        elif what == "visible":
            return len(self._visible_sections)
        elif what == "open":
            return len(self._open_sections)
        else:
            raise ValueError(f"Option '{what}' unknown.")
