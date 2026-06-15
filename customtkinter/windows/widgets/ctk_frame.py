from __future__ import annotations

import tkinter
from typing import Any
from typing_extensions import TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import ColorType, TransparentColorType, ThemeManager
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkFrameThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int
    border_width: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    top_fg_color: ColorType
    border_color: ColorType

class CTkFrameArgs(CTkFrameThemedArgs, total=False, closed=True):
    background_corner_colors: tuple[ColorType, ...] | None


class CTkFrame(CTkWidget, CTkContainer):
    """
    Frame with rounded corners and border.
    Default foreground colors are set according to theme.
    To make the frame transparent set fg_color=None.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkFrameArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkFrameThemedArgs.__annotations__)
        self._theme_info: CTkFrameThemedArgs = ThemeManager.get_info("CTkFrame", theme_key, **theme_args)

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

        self._background_corner_colors: tuple[ColorType, ...] | None = kwargs.pop("background_corner_colors", None)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.place(x=0, y=0, relwidth=1, relheight=1)
        self._background_corners = RoundedRect(self._canvas)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._draw(force_colors_update=True)

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

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        if not self._canvas.winfo_exists():
            return

        if self._background_corner_colors is not None:
            if (self._background_corners.update(0, 0,
                                                self._current_width, self._current_height,
                                                0,
                                                self._current_width / 2, self._current_height / 2) or
                force_colors_update):
                for idx, section in enumerate(("top_left", "top_right", "bottom_right", "bottom_left")):
                    self._background_corners.set_color(self._apply_appearance_mode(self._background_corner_colors[idx]), section)
        else:
            self._background_corners.delete()

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if force_colors_update or requires_recoloring:
            self._background_corners.raise_()
            self._rounded_rect.raise_()

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))
            self._rounded_rect.set_main_color(self._apply_appearance_mode(self.get_fg_color()))

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkFrameArgs]) -> None:
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
            #only if fg_color is transparent, bg_color is actually used by children widgets
            if self._fg_color == "transparent":
                require_propagate = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)
        if require_propagate:
            self.propagate_fg_color(self.winfo_children())

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def get_fg_color(self) -> ColorType:
        if self._fg_color == "transparent":
            return self._bg_color
        else:
            return self._fg_color
