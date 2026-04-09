from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .theme import ThemeManager


class CTkFrameArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    top_fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    overwrite_preferred_drawing_method: Literal["polygon_shapes", "font_shapes", "circle_shapes"] | None


class CTkFrame(CTkBaseClass):
    """
    Frame with rounded corners and border.
    Default foreground colors are set according to theme.
    To make the frame transparent set fg_color=None.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 background_corner_colors: tuple[str | tuple[str, str], ...] | None = None,
                 **kwargs: Unpack[CTkFrameArgs]) -> None:

        self._theme_info: CTkFrameArgs = ThemeManager.get_info("CTkFrame", theme_key, **kwargs)

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

        self._background_corner_colors: tuple[str | tuple[str, str], ...] | None = background_corner_colors  # rendering options for DrawEngine

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._current_width),
                                 height=self._apply_widget_scaling(self._current_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
        self._draw_engine = DrawEngine(self._canvas)

        self._draw(no_color_updates=True)

    def winfo_children(self) -> list[tkinter.Widget]:
        """
        winfo_children of CTkFrame without self.canvas widget,
        because it's not a child but part of the CTkFrame itself
        """

        child_widgets = super().winfo_children()
        try:
            child_widgets.remove(self._canvas)
            return child_widgets
        except ValueError:
            return child_widgets

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

        if not self._canvas.winfo_exists():
            return

        if self._background_corner_colors is not None:
            self._draw_engine.draw_background_corners(self._apply_widget_scaling(self._current_width),
                                                      self._apply_widget_scaling(self._current_height))
            self._canvas.itemconfig("background_corner_top_left", fill=self._apply_appearance_mode(self._background_corner_colors[0]))
            self._canvas.itemconfig("background_corner_top_right", fill=self._apply_appearance_mode(self._background_corner_colors[1]))
            self._canvas.itemconfig("background_corner_bottom_right", fill=self._apply_appearance_mode(self._background_corner_colors[2]))
            self._canvas.itemconfig("background_corner_bottom_left", fill=self._apply_appearance_mode(self._background_corner_colors[3]))
        else:
            self._canvas.delete("background_parts")

        requires_recoloring = self._draw_engine.draw_rounded_rect_with_border(self._apply_widget_scaling(self._current_width),
                                                                              self._apply_widget_scaling(self._current_height),
                                                                              self._apply_widget_scaling(self._theme_info["corner_radius"]),
                                                                              self._apply_widget_scaling(self._theme_info["border_width"]),
                                                                              overwrite_preferred_drawing_method=self._theme_info["overwrite_preferred_drawing_method"])

        if no_color_updates is False or requires_recoloring:
            if self._fg_color == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._bg_color),
                                        outline=self._apply_appearance_mode(self._bg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        fill=self._apply_appearance_mode(self._fg_color),
                                        outline=self._apply_appearance_mode(self._fg_color))

            self._canvas.itemconfig("border_parts",
                                    fill=self._apply_appearance_mode(self._theme_info["border_color"]),
                                    outline=self._apply_appearance_mode(self._theme_info["border_color"]))
            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

        # self._canvas.tag_lower("inner_parts")  # maybe unnecessary, I don't know ???
        # self._canvas.tag_lower("border_parts")

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkFrameArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "fg_color" in kwargs:
            self._fg_color = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

            # check if CTk widgets are children of the frame and change their bg_color to new frame fg_color
            for child in self.winfo_children():
                if isinstance(child, CTkBaseClass):
                    child.configure(bg_color=self._fg_color)

        if "bg_color" in kwargs:
            # pass bg_color change to children if fg_color is "transparent"
            if self._fg_color == "transparent":
                for child in self.winfo_children():
                    if isinstance(child, CTkBaseClass):
                        child.configure(bg_color=self._fg_color)

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "fg_color":
            return self._fg_color
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas """
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        self._canvas.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Canvas """
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        self._canvas.unbind(sequence, None)
