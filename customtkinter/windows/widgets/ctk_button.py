from __future__ import annotations

import tkinter
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkContainer, CTkWidget
from .core_rendering import CTkCanvas, BorderedRoundedRect, RoundedRect
from .theme import AnchorType, ColorType, TransparentColorType, ThemeManager
from .font import CTkFont, FontType
from .image import CTkImage, ImageType
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_proper_cursor


class CTkButtonThemedArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    border_color: ColorType
    hover_color: ColorType
    text_color: ColorType
    text_color_disabled: ColorType
    hover: bool
    text: str
    font: FontType
    anchor: AnchorType
    image: ImageType
    compound: Literal["left", "right", "top", "bottom"]

class CTkButtonArgs(CTkButtonThemedArgs, total=False):
    state: Literal["normal", "disabled"]
    textvariable: tkinter.Variable | None
    command: Callable[[], None] | None
    background_corner_colors: tuple[ColorType, ...] | None


class CTkButton(CTkWidget):
    """
    Button with rounded corners, border, hover effect, image support, click command and textvariable.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkButtonArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkButtonThemedArgs.__annotations__)
        self._theme_info: CTkButtonThemedArgs = ThemeManager.get_info("CTkButton", theme_key, **theme_args)

        #validity checks
        for key in self._theme_info:
            if "_color" in key:
                self._theme_info[key] = self._check_color_type(self._theme_info[key],
                                                               transparency=key in ("fg_color", "bg_color"))

        super().__init__(master=master,
                         bg_color=self._theme_info["bg_color"],
                         width=self._theme_info["width"],
                         height=self._theme_info["height"])

        # rendering options
        self._background_corner_colors: tuple[ColorType, ...] | None = kwargs.pop("background_corner_colors", None)

        # canvas
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_scaling(self._desired_width),
                                 height=self._apply_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")
        self._background_corners = RoundedRect(self._canvas)
        self._rounded_rect = BorderedRoundedRect(self._canvas)
        self._bind_targets.append(self._canvas)
        self._focus_target = self._canvas

        # text and font
        self._textvariable: tkinter.Variable | None = kwargs.pop("textvariable", None)
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)
        self._text_label = tkinter.Label(master=self,
                                         font=self._apply_font_scaling(self._font),
                                         text=self._theme_info["text"],
                                         anchor=self._theme_info["anchor"],
                                         padx=0,
                                         pady=0,
                                         borderwidth=1,
                                         textvariable=self._textvariable)
        self._bind_targets.append(self._text_label)

        # image
        self._image: CTkImage = CTkImage.from_parameter(self._theme_info["image"])
        self._image.add_configure_callback(self._update_image)
        self._image_label = tkinter.Label(master=self, anchor=self._theme_info["anchor"])
        self._bind_targets.append(self._image_label)

        # functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", "normal")
        self._command: Callable[[], None] | None = kwargs.pop("command", None)
        self._click_animation_running: bool = False
        self._mouse_inside: bool = False

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        # configure cursor and initial draw
        self._create_bindings()
        self._set_cursor()
        self._update_image()
        self._draw(force_colors_update=True)

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """
        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)
            self._text_label.bind("<Enter>", self._on_enter)
            self._image_label.bind("<Enter>", self._on_enter)
        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)
            self._text_label.bind("<Leave>", self._on_leave)
            self._image_label.bind("<Leave>", self._on_leave)
        if sequence is None or sequence == "<ButtonRelease-1>":
            self._canvas.bind("<ButtonRelease-1>", self._on_release)
            self._text_label.bind("<ButtonRelease-1>", self._on_release)
            self._image_label.bind("<ButtonRelease-1>", self._on_release)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._text_label.configure(font=self._apply_font_scaling(self._font))
        self._canvas.configure(width=self._apply_scaling(self._desired_width),
                               height=self._apply_scaling(self._desired_height))
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
        self._text_label.configure(font=self._apply_font_scaling(self._font))

        # Workaround to force grid to be resized when text changes size.
        # Otherwise grid will lag and only resizes if other mouse action occurs.
        self._canvas.grid_forget()
        self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")

    def _update_image(self) -> None:
        image = self._image.get(self.get_scaling(), self._get_appearance_mode())
        self._image_label.configure(image=image)
        self._update_geometry()

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        self._image.remove_configure_callback(self._update_image)
        super().destroy()

    def _draw(self, force_colors_update: bool = False) -> None:
        super()._draw(force_colors_update)

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

        if self._rounded_rect.info["spacings_changed"]:
            self._update_geometry()

        if force_colors_update or requires_recoloring:
            self._background_corners.raise_()
            self._rounded_rect.raise_()

            fg_color = self._apply_appearance_mode(self._theme_info["fg_color"], if_transparent=self._bg_color)

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_main_color(fg_color)
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]))

            if self._state != tkinter.NORMAL:
                self._text_label.configure(bg=fg_color, fg=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
            else:
                self._text_label.configure(bg=fg_color, fg=self._apply_appearance_mode(self._theme_info["text_color"]))
            self._image_label.configure(bg=fg_color)

    def _update_geometry(self) -> None:
        """ configure grid system (5x5) """

        text_visible = self._textvariable is not None or self._text_label.cget("text") != ""
        image_visible = self._image_label.cget("image") != ""

        # Outer rows and columns have weight of 1000 to overpower the rows and columns of the label and image with weight 1.
        # Rows and columns of image and label need weight of 1 to collapse in case of missing space on the button,
        # so image and label need sticky option to stick together in the center, and therefore outer rows and columns
        # need weight of 100 in case of other anchor than center.
        padding_weights = {}
        for anchor_char in "nsew":
            padding_weights[anchor_char] = 1000
        anchor = self._theme_info["anchor"].lower()
        if anchor != "center":
            for anchor_char in anchor:
                padding_weights[anchor_char] = 0

        spacing = self._rounded_rect.info.get("inscribed_spacing", 0) + self._apply_scaling(self._theme_info["border_spacing"])

        self.grid_rowconfigure(0, weight=padding_weights["n"], minsize=spacing)
        self.grid_rowconfigure(4, weight=padding_weights["s"], minsize=spacing)
        self.grid_columnconfigure(0, weight=padding_weights["w"], minsize=spacing)
        self.grid_columnconfigure(4, weight=padding_weights["e"], minsize=spacing)

        #if at least one of the 2 labels is missing
        if not text_visible or not image_visible:
            self.grid_rowconfigure(1, weight=1)
            self.grid_rowconfigure((2, 3), weight=0, minsize=0)
            self.grid_columnconfigure(1, weight=1)
            self.grid_columnconfigure((2, 3), weight=0, minsize=0)

            if text_visible:
                self._text_label.grid(row=1, column=1)
                self._image_label.grid_forget()
            elif image_visible:
                self._image_label.grid(row=1, column=1)
                self._text_label.grid_forget()
            else:
                self._text_label.grid_forget()
                self._image_label.grid_forget()

        else:
            compound = self._theme_info["compound"]
            image_label_spacing = self._apply_scaling(self._theme_info["internal_spacing"])

            if compound in ("left", "right"):
                self.grid_columnconfigure((1, 3), weight=1)
                self.grid_columnconfigure(2, weight=0, minsize=image_label_spacing)
                self.grid_rowconfigure(1, weight=1)
                self.grid_rowconfigure((2, 3), weight=0, minsize=0)
            else:
                self.grid_rowconfigure((1, 3), weight=1)
                self.grid_rowconfigure(2, weight=0, minsize=image_label_spacing)
                self.grid_columnconfigure(1, weight=1)
                self.grid_columnconfigure((2, 3), weight=0, minsize=0)

            if compound == "left":
                self._image_label.grid(row=1, column=1, sticky="e")
                self._text_label.grid(row=1, column=3, sticky="w")
            elif compound == "right":
                self._text_label.grid(row=1, column=1, sticky="e")
                self._image_label.grid(row=1, column=3, sticky="w")
            elif compound == "top":
                self._image_label.grid(row=1, column=1, sticky="s")
                self._text_label.grid(row=3, column=1, sticky="n")
            else:
                self._text_label.grid(row=1, column=1, sticky="s")
                self._image_label.grid(row=3, column=1, sticky="n")

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkButtonArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "internal_spacing" in kwargs:
            self._theme_info["internal_spacing"] = kwargs.pop("internal_spacing")
            self._update_geometry()

        if "fg_color" in kwargs:
            self._theme_info["fg_color"] = self._check_color_type(kwargs.pop("fg_color"), transparency=True)
            require_redraw = True

        if "hover_color" in kwargs:
            self._theme_info["hover_color"] = self._check_color_type(kwargs.pop("hover_color"))
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

        if "background_corner_colors" in kwargs:
            self._background_corner_colors = kwargs.pop("background_corner_colors")
            require_redraw = True

        if "text" in kwargs:
            self._theme_info["text"] = kwargs.pop("text")
            self._text_label.configure(text=self._theme_info["text"])
            self._update_geometry()

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            self._text_label.configure(textvariable=self._textvariable)
            self._update_geometry()

        if "image" in kwargs:
            self._image.remove_configure_callback(self._update_image)
            self._image = CTkImage.from_parameter(kwargs.pop("image"))
            self._image.add_configure_callback(self._update_image)
            self._update_image()

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._set_cursor()
            require_redraw = True

        if "hover" in kwargs:
            self._theme_info["hover"] = kwargs.pop("hover")

        if "command" in kwargs:
            self._command = kwargs.pop("command")
            self._set_cursor()

        if "compound" in kwargs:
            self._theme_info["compound"] = kwargs.pop("compound")
            self._update_geometry()
            require_redraw = True

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            self._text_label.configure(anchor=self._theme_info["anchor"])
            self._image_label.configure(anchor=self._theme_info["anchor"])
            self._update_geometry()

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "image":
            return self._image
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "background_corner_colors":
            return self._background_corner_colors
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def _set_cursor(self) -> None:
        if self._command is None or self._state != tkinter.NORMAL:
            cursor = get_proper_cursor("normal")
        else:
            cursor = get_proper_cursor("clickable")
        if cursor is not None:
            self.configure(cursor=cursor)

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = True
        if self._theme_info["hover"] and self._state == tkinter.NORMAL:
            hover_color = self._apply_appearance_mode(self._theme_info["hover_color"])

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
        if self._mouse_inside and self._state == tkinter.NORMAL:
            # click animation: change color with .on_leave() and back to normal after 100ms with click_animation()
            self._on_leave()
            self._click_animation_running = True
            self.after(100, self._click_animation)
            self.invoke()

    def invoke(self) -> None:
        """ Calls command function if button is not disabled.\n
        Can be called to simulate the user who clicks on the widget. """
        if self._state == tkinter.NORMAL:
            if self._command is not None:
                self._command()
