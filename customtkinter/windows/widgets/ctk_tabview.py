from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame
from .ctk_segmented_button import CTkSegmentedButton, CTkSegmentedButtonArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkTabviewThemedArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    top_fg_color: ColorType
    border_color: ColorType
    anchor: AnchorType
    segmented_button: CTkSegmentedButtonArgs

class CTkTabviewArgs(CTkTabviewThemedArgs, total=False):
    state: Literal["normal", "disabled"]
    command: Callable[[str], None] | None


class CTkTabview(CTkWidget, CTkContainer):
    """
    Tabview...
    For detailed information check out the documentation.
    """

    _outer_button_overhang: int = 8  # px
    _extra_button_border: int = 8  # px

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkTabviewArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkTabviewThemedArgs.__annotations__)
        self._theme_info: CTkTabviewThemedArgs = ThemeManager.get_info("CTkTabview", theme_key, **theme_args)

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
        CTkContainer.__init__(self,
                              fg_color=self._theme_info["fg_color"])

        # update fg_color: use "top" version if not forced and parent frame has the same fg_color
        # (if _fg_color is "transparent" we don't change it)
        if (("fg_color" not in kwargs or "top_fg_color" in kwargs) and
            isinstance(self.master, CTkContainer) and
            self.master.get_fg_color() == self._fg_color):
            self._fg_color = self._theme_info["top_fg_color"]

        #functionality
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._tab_dict: dict[str, CTkFrame] = {}
        self._name_list: list[str] = []  # list of unique tab names in order of tabs
        self._current_name: str = ""

        self._canvas = CTkCanvas(master=self,
                                 bg=self._apply_appearance_mode(self._bg_color),
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height - self._outer_button_overhang))
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._focus_target = self._canvas

        self._segmented_button = CTkSegmentedButton(self,
                                                    values=[],
                                                    command=self._segmented_button_callback,
                                                    state=kwargs.pop("state", "normal"),
                                                    **self._theme_info["segmented_button"])

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._configure_segmented_button_background_corners()
        self._update_geometry()
        self._draw(force_colors_update=True)

    def _segmented_button_callback(self, selected_name: str) -> None:
        self.set(selected_name)
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

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height - self._outer_button_overhang))
        self._update_geometry()
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height - self._outer_button_overhang))
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

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        if not self._canvas.winfo_exists():
            return

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height - self._apply_scaling(self._outer_button_overhang),
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._rounded_rect.info["spacings_changed"]:
            self._update_geometry_segmented_button()
            self._update_geometry_current_tab()

        if force_colors_update or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)

            self._canvas.configure(bg=bg_color)
            tkinter.Frame.configure(self, bg=bg_color)  # configure bg color of tkinter.Frame, cause canvas does not fill frame
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self.get_fg_color()))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))

    def _update_geometry(self) -> None:
        """ create 3 x 4 grid system """

        self.grid_columnconfigure(0, weight=1)

        if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
            self.grid_rowconfigure(0, weight=0, minsize=0)
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_scaling(self._outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_scaling(self._segmented_button.cget("height") - self._outer_button_overhang))
            self.grid_rowconfigure(3, weight=1)

            self._canvas.grid(row=2, rowspan=2, column=0, columnspan=1, sticky="nsew")
        else:
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_scaling(self._segmented_button.cget("height") - self._outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_scaling(self._outer_button_overhang))
            self.grid_rowconfigure(3, weight=0, minsize=0)

            self._canvas.grid(row=0, rowspan=2, column=0, columnspan=1, sticky="nsew")

    def _update_geometry_segmented_button(self) -> None:
        """ needs to be called for changes in corner_radius, anchor """
        anchor = self._theme_info["anchor"].lower()
        if anchor in ("nw", "w", "sw"):
            sticky = "nsw"
        elif anchor in ("ne", "e", "se"):
            sticky = "nse"
        else:
            sticky = "ns"
        spacing = self._rounded_rect.info.get("flat_spacing", 0) + self._apply_scaling(self._extra_button_border)
        self._segmented_button.grid(row=1, rowspan=2, column=0, columnspan=1,
                                    padx=spacing, sticky=sticky, apply_scaling=False)

    def _update_geometry_current_tab(self) -> None:
        """ needs to be called for changes in corner_radius, border_width """
        if self._current_name:
            row = 3 if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e") else 0
            pad = self._reverse_scaling(self._rounded_rect.info.get("inscribed_spacing", 0))
            self._tab_dict[self._current_name].grid(row=row, column=0, sticky="nsew", padx=pad, pady=pad)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkTabviewArgs]) -> None:
        require_propagate = False

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True
            require_propagate = True

        if "bg_color" in kwargs:
            require_propagate = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._update_geometry()
            require_redraw = True
            require_propagate = True

        if "state" in kwargs:
            self._segmented_button.configure(state=kwargs.pop("state"))

        if "segmented_button" in kwargs:
            self._segmented_button.configure(**kwargs.pop("segmented_button"))

        super().configure(require_redraw=require_redraw, **kwargs)
        if require_propagate:
            self.propagate_fg_color(self.winfo_children())
            self._configure_segmented_button_background_corners()

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

    def get_fg_color(self) -> ColorType:
        if self._fg_color == "transparent":
            return self._bg_color
        else:
            return self._fg_color

    def tab(self, name: str) -> CTkFrame:
        """ Returns reference to the tab with given name. """

        if name in self._tab_dict:
            return self._tab_dict[name]
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def insert(self, index: int, name: str) -> CTkFrame:
        """ Creates new tab with given name at position index. """
        if name in self._tab_dict:
            raise ValueError(f"CTkTabview already has tab named '{name}'")

        self._name_list.append(name)
        self._tab_dict[name] = CTkFrame(self,
                                        height=0,
                                        width=0,
                                        border_width=0,
                                        corner_radius=0,
                                        fg_color="transparent",
                                        bg_color="transparent")
        self._segmented_button.insert(index, name)

        # if created tab is the first one, activate it and set grid for segmented button
        if len(self._tab_dict) == 1:
            self._current_name = name
            self._segmented_button.set(self._current_name)
            self._update_geometry_segmented_button()
            self._update_geometry_current_tab()

        return self._tab_dict[name]

    def add(self, name: str) -> CTkFrame:
        """ Appends new tab with given name. """
        return self.insert(len(self._tab_dict), name)

    def move(self, new_index: int, name: str) -> None:
        if not 0 <= new_index < len(self._name_list):
            raise ValueError(f"CTkTabview new_index {new_index} not in range of name list with len {len(self._name_list)}")
        if name not in self._tab_dict:
            raise ValueError(f"CTkTabview has no name '{name}'")

        self._segmented_button.move(new_index, name)

    def rename(self, old_name: str, new_name: str) -> None:
        if old_name not in self._name_list:
            raise ValueError(f"CTkTabview has no tab named '{old_name}'")
        if new_name in self._name_list:
            raise ValueError(f"CTkTabview new_name '{new_name}' already exists")

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
        """ Deletes tab by name. """
        if name not in self._tab_dict:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

        self._name_list.remove(name)
        self._tab_dict[name].destroy()
        self._tab_dict.pop(name)
        self._segmented_button.delete(name)

        # set current_name to '' and remove segmented button if no tab is left
        if len(self._name_list) == 0:
            self._current_name = ""
            self._segmented_button.grid_forget()
        else:
            # if current_name is deleted tab, select first tab at position 0
            if self._current_name == name:
                self.set(self._name_list[0])

    def set(self, name: str) -> None:
        """ Selects tab by name. """
        if name not in self._tab_dict:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

        self._tab_dict[self._current_name].grid_forget()
        self._current_name = name
        self._update_geometry_current_tab()
        self._segmented_button.set(name)

    def get(self, index: int | None = None) -> str:
        """ Returns name of selected tab, returns empty string if no tab selected.\n
        If an index is provided, returns the tab name in that position. """
        if index is None:
            return self._current_name
        else:
            return self._name_list[index]

    def index(self, name: str | None = None) -> int:
        """ Returns index of selected tab, raises ValueError if the tab is missing
        if the parameter is provided, returns the associated index or raises ValueError if no tab is found """
        if name is None:
            name = self._current_name
        return self._name_list.index(name)

    def len(self) -> int:
        """ Returns the number of defined tabs. """
        return len(self._name_list)
