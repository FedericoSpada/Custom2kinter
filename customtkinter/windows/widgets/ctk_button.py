from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable, TYPE_CHECKING
from typing_extensions import Literal, TypedDict, Unpack

from .core_widget_classes import CTkBaseClass
from .core_rendering import CTkCanvas, DrawEngine
from .theme import ThemeManager
from .font.ctk_font import CTkFont, CTkFontArgs
from .image import CTkImage

if TYPE_CHECKING:
    from PIL import ImageTk


class CTkButtonArgs(TypedDict, total=False):
    width: int
    height: int
    corner_radius: int
    border_width: int
    border_spacing: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    text_color_disabled: str | tuple[str, str]
    hover_color: str | tuple[str, str]
    hover: bool
    round_width_to_even_numbers: bool
    round_height_to_even_numbers: bool
    text: str
    font: CTkFontArgs | CTkFont | tuple | str
    anchor: str  #center or combination of n, e, s, w
    compound: Literal["left", "right", "top", "bottom"]


class CTkButton(CTkBaseClass):
    """
    Button with rounded corners, border, hover effect, image support, click command and textvariable.
    For detailed information check out the documentation.
    """

    _image_label_spacing: int = 6

    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 textvariable: tkinter.Variable | None = None,
                 image: CTkImage | ImageTk.PhotoImage | tkinter.PhotoImage | None = None,
                 state: Literal["normal", "disabled"] = "normal",
                 command: Callable[[], None] | None = None,
                 background_corner_colors: tuple[str | tuple[str, str], ...] | None = None,
                 **kwargs: Unpack[CTkButtonArgs]) -> None:

        self._theme_info: CTkButtonArgs = ThemeManager.get_info("CTkButton", theme_key, **kwargs)

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

        self._theme_info["corner_radius"] = min(self._theme_info["corner_radius"], round(self._current_height / 2))

        # rendering options
        self._background_corner_colors: tuple[str | tuple[str, str], ...] | None = background_corner_colors  # rendering options for DrawEngine

        # text and font
        self._textvariable: tkinter.Variable | None = textvariable
        self._font: CTkFont = CTkFont.from_parameter(self._theme_info["font"])
        self._font.add_size_configure_callback(self._update_font)
        self._text_label: tkinter.Label | None = None

        # image
        self._image: CTkImage | ImageTk.PhotoImage | tkinter.PhotoImage | str | None = self._check_image_type(image)
        self._image_label: tkinter.Label | None = None
        if isinstance(self._image, CTkImage):
            self._image.add_configure_callback(self._update_image)

        # functionality
        self._state: Literal["normal", "disabled"] = state
        self._command: Callable[[], None] | None = command
        self._click_animation_running: bool = False
        self._mouse_inside: bool = False

        # canvas and draw engine
        self._canvas = CTkCanvas(master=self,
                                 highlightthickness=0,
                                 width=self._apply_widget_scaling(self._desired_width),
                                 height=self._apply_widget_scaling(self._desired_height))
        self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")
        self._draw_engine = DrawEngine(self._canvas)
        self._draw_engine.set_round_to_even_numbers(self._theme_info["round_width_to_even_numbers"], self._theme_info["round_height_to_even_numbers"])  # rendering options

        # configure cursor and initial draw
        self._create_bindings()
        self._set_cursor()
        self._draw()

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ set necessary bindings for functionality of widget, will overwrite other bindings """

        if sequence is None or sequence == "<Enter>":
            self._canvas.bind("<Enter>", self._on_enter)

            if self._text_label is not None:
                self._text_label.bind("<Enter>", self._on_enter)
            if self._image_label is not None:
                self._image_label.bind("<Enter>", self._on_enter)

        if sequence is None or sequence == "<Leave>":
            self._canvas.bind("<Leave>", self._on_leave)

            if self._text_label is not None:
                self._text_label.bind("<Leave>", self._on_leave)
            if self._image_label is not None:
                self._image_label.bind("<Leave>", self._on_leave)

        if sequence is None or sequence == "<ButtonRelease-1>":
            self._canvas.bind("<ButtonRelease-1>", self._on_release)

            if self._text_label is not None:
                self._text_label.bind("<ButtonRelease-1>", self._on_release)
            if self._image_label is not None:
                self._image_label.bind("<ButtonRelease-1>", self._on_release)

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._create_grid()

        if self._text_label is not None:
            self._text_label.configure(font=self._apply_font_scaling(self._font))

        self._update_image()

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw(no_color_updates=True)

    def _set_appearance_mode(self, mode: Literal["light", "dark"]) -> None:
        super()._set_appearance_mode(mode)
        self._update_image()

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        super()._set_dimensions(width, height)

        self._canvas.configure(width=self._apply_widget_scaling(self._desired_width),
                               height=self._apply_widget_scaling(self._desired_height))
        self._draw()

    def _update_font(self) -> None:
        """ pass font to tkinter widgets with applied font scaling and update grid with workaround """
        if self._text_label is not None:
            self._text_label.configure(font=self._apply_font_scaling(self._font))

            # Workaround to force grid to be resized when text changes size.
            # Otherwise grid will lag and only resizes if other mouse action occurs.
            self._canvas.grid_forget()
            self._canvas.grid(row=0, column=0, rowspan=5, columnspan=5, sticky="nsew")

    def _update_image(self) -> None:
        if self._image_label is not None:
            if isinstance(self._image, CTkImage):
                self._image_label.configure(image=self._image.create_scaled_photo_image(self._get_widget_scaling(),
                                                                                        self._get_appearance_mode()))
            elif self._image is not None:
                self._image_label.configure(image=self._image)

    def destroy(self) -> None:
        self._font.remove_size_configure_callback(self._update_font)
        super().destroy()

    def _draw(self, no_color_updates: bool = False) -> None:
        super()._draw(no_color_updates)

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
                                                                              self._apply_widget_scaling(self._theme_info["border_width"]))

        if no_color_updates is False or requires_recoloring:

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))

            # set color for the button border parts (outline)
            self._canvas.itemconfig("border_parts",
                                    outline=self._apply_appearance_mode(self._theme_info["border_color"]),
                                    fill=self._apply_appearance_mode(self._theme_info["border_color"]))

            # set color for inner button parts
            if self._theme_info["fg_color"] == "transparent":
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._bg_color),
                                        fill=self._apply_appearance_mode(self._bg_color))
            else:
                self._canvas.itemconfig("inner_parts",
                                        outline=self._apply_appearance_mode(self._theme_info["fg_color"]),
                                        fill=self._apply_appearance_mode(self._theme_info["fg_color"]))

        # create text label if text given
        if self._theme_info["text"] is not None and self._theme_info["text"] != "":

            if self._text_label is None:
                self._text_label = tkinter.Label(master=self,
                                                 font=self._apply_font_scaling(self._font),
                                                 text=self._theme_info["text"],
                                                 anchor=self._theme_info["anchor"],
                                                 padx=0,
                                                 pady=0,
                                                 borderwidth=1,
                                                 textvariable=self._textvariable)
                self._create_grid()

                self._text_label.bind("<Enter>", self._on_enter)
                self._text_label.bind("<Leave>", self._on_leave)
                self._text_label.bind("<ButtonRelease-1>", self._on_release)
                self._text_label.bind("<ButtonRelease-1>", self._on_release)

            if no_color_updates is False:
                # set text_label fg color (text color)
                self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]))

                if self._state == tkinter.DISABLED:
                    self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color_disabled"]))
                else:
                    self._text_label.configure(fg=self._apply_appearance_mode(self._theme_info["text_color"]))

                if self._apply_appearance_mode(self._theme_info["fg_color"]) == "transparent":
                    self._text_label.configure(bg=self._apply_appearance_mode(self._bg_color))
                else:
                    self._text_label.configure(bg=self._apply_appearance_mode(self._theme_info["fg_color"]))

        else:
            # delete text_label if no text given
            if self._text_label is not None:
                self._text_label.destroy()
                self._text_label = None
                self._create_grid()

        # create image label if image given
        if self._image is not None:
            if self._image_label is None:
                self._image_label = tkinter.Label(master=self, anchor=self._theme_info["anchor"])
                self._update_image()  # set image
                self._create_grid()

                self._image_label.bind("<Enter>", self._on_enter)
                self._image_label.bind("<Leave>", self._on_leave)
                self._image_label.bind("<ButtonRelease-1>", self._on_release)
                self._image_label.bind("<ButtonRelease-1>", self._on_release)

            if no_color_updates is False:
                # set image_label bg color (background color of label)
                if self._apply_appearance_mode(self._theme_info["fg_color"]) == "transparent":
                    self._image_label.configure(bg=self._apply_appearance_mode(self._bg_color))
                else:
                    self._image_label.configure(bg=self._apply_appearance_mode(self._theme_info["fg_color"]))

        else:
            # delete text_label if no text given
            if self._image_label is not None:
                self._image_label.destroy()
                self._image_label = None
                self._create_grid()

    def _create_grid(self) -> None:
        """ configure grid system (5x5) """

        # Outer rows and columns have weight of 1000 to overpower the rows and columns of the label and image with weight 1.
        # Rows and columns of image and label need weight of 1 to collapse in case of missing space on the button,
        # so image and label need sticky option to stick together in the center, and therefore outer rows and columns
        # need weight of 100 in case of other anchor than center.
        n_padding_weight, s_padding_weight, e_padding_weight, w_padding_weight = 1000, 1000, 1000, 1000
        anchor = self._theme_info["anchor"]
        if anchor != "center":
            if "n" in anchor:
                n_padding_weight, s_padding_weight = 0, 1000
            if "s" in anchor:
                n_padding_weight, s_padding_weight = 1000, 0
            if "e" in anchor:
                e_padding_weight, w_padding_weight = 1000, 0
            if "w" in anchor:
                e_padding_weight, w_padding_weight = 0, 1000

        scaled_minsize_rows = self._apply_widget_scaling(max(self._theme_info["border_width"] + 1, self._theme_info["border_spacing"]))
        scaled_minsize_columns = self._apply_widget_scaling(max(self._theme_info["corner_radius"], self._theme_info["border_width"] + 1, self._theme_info["border_spacing"]))
        compound = self._theme_info["compound"]

        self.grid_rowconfigure(0, weight=n_padding_weight, minsize=scaled_minsize_rows)
        self.grid_rowconfigure(4, weight=s_padding_weight, minsize=scaled_minsize_rows)
        self.grid_columnconfigure(0, weight=e_padding_weight, minsize=scaled_minsize_columns)
        self.grid_columnconfigure(4, weight=w_padding_weight, minsize=scaled_minsize_columns)

        if compound in ("right", "left"):
            self.grid_rowconfigure(2, weight=1)
            if self._image_label is not None and self._text_label is not None:
                self.grid_columnconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._image_label_spacing))
            else:
                self.grid_columnconfigure(2, weight=0, minsize=0)

            self.grid_rowconfigure((1, 3), weight=0)
            self.grid_columnconfigure((1, 3), weight=1)
        else:
            self.grid_columnconfigure(2, weight=1)
            if self._image_label is not None and self._text_label is not None:
                self.grid_rowconfigure(2, weight=0, minsize=self._apply_widget_scaling(self._image_label_spacing))
            else:
                self.grid_rowconfigure(2, weight=0, minsize=0)

            self.grid_columnconfigure((1, 3), weight=0)
            self.grid_rowconfigure((1, 3), weight=1)

        if compound == "right":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=3, sticky="w")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=1, sticky="e")
        elif compound == "left":
            if self._image_label is not None:
                self._image_label.grid(row=2, column=1, sticky="e")
            if self._text_label is not None:
                self._text_label.grid(row=2, column=3, sticky="w")
        elif compound == "top":
            if self._image_label is not None:
                self._image_label.grid(row=1, column=2, sticky="s")
            if self._text_label is not None:
                self._text_label.grid(row=3, column=2, sticky="n")
        elif compound == "bottom":
            if self._image_label is not None:
                self._image_label.grid(row=3, column=2, sticky="n")
            if self._text_label is not None:
                self._text_label.grid(row=1, column=2, sticky="s")

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkButtonArgs]) -> None:
        if "corner_radius" in kwargs:
            self._theme_info["corner_radius"] = kwargs.pop("corner_radius")
            self._create_grid()
            require_redraw = True

        if "border_width" in kwargs:
            self._theme_info["border_width"] = kwargs.pop("border_width")
            self._create_grid()
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._create_grid()
            require_redraw = True

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
            if self._text_label is None:
                require_redraw = True  # text_label will be created in .draw()
            else:
                self._text_label.configure(text=self._theme_info["text"])

        if "font" in kwargs:
            self._font.remove_size_configure_callback(self._update_font)
            self._font = CTkFont.from_parameter(kwargs.pop("font"))
            self._font.add_size_configure_callback(self._update_font)
            self._update_font()

        if "textvariable" in kwargs:
            self._textvariable = kwargs.pop("textvariable")
            if self._text_label is not None:
                self._text_label.configure(textvariable=self._textvariable)

        if "image" in kwargs:
            if isinstance(self._image, CTkImage):
                self._image.remove_configure_callback(self._update_image)
            self._image = self._check_image_type(kwargs.pop("image"))
            if isinstance(self._image, CTkImage):
                self._image.add_configure_callback(self._update_image)
            if self._image_label is not None:
                self._update_image()
            else:
                require_redraw = True

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
            require_redraw = True

        if "anchor" in kwargs:
            self._theme_info["anchor"] = kwargs.pop("anchor")
            if self._text_label is not None:
                self._text_label.configure(anchor=self._theme_info["anchor"])
            if self._image_label is not None:
                self._image_label.configure(anchor=self._theme_info["anchor"])
            self._create_grid()
            require_redraw = True

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "font":
            return self._font
        elif attribute_name == "textvariable":
            return self._textvariable
        elif attribute_name == "image":
            return self._image
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
        if self._cursor_manipulation_enabled:
            if self._state == tkinter.DISABLED:
                if sys.platform == "darwin" and self._command is not None:
                    self.configure(cursor="arrow")
                elif sys.platform.startswith("win") and self._command is not None:
                    self.configure(cursor="arrow")

            elif self._state == tkinter.NORMAL:
                if sys.platform == "darwin" and self._command is not None:
                    self.configure(cursor="pointinghand")
                elif sys.platform.startswith("win") and self._command is not None:
                    self.configure(cursor="hand2")

    def _on_enter(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = True
        if self._theme_info["hover"] is True and self._state == "normal":
            if self._theme_info["hover_color"] is None:
                inner_parts_color = self._theme_info["fg_color"]
            else:
                inner_parts_color = self._theme_info["hover_color"]

            # set color of inner button parts to hover color
            self._canvas.itemconfig("inner_parts",
                                    outline=self._apply_appearance_mode(inner_parts_color),
                                    fill=self._apply_appearance_mode(inner_parts_color))

            # set text_label bg color to button hover color
            if self._text_label is not None:
                self._text_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

            # set image_label bg color to button hover color
            if self._image_label is not None:
                self._image_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

    def _on_leave(self, _: tkinter.Event | None = None) -> None:
        self._mouse_inside = False
        self._click_animation_running = False

        if self._theme_info["fg_color"] == "transparent":
            inner_parts_color = self._bg_color
        else:
            inner_parts_color = self._theme_info["fg_color"]

        # set color of inner button parts
        self._canvas.itemconfig("inner_parts",
                                outline=self._apply_appearance_mode(inner_parts_color),
                                fill=self._apply_appearance_mode(inner_parts_color))

        # set text_label bg color (label color)
        if self._text_label is not None:
            self._text_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

        # set image_label bg color (image bg color)
        if self._image_label is not None:
            self._image_label.configure(bg=self._apply_appearance_mode(inner_parts_color))

    def _click_animation(self) -> None:
        if self._click_animation_running:
            self._on_enter()

    def _on_release(self, _: tkinter.Event) -> None:
        if self._mouse_inside and self._state != tkinter.DISABLED:
            # click animation: change color with .on_leave() and back to normal after 100ms with click_animation()
            self._on_leave()
            self._click_animation_running = True
            self.after(100, self._click_animation)

            if self._command is not None:
                self._command()

    def invoke(self) -> None:
        """ calls command function if button is not disabled """
        if self._state != tkinter.DISABLED:
            if self._command is not None:
                self._command()

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        """ called on the tkinter.Canvas """

        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")

        self._canvas.bind(sequence, func, add=True)
        if self._text_label is not None:
            self._text_label.bind(sequence, func, add=True)
        if self._image_label is not None:
            self._image_label.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        """ called on the tkinter.Label and tkinter.Canvas """

        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")

        self._canvas.unbind(sequence, None)
        if self._text_label is not None:
            self._text_label.unbind(sequence, None)
        if self._image_label is not None:
            self._image_label.unbind(sequence, None)

        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def focus(self) -> None:
        return self._text_label.focus()

    def focus_set(self) -> None:
        return self._text_label.focus_set()

    def focus_force(self) -> None:
        return self._text_label.focus_force()
