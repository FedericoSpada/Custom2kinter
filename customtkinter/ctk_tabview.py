from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer
from .core_widget_classes.ctk_widget import CTkWidget, CTkWidgetArgs
from .core_rendering import CTkCanvas, BorderedRoundedRect
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .ctk_frame import CTkFrame
from .ctk_button import CTkButton
from .ctk_segmented_button import CTkSegmentedButton, CTkSegmentedButtonArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors


class CTkTabviewThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    top_fg_color: ColorType  #used if the actual bg_color is equal to fg_color
    border_color: ColorType
    anchor: AnchorType
    segmented_button: CTkSegmentedButtonArgs

class CTkTabviewArgs(CTkTabviewThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    pre_command: Callable[[str], Literal["break"] | None] | None
    command: Callable[[str], None] | None


class CTkTabview(CTkWidget, CTkContainer):
    """
    Tabbed container: a collection of frames displayed one at a time, selected through a
    CTkSegmentedButton placed on the border.

    Create the tabs with add(name) and use the returned frames as 'master' of other widgets;
    change the visible tab with set(name).

    For the full list of arguments and methods, check out the documentation:
    https://custom2kinter.readthedocs.io/stable/containers/CTkTabview.html
    """

    outer_button_overhang: int = 8  # pixels
    extra_button_border: int = 8  # pixels

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkTabviewArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkTabviewThemedArgs.__annotations__)
        self._theme_info: CTkTabviewThemedArgs = ThemeManager.get_info("CTkTabview", theme_key, **theme_args)

        #validity checks
        check_colors(self._theme_info, CTkTabviewThemedArgs)

        CTkWidget.__init__(self,
                           master=master,
                           bg_color=self._theme_info["bg_color"],
                           width=self._theme_info["width"],
                           height=self._theme_info["height"])
        CTkContainer.__init__(self,
                              fg_color=self._theme_info["fg_color"])

        # update fg_color: use "top" version if not forced and parent frame has the same fg_color
        # (if _fg_color is "transparent" we don't change it)
        if (("fg_color" not in theme_args or "top_fg_color" in theme_args) and self._fg_color == self._bg_color):
            self._fg_color = self._theme_info["top_fg_color"]

        #functionality
        self._pre_command: Callable[[str], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._tab_frames: dict[str, CTkFrame] = {}
        self._visible_tab: str = ""

        self._canvas = CTkCanvas(master=self,
                                 bg=self._apply_appearance_mode(self._bg_color),
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height - self.outer_button_overhang))
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._focus_target = self._canvas

        self._segmented_button = CTkSegmentedButton(self,
                                                    values=[],
                                                    pre_command=self.invoke,
                                                    state=kwargs.pop("state", tkinter.NORMAL),
                                                    **self._theme_info["segmented_button"])

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._configure_segmented_button_corners()
        self._update_geometry()
        self._draw(force_colors_update=True)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height - self.outer_button_overhang))
        self._update_geometry()
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height - self.outer_button_overhang))
        self._draw()

    def _configure_segmented_button_corners(self) -> None:
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
                                                        self._current_height - self._apply_scaling(self.outer_button_overhang),
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._rounded_rect.info["spacings_changed"]:
            self._update_segmented_button_geometry()
            self._update_tab_geometry()

        if force_colors_update or requires_recoloring:
            bg_color = self._apply_appearance_mode(self._bg_color)

            self._canvas.configure(bg=bg_color)
            tkinter.Frame.configure(self, bg=bg_color)  # configure bg color of tkinter.Frame, cause canvas does not fill frame
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self.get_fg_color()))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))

    def _update_geometry(self) -> None:
        # configure grid system (4x1)

        self.grid_columnconfigure(0, weight=1)

        if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e"):
            self.grid_rowconfigure(0, weight=0, minsize=0)
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_scaling(self.outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_scaling(self._segmented_button.cget("height") - self.outer_button_overhang))
            self.grid_rowconfigure(3, weight=1)

            self._canvas.grid(row=2, rowspan=2, column=0, columnspan=1, sticky="nsew")
        else:
            self.grid_rowconfigure(0, weight=1)
            self.grid_rowconfigure(1, weight=0, minsize=self._apply_scaling(self._segmented_button.cget("height") - self.outer_button_overhang))
            self.grid_rowconfigure(2, weight=0, minsize=self._apply_scaling(self.outer_button_overhang))
            self.grid_rowconfigure(3, weight=0, minsize=0)

            self._canvas.grid(row=0, rowspan=2, column=0, columnspan=1, sticky="nsew")

    def _update_segmented_button_geometry(self) -> None:
        anchor = self._theme_info["anchor"].lower()
        if anchor in ("nw", "w", "sw"):
            sticky = "nsw"
        elif anchor in ("ne", "e", "se"):
            sticky = "nse"
        else:
            sticky = "ns"
        spacing = self._rounded_rect.info.get("flat_spacing", 0) + self._apply_scaling(self.extra_button_border)
        self._segmented_button.grid(row=1, rowspan=2, column=0, columnspan=1,
                                    padx=spacing, sticky=sticky, apply_scaling=False)

    def _update_tab_geometry(self) -> None:
        if self._visible_tab:
            row = 3 if self._theme_info["anchor"].lower() in ("center", "w", "nw", "n", "ne", "e") else 0
            pad = self._reverse_scaling(self._rounded_rect.info.get("inscribed_spacing", 0))
            self._tab_frames[self._visible_tab].grid(row=row, column=0, sticky="nsew", padx=pad, pady=pad)

    def winfo_children(self) -> list[tkinter.Widget]:
        """
        Returns the list of the children widgets of the view.
        The Canvas and CTkSegmentedButton are not included,
        because they are not children but part of the view itself.
        """
        child_widgets = super().winfo_children()
        try:
            child_widgets.remove(self._canvas)
            child_widgets.remove(self._segmented_button)
        except ValueError:
            pass
        return child_widgets

    def get_fg_color(self) -> ColorType:
        if self._fg_color == "transparent":
            return self._bg_color
        else:
            return self._fg_color

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkTabviewArgs]) -> None:
        require_propagate = False

        check_colors(kwargs, CTkTabviewThemedArgs)

        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = kwargs.pop("fg_color")
            require_redraw = True
            require_propagate = True

        if "bg_color" in kwargs:
            require_propagate = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = kwargs.pop("border_color")
            require_redraw = True

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

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
            self._configure_segmented_button_corners()

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._segmented_button.cget(attribute_name)
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_info and attribute_name not in CTkWidgetArgs.__annotations__:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("segmented_button_"):
            return self._segmented_button.cget(attribute_name.removeprefix("segmented_button_"))
        else:
            return super().cget(attribute_name)

    def tab(self, name: str) -> CTkFrame:
        """
        Returns the main CTkFrame of the tab with the given name.

        Raises:
            ValueError: if the tab is not found.
        """
        if name in self._tab_frames:
            return self._tab_frames[name]
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def button(self, name: str) -> CTkButton:
        """
        Returns the CTkButton of the tab with the given name.
        It can be used to customize each button individually
        (e.g. to add an image or disable the tab).

        Raises:
            ValueError: if the tab is not found.
        """
        if name in self._tab_frames:
            return self._segmented_button.button(name)
        else:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

    def insert(self, index: int, name: str) -> CTkFrame:
        """
        Creates a new tab with the given name at the position 'index' and returns its main CTkFrame.
        The first created tab is activated automatically.

        Args:
            index: position at which the new tab is placed.
            name: key used to refer to the tab in the other methods (it is also the displayed text).

        Raises:
            ValueError: if the name is already assigned to another tab.
        """
        if name in self._tab_frames:
            raise ValueError(f"CTkTabview already has tab named '{name}'")

        self._tab_frames[name] = CTkFrame(self,
                                          height=0,
                                          width=0,
                                          border_width=0,
                                          corner_radius=0,
                                          fg_color="transparent")
        self._segmented_button.insert(index, name)

        # if created tab is the first one, activate it and set grid for segmented button
        if len(self._tab_frames) == 1:
            self._update_segmented_button_geometry()
            self.set(name)

        return self._tab_frames[name]

    def add(self, name: str) -> CTkFrame:
        """
        Creates a new tab with the given name at the end and returns its main CTkFrame.

        Raises:
            ValueError: if the name is already assigned to another tab.
        """
        return self.insert(len(self._tab_frames), name)

    def move(self, new_index: int, name: str) -> None:
        """
        Moves the tab with the given name to the position 'new_index'.

        Raises:
            ValueError: if the tab is not found or 'new_index' is invalid.
        """
        if not 0 <= new_index < self.len():
            raise ValueError(f"CTkTabview new_index {new_index} not in range of name list with len {self.len()}")
        if name not in self._tab_frames:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

        self._segmented_button.move(new_index, name)

    def rename(self, old_name: str, new_name: str) -> None:
        """
        Changes the name of a tab (it is also the text displayed in the button).

        Raises:
            ValueError: if 'old_name' is not found or 'new_name' is already assigned to another tab.
        """
        if old_name not in self._tab_frames:
            raise ValueError(f"CTkTabview has no tab named '{old_name}'")
        if new_name in self._tab_frames:
            raise ValueError(f"CTkTabview new_name '{new_name}' already exists")

        # segmented button
        old_index = self._segmented_button.index(old_name)
        self._segmented_button.delete(old_name)
        self._segmented_button.insert(old_index, new_name)

        # internal data
        self._tab_frames[new_name] = self._tab_frames.pop(old_name)
        if self._visible_tab == old_name:
            self._visible_tab = new_name

    def delete(self, name: str) -> None:
        """
        Deletes the tab with the given name.

        Raises:
            ValueError: if the tab is not found.
        """
        if name not in self._tab_frames:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

        self._tab_frames.pop(name).destroy()
        self._segmented_button.delete(name)

        # set current_name to '' and remove segmented button if no tab is left
        if self.len() == 0:
            self._visible_tab = ""
            self._segmented_button.grid_forget()
        else:
            # if current_name is deleted tab, select first tab at position 0
            if self._visible_tab == name:
                self.set(self._segmented_button.get(index=0))

    def invoke(self, name: str) -> str:
        """
        Shows the tab with the given name if 'pre_command' doesn't return "break"; then 'command' is invoked.
        Can be called to simulate the user who clicks on a specific button.
        """
        retval = "" if self._pre_command is None else self._pre_command(name)

        #if _pre_command() returns exactly "break", operation is stopped
        if retval != "break":
            self.set(name)

            if self._command is not None:
                self._command(name)

        #segmented_button's state is changed directly using set(), so we block the normal change
        return "break"

    def set(self, name: str) -> None:
        """
        Shows the tab with the given name, regardless of the widget's 'state'.
        No callbacks are invoked.

        Raises:
            ValueError: if the tab is not found.
        """
        if name not in self._tab_frames:
            raise ValueError(f"CTkTabview has no tab named '{name}'")

        if self._visible_tab in self._tab_frames:
            self._tab_frames[self._visible_tab].grid_forget()
        self._visible_tab = name
        self._update_tab_geometry()
        self._segmented_button.set(name)

    def get(self, index: int | None = None) -> str:
        """
        Returns the name of the visible tab (an empty string if there are no tabs).

        Args:
            index: if provided, returns the name of the tab at that position instead.

        Raises:
            IndexError: if 'index' is invalid.
        """
        if index is None:
            return self._visible_tab
        else:
            return self._segmented_button.get(index)

    def index(self, name: str | None = None) -> int:
        """
        Returns the index of the visible tab.

        Args:
            name: if provided, returns the index of that tab instead.

        Raises:
            ValueError: if the tab is not found.
        """
        if name is None:
            name = self._visible_tab
        return self._segmented_button.index(name)

    def len(self) -> int:
        """Returns the number of defined tabs."""
        return self._segmented_button.len()
