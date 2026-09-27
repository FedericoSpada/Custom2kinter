from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, Unpack

from .core_widget_classes import CTkContainer
from .theme import ColorType, ThemeManager
from .ctk_label import CTkLabel, CTkLabelThemedArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors, get_proper_cursor


class CTkButtonThemedArgs(CTkLabelThemedArgs, total=False, closed=True):
    hover_color: ColorType
    hover: bool

class CTkButtonArgs(CTkButtonThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    textvariable: tkinter.StringVar | None
    command: Callable[[], None] | None
    background_corner_colors: tuple[ColorType, ...] | None


class CTkButton(CTkLabel):
    """
    Button with rounded corners, border, hover effect, image support, click command and textvariable.
    For detailed information check out the documentation.
    """

    animation_duration: int = 100  #[ms], set 0 to disable it

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkButtonArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkButtonThemedArgs.__annotations__)
        self._theme_bu_info: CTkButtonThemedArgs = ThemeManager.get_info("CTkButton", theme_key, **theme_args)

        #validity checks
        check_colors(self._theme_bu_info, CTkButtonThemedArgs)

        #label
        label_kwargs = {key: self._theme_bu_info[key] for key in CTkLabelThemedArgs.__annotations__}
        super().__init__(master=master,
                         state=kwargs.pop("state", tkinter.NORMAL),
                         textvariable=kwargs.pop("textvariable", None),
                         background_corner_colors=kwargs.pop("background_corner_colors", None),
                         **label_kwargs)

        # functionality
        self._command: Callable[[], None] | None = kwargs.pop("command", None)
        self._click_animation_running: bool = False
        self._mouse_inside: bool = False

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        # configure cursor and initial draw
        self._create_bindings()
        self._set_cursor()

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<ButtonRelease-1>":
            self.bind("<ButtonRelease-1>", self._on_release)

    def _set_cursor(self) -> None:
        if self._command is None or super().cget("state") != tkinter.NORMAL:
            cursor = get_proper_cursor("normal")
        else:
            cursor = get_proper_cursor("clickable")
        if cursor is not None:
            self.configure(cursor=cursor)

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = True
        if self._theme_bu_info["hover"] and super().cget("state") == tkinter.NORMAL:
            hover_color = self._apply_appearance_mode(self._theme_bu_info["hover_color"])

            self._rounded_rect.set_main_color(hover_color)
            self._text_label.configure(bg=hover_color)
            self._image_label.configure(bg=hover_color)

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = False
        self._click_animation_running = False

        fg_color = self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color)

        self._rounded_rect.set_main_color(fg_color)
        self._text_label.configure(bg=fg_color)
        self._image_label.configure(bg=fg_color)

    def _click_animation(self) -> None:
        if self._click_animation_running:
            self._on_enter()

    def _on_release(self, _: tkinter.Event) -> None:
        if self._mouse_inside and super().cget("state") == tkinter.NORMAL:
            if self.animation_duration > 0:
                # change color with .on_leave() and back to normal after some time with click_animation()
                self._on_leave()
                self._click_animation_running = True
                self.after(self.animation_duration, self._click_animation)
            self.invoke()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkButtonArgs]) -> None:
        check_colors(kwargs, CTkButtonThemedArgs)

        if "hover_color" in kwargs:
            self._theme_bu_info["hover_color"] = kwargs.pop("hover_color")
            if self._mouse_inside:
                self._on_enter()

        if "hover" in kwargs:
            self._theme_bu_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")
            self._set_cursor()

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_bu_info and attribute_name not in CTkLabelThemedArgs.__annotations__:
            return self._theme_bu_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def invoke(self) -> None:
        """ Calls command function if button is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        if super().cget("state") == tkinter.NORMAL:
            if self._command is not None:
                self._command()
