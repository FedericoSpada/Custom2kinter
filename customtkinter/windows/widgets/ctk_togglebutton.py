from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, Unpack

from .core_widget_classes import CTkContainer, CTkToggleable
from .theme import ColorType, TransparentColorType, ThemeManager
from .image import CTkImage, ImageType
from .ctk_button import CTkButton, CTkButtonThemedArgs, CTkButtonArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors, get_proper_cursor


class CTkToggleButtonThemedArgs(CTkButtonThemedArgs, total=False, closed=True):
    #replace 'fg_color' if at least one variant is not "transparent"
    fg_color_checked: TransparentColorType
    fg_color_unchecked: TransparentColorType
    #replace 'hover_color' if both variants are not "transparent"
    hover_color_checked: TransparentColorType
    hover_color_unchecked: TransparentColorType
    #replace 'text' if at least one variant is provided
    text_checked: str
    text_unchecked: str
    #replace 'image' if at least one variant is provided
    image_checked: ImageType
    image_unchecked: ImageType

class CTkToggleButtonArgs(CTkToggleButtonThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    onvalue: int | float | str | bool
    offvalue: int | float | str | bool
    textvariable: tkinter.StringVar | None
    variable: tkinter.Variable | None
    pre_command: Callable[[int | float | str | bool], Literal["break"] | None] | None
    command: Callable[[int | float | str | bool], None] | None
    background_corner_colors: tuple[ColorType, ...] | None


class CTkToggleButton(CTkButton, CTkToggleable):
    """
    A CTkButton with 2 different states (like CTkCheckBox but with the ability to display images and/or text).
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkToggleButtonArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkToggleButtonThemedArgs.__annotations__)
        self._theme_tb_info: CTkToggleButtonThemedArgs = ThemeManager.get_info("CTkToggleButton", theme_key, **theme_args)

        #validity checks
        check_colors(self._theme_tb_info, CTkToggleButtonThemedArgs)

        # images
        self._image_checked: CTkImage = CTkImage.from_parameter(self._theme_tb_info["image_checked"])
        self._image_unchecked: CTkImage = CTkImage.from_parameter(self._theme_tb_info["image_unchecked"])

        # button
        CTkToggleable.__init__(self)
        button_kwargs = {key: self._theme_tb_info[key] for key in CTkButtonThemedArgs.__annotations__}
        CTkButton.__init__(self,
                           master=master,
                           state=kwargs.pop("state", tkinter.NORMAL),
                           command=kwargs.pop("command", None),
                           textvariable=kwargs.pop("textvariable", None),
                           background_corner_colors=kwargs.pop("background_corner_colors", None),
                           **button_kwargs)
        self.animation_duration = 0

        # functionality
        self._pre_command = kwargs.pop("pre_command", None)
        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")

        if "variable" in kwargs:
            self._update_variable(kwargs.pop("variable"))
        else:
            super().configure(**self._get_conditional_arguments())

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

    def _set_cursor(self) -> None:
        if cursor := get_proper_cursor("normal" if super().cget("state") != tkinter.NORMAL else "clickable"):
            self.configure(cursor=cursor)

    def _get_conditional_arguments(self) -> dict[str, Any]:
        info = self._theme_tb_info
        kwargs = {}

        if info["fg_color_checked"] != "transparent" or info["fg_color_unchecked"] != "transparent":
            kwargs["fg_color"] = info["fg_color_checked" if self._check_state else "fg_color_unchecked"]

        if info["hover_color_checked"] != "transparent" and info["hover_color_unchecked"] != "transparent":
            kwargs["hover_color"] = info["hover_color_checked" if self._check_state else "hover_color_unchecked"]

        if info["text_checked"] or info["text_unchecked"]:
            kwargs["text"] = info["text_checked" if self._check_state else "text_unchecked"]

        if self._image_checked or self._image_unchecked:
            kwargs["image"] = self._image_checked if self._check_state else self._image_unchecked

        return kwargs

    def destroy(self) -> None:
        CTkToggleable.destroy(self)
        CTkButton.destroy(self)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkToggleButtonArgs]) -> None:
        require_new_state = False
        require_condargs = False

        check_colors(kwargs, CTkToggleButtonThemedArgs)

        if "fg_color_checked" in kwargs:
            self._theme_tb_info["fg_color_checked"] = kwargs.pop("fg_color_checked")
            require_condargs = True

        if "fg_color_unchecked" in kwargs:
            self._theme_tb_info["fg_color_unchecked"] = kwargs.pop("fg_color_unchecked")
            require_condargs = True

        if "hover_color_checked" in kwargs:
            self._theme_tb_info["hover_color_checked"] = kwargs.pop("hover_color_checked")
            require_condargs = True

        if "hover_color_unchecked" in kwargs:
            self._theme_tb_info["hover_color_unchecked"] = kwargs.pop("hover_color_unchecked")
            require_condargs = True

        if "text_checked" in kwargs:
            self._theme_tb_info["text_checked"] = kwargs.pop("text_checked")
            require_condargs = True

        if "text_unchecked" in kwargs:
            self._theme_tb_info["text_unchecked"] = kwargs.pop("text_unchecked")
            require_condargs = True

        if "image_checked" in kwargs:
            self._image_checked = CTkImage.from_parameter(kwargs.pop("image_checked"))
            require_condargs = True

        if "image_unchecked" in kwargs:
            self._image_unchecked = CTkImage.from_parameter(kwargs.pop("image_unchecked"))
            require_condargs = True

        if "onvalue" in kwargs:
            self._onvalue = kwargs.pop("onvalue")
            require_new_state = True

        if "offvalue" in kwargs:
            self._offvalue = kwargs.pop("offvalue")
            require_new_state = True

        if "variable" in kwargs:
            self._update_variable(kwargs.pop("variable"))
            require_new_state = False  #already changed in _update_variable()

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if require_new_state and self._variable is not None:
            self._check_state = self._variable.get() == self._onvalue
            require_condargs = True
        if require_condargs:
            kwargs.update(self._get_conditional_arguments())
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "image_checked":
            return self._image_checked
        elif attribute_name == "image_unchecked":
            return self._image_unchecked
        elif attribute_name == "onvalue":
            return self._onvalue
        elif attribute_name == "offvalue":
            return self._offvalue
        elif attribute_name == "variable":
            return self._variable
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_tb_info and attribute_name not in CTkButtonArgs.__annotations__:
            return self._theme_tb_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def set(self, value: int | float | str | bool | None = None, state: bool | None = None) -> None:
        super().set(value, state)
        super().configure(**self._get_conditional_arguments())

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """ Toggles the selection status if the widget is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        CTkToggleable.invoke(self)
