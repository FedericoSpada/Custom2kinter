from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .theme import ThemeManager
from .ctk_frame import CTkFrame
from .ctk_segmented_button import CTkSegmentedButton, CTkSegmentedButtonArgs


class CTkTabviewArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    top_fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    anchor: str  #center or combination of n, e, s, w
    segmented_button: CTkSegmentedButtonArgs


class CTkTabview(CTkBaseClass):
    """
    Tabview...
    For detailed information check out the documentation.
    """

    _outer_spacing: int = 10  # px on top or below the button
    _outer_button_overhang: int = 8  # px
    _button_height: int = 26
    _segmented_button_border_width: int = 3

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 state: Literal["normal", "disabled"] = "normal",
                 command: Callable[[str], None] | None = None,
                 **kwargs: Unpack[CTkTabviewArgs]) -> None:

        self._theme_info: CTkTabviewArgs = ThemeManager.get_info("CTkTabview", theme_key, **kwargs)

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

        # determine fg_color of frame: use "top" one if not forced and parent frame has the same fg_color
        self._fg_color: str | tuple[str, str] = self._theme_info["fg_color"]
        if (("fg_color" not in kwargs or "top_fg_color" in kwargs) and
            isinstance(self.master, CTkFrame) and
            self.master._fg_color == self._fg_color):
            self._fg_color = self._theme_info["top_fg_color"]

        #functionality
        self._command: Callable[[str], None] | None = command
        self._tab_dict: dict[str, CTkFrame] = {}
        self._name_list: list[str] = []  # list of unique tab names in order of tabs
        self._current_name: str = ""

        self._canvas = CTkCanvas(master=self,
                                 bg=self._apply_appearance_mode(self._bg_color),
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height - self._outer_spacing - self._outer_button_overhang))
        self._draw_engine = DrawEngine(self._canvas)

        segmented_button_kwargs = self._theme_info["segmented_button"]
        segmented_button_kwargs["corner_radius"] = self._theme_info["corner_radius"]
        self._segmented_button = CTkSegmentedButton(self,
                                                    values=[],
                                                    command=self._segmented_button_callback,
                                                    state=state,
                                                    **segmented_button_kwargs)
        self._configure_segmented_button_background_corners()
        self._configure_grid()
        self._set_grid_canvas()
        self._draw()

    def _segmented_button_callback(self, selected_name: str) -> None:
        self._tab_dict[self._current_name].grid_forget()
        self._current_name = selected_name
        self._set_grid_current_tab()

        if self._command is not None:
            self._command(selected_name)

    def winfo_children(self) -> list[tkinter.Widget]:
        """
        winfo_children of CTkTabview without canvas and segmented button widgets,
        because it's not a child but part of the CTkTabview itself
        """

        child_widgets = super().winfo_children()
        try:
            child_widgets.remove(self._canvas)
            child_widgets.remove(self._segmented_button)
            return child_widgets
        except ValueError:
            return child_widgets

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height - self._outer_spacing - self._outer_button_overhang))
        self._configure_grid()
        self._draw(no_color_updates=True)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height - self._outer_spacing - self._outer_button_overhang))
        self._draw()

    def _configure_segmented_button_background_corners(self) -> None:
        """ needs to be called for changes in fg_color, bg_color """

        if self._fg_color == "transparent":
            self._segmented_button.configure(background_corner_colors=(self._bg_color, self._bg_color, self._bg_color, self._bg_color))
        else:
            if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
                self._segmented_button.configure(background_corner_colors=(self._bg_color, self._bg_color, self._fg_color, self._fg_color))
            else:
                self._segmented_button.configure(background_corner_colors=(self._fg_color, self._fg_color, self._bg_color, self._bg_color))

    def _configure_grid(self) -> None:
        """ create 3 x 4 grid system """

        if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
            self.grid_rowconfigure(0, weight=0, minsize=self._apply_widget_scaling(self._outer_spacing))
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_widget_scaling(self._outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._button_height - self._outer_button_overhang))
            self.grid_rowconfigure(3, weight=1)
        else:
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_widget_scaling(self._button_height - self._outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._outer_button_overhang))
            self.grid_rowconfigure(3, weight=0, minsize=self._apply_widget_scaling(self._outer_spacing))

        self.grid_columnconfigure(0, weight=1)

    def _set_grid_canvas(self) -> None:
        if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
            self._canvas.grid(row=2, rowspan=2, column=0, columnspan=1, sticky="nsew")
        else:
            self._canvas.grid(row=0, rowspan=2, column=0, columnspan=1, sticky="nsew")

    def _set_grid_segmented_button(self) -> None:
        """ needs to be called for changes in corner_radius, anchor """
        anchor = self._theme_info["anchor"].lower()

        if anchor in ("center", "n", "s"):
            self._segmented_button.grid(row=1, rowspan=2, column=0, columnspan=1, padx=self._apply_widget_scaling(self._theme_info["corner_radius"]), sticky="ns")
        elif anchor in ("nw", "w", "sw"):
            self._segmented_button.grid(row=1, rowspan=2, column=0, columnspan=1, padx=self._apply_widget_scaling(self._theme_info["corner_radius"]), sticky="nsw")
        elif anchor in ("ne", "e", "se"):
            self._segmented_button.grid(row=1, rowspan=2, column=0, columnspan=1, padx=self._apply_widget_scaling(self._theme_info["corner_radius"]), sticky="nse")

    def _set_grid_current_tab(self) -> None:
        """ needs to be called for changes in corner_radius, border_width """
        pad = self._apply_widget_scaling(max(self._theme_info["corner_radius"], self._theme_info["border_width"]))

        if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
            self._tab_dict[self._current_name].grid(row=3, column=0, sticky="nsew", padx=pad, pady=pad)
        else:
            self._tab_dict[self._current_name].grid(row=0, column=0, sticky="nsew", padx=pad, pady=pad)

    def _grid_forget_all_tabs(self, exclude_name: str | None = None) -> None:
        for name, frame in self._tab_dict.items():
            if name != exclude_name:
                frame.grid_forget()

    def _create_tab(self) -> CTkFrame:
        color = self._bg_color if self._fg_color == "transparent" else self._fg_color
        new_tab = CTkFrame(self,
                           height=0,
                           width=0,
                           border_width=0,
                           corner_radius=0,
                           fg_color=color,
                           bg_color=color)
        return new_tab

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height - self._outer_spacing - self._outer_button_overhang),
                                                                              self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                              self._apply_widget_scaling(self._theme_info["border_width"]))

        if no_color_updates is False or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)
            fg_color = self._apply_appearance_mode(self._fg_color)
            border_color = self._apply_appearance_mode(self._theme_info["border_color"])

            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts", fill=bg_color, outline=bg_color)
                for tab in self._tab_dict.values():
                    tab.configure(fg_color=bg_color, bg_color=bg_color)
            else:
                self._canvas.itemconfig("inner_parts", fill=fg_color, outline=fg_color)
                for tab in self._tab_dict.values():
                    tab.configure(fg_color=fg_color, bg_color=fg_color)

            self._canvas.itemconfig("border_parts", fill=border_color, outline=border_color)
            self._canvas.configure(bg=bg_color)
            tkinter.Frame.configure(self, bg=bg_color)  # configure bg color of tkinter.Frame, cause canvas does not fill frame

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkTabviewArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            self._set_grid_segmented_button()
            self._set_grid_current_tab()
            self._set_grid_canvas()
            self._configure_segmented_button_background_corners()
            self._segmented_button.configure(corner_radius=self._theme_info["corner_radius"])

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            self._configure_segmented_button_background_corners()
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "segmented" in kwargs:
            self._segmented_button.configure(**kwargs.pop("segmented"))

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._configure_grid()
            self._set_grid_segmented_button()

        if "state" in kwargs:
            self._segmented_button.configure(state=kwargs.pop("state"))

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._segmented_button.cget(attribute_name)
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("segmented_button_"):
            return self._segmented_button.cget(attribute_name.removeprefix("segmented_button_"))
        else:
            return super().cget(attribute_name)

    def tab(self, name: str) -> CTkFrame:
        """ returns reference to the tab with given name """

        if name in self._tab_dict:
            return self._tab_dict[name]
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def insert(self, index: int, name: str) -> CTkFrame:
        """ creates new tab with given name at position index """

        if name not in self._tab_dict:
            # if no tab exists, set grid for segmented button
            if len(self._tab_dict) == 0:
                self._set_grid_segmented_button()

            self._name_list.append(name)
            self._tab_dict[name] = self._create_tab()
            self._segmented_button.insert(index, name)

            # if created tab is only tab select this tab
            if len(self._tab_dict) == 1:
                self._current_name = name
                self._segmented_button.set(self._current_name)
                self._grid_forget_all_tabs()
                self._set_grid_current_tab()

            return self._tab_dict[name]
        else:
            raise ValueError(f"CTkTabview already has tab named '{name}'")

    def add(self, name: str) -> CTkFrame:
        """ appends new tab with given name """
        return self.insert(len(self._tab_dict), name)

    def move(self, new_index: int, name: str) -> None:
        if 0 <= new_index < len(self._name_list):
            if name in self._tab_dict:
                self._segmented_button.move(new_index, name)
            else:
                raise ValueError(f"CTkTabview has no name '{name}'")
        else:
            raise ValueError(f"CTkTabview new_index {new_index} not in range of name list with len {len(self._name_list)}")

    def rename(self, old_name: str, new_name: str) -> None:
        if new_name in self._name_list:
            raise ValueError(f"new_name '{new_name}' already exists")

        # segmented button
        old_index = self._segmented_button.index(old_name)
        self._segmented_button.delete(old_name)
        self._segmented_button.insert(old_index, new_name)

        # name list
        self._name_list[self._name_list.index(old_name)] = new_name

        # tab dictionary
        self._tab_dict[new_name] = self._tab_dict.pop(old_name)

        # update current_name so we don't loose the connection to the frame
        if self._current_name == old_name:
            self._current_name = new_name

    def delete(self, name: str) -> None:
        """ delete tab by name """

        if name in self._tab_dict:
            self._name_list.remove(name)
            self._tab_dict[name].destroy()
            self._tab_dict.pop(name)
            self._segmented_button.delete(name)

            # set current_name to '' and remove segmented button if no tab is left
            if len(self._name_list) == 0:
                self._current_name = ""
                self._segmented_button.grid_forget()

            # if only one tab left, select this tab
            elif len(self._name_list) == 1:
                self._current_name = self._name_list[0]
                self._segmented_button.set(self._current_name)
                self._grid_forget_all_tabs()
                self._set_grid_current_tab()

            # more tabs are left
            else:
                # if current_name is deleted tab, select first tab at position 0
                if self._current_name == name:
                    self.set(self._name_list[0])
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def set(self, name: str) -> None:
        """ select tab by name """

        if name in self._tab_dict:
            self._current_name = name
            self._segmented_button.set(name)
            self._set_grid_current_tab()
            self.after(100, lambda: self._grid_forget_all_tabs(exclude_name=name))
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def get(self, index: int | None = None) -> str:
        """ returns name of selected tab, returns empty string if no tab selected.\n
        if an index is provided, returns the tab name in that position """
        if index is None:
            return self._current_name
        else:
            return self._name_list[index]

    def index(self, name: str | None = None) -> int:
        """ returns index of selected tab, raises ValueError if the tab is missing
        if the parameter is provided, returns the associated index or raises ValueError if no tab is found """
        if name is None:
            return self._name_list.index(self._current_name)
        else:
            return self._name_list.index(name)

    def len(self) -> int:
        """ returns the number of defined tabs """
        return len(self._name_list)
