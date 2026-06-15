from __future__ import annotations

import tkinter
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect
from .font import CTkFont, FontType
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .image import CTkImage, ImageType
from .utility import pop_from_dict_by_iterable, check_kwargs_empty


class CTkLabelThemedArgs(TypedDict, total=False, closed=True):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    border_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    text: str
    font: FontType
    anchor: AnchorType
    justify: Literal["left", "center", "right"]
    image: ImageType
    compound: Literal["center", "left", "right", "top", "bottom", "none"]
    wraplength: int

#Explanations can be found here: https://tkdocs.com/shipman/label.html
class ValidTkLabelArgs(TypedDict, total=False, closed=True):
    state: Literal["normal", "disabled"]
    textvariable: tkinter.StringVar | None
    takefocus: bool
    underline: int

class CTkLabelArgs(CTkLabelThemedArgs, ValidTkLabelArgs, total=False, closed=True):
    pass


class CTkLabel(CTkWidget):
    """
    Label with rounded corners.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkLabelArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkLabelThemedArgs.__annotations__)
        self._theme_info: CTkLabelThemedArgs = ThemeManager.get_info("CTkLabel", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # image
        self._image: CTkImage = CTkImage.from_parameter(self._theme_info["image"])
        self._image.add_configure_callback(self._update_image)

        # font
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)

        # configure grid system (1x1)
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, sticky="nswe")
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)

        self._label = tkinter.Label(master=self,
                                    highlightthickness=0,
                                    padx=0,
                                    pady=0,
                                    borderwidth=0,
                                    anchor=self._theme_info["anchor"],
                                    justify=self._theme_info["justify"],
                                    compound=self._theme_info["compound"],
                                    wraplength=self._apply_scaling(self._theme_info["wraplength"]),
                                    text=self._theme_info["text"],
                                    font=self._apply_font_scaling(self._font),
                                    **pop_from_dict_by_iterable(kwargs, ValidTkLabelArgs.__annotations__))
        self._bind_targets.append(self._label)
        self._focus_target = self._label

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._update_image()
        self._draw(force_colors_update=True)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._label.configure(font=self._apply_font_scaling(self._font),
                              wraplength=self._apply_scaling(self._theme_info["wraplength"]))

        self._update_image()
        self._draw()

    def _set_appearance_mode(self) -> None:
        super()._set_appearance_mode()
        self._update_image()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        self._label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, sticky="nswe")

    def _update_image(self) -> None:
        image = self._image.get(self.get_scaling(), self._get_appearance_mode())
        self._label.configure(image=image)

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        self._image.remove_configure_callback(self._update_image)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]))

        if self._rounded_rect.info["spacings_changed"]:
            self._update_geometry()

        if force_colors_update or requires_recoloring:
            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color)

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(fg_color)
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))
            self._label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]),
                                  disabledforeground=self._apply_appearance_mode(self._theme_info["text_color_disabled"]),
                                  bg=fg_color)

    def _update_geometry(self) -> None:
        sticky = self._theme_info["anchor"] if self._theme_info["anchor"] != "center" else ""
        spacing = self._rounded_rect.info.get("inscribed_spacing", 0) + self._apply_scaling(self._theme_info["border_spacing"])
        self._label.grid(row=0, column=0, sticky=sticky, padx=spacing, pady=spacing)

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkLabelArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "border_color" in kwargs:
            self._theme_info["border_color"] = self._check_color_type(kwargs.pop("border_color"))
            require_redraw = True

        if "text_color" in kwargs:
            self._theme_info["text_color"] = self._check_color_type(kwargs.pop("text_color"))
            require_redraw = True

        if "text_color_disabled" in kwargs:
            self._theme_info["text_color_disabled"] = self._check_color_type(kwargs.pop("text_color_disabled"))
            require_redraw = True

        if "text" in kwargs:
            self._theme_info["text"] = kwargs.pop("text")
            self._label.configure(text=self._theme_info["text"])

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "image" in kwargs:
            self._image.remove_configure_callback(self._update_image)
            self._image = CTkImage.from_parameter(kwargs.pop("image"))
            self._image.add_configure_callback(self._update_image)
            self._update_image()

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            self._label.configure(compound=self._theme_info["compound"])

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._label.configure(anchor=self._theme_info["anchor"])
            self._update_geometry()

        if "justify" in kwargs:
            self._theme_info["justify"] = kwargs.pop("justify")
            self._label.configure(justify=self._theme_info["justify"])

        if "wraplength" in kwargs:
            self._theme_info["wraplength"] = kwargs.pop("wraplength")
            self._label.configure(wraplength=self._apply_scaling(self._theme_info["wraplength"]))

        self._label.configure(**pop_from_dict_by_iterable(kwargs, ValidTkLabelArgs.__annotations__))
        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "image":
            return self._image
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name in ValidTkLabelArgs.__annotations__:
            return self._label.cget(attribute_name)
        else:
            return super().cget(attribute_name)
