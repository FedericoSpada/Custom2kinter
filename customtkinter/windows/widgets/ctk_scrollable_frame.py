from __future__ import annotations

import tkinter
import sys
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack

from .appearance_mode import CTkAppearanceModeBaseClass
from .scaling import CTkScalingBaseClass
from .core_widget_classes import CTkBaseClass
from .theme import ThemeManager
from .ctk_frame import CTkFrame, CTkFrameArgs
from .ctk_scrollbar import CTkScrollbar, CTkScrollbarArgs
from .ctk_slider import CTkSlider
from .ctk_textbox import CTkTextbox
from .ctk_label import CTkLabel, CTkLabelArgs


class CTkScrollableFrameArgs(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    width: int
    height: int
    frame: CTkFrameArgs
    scrollbar: CTkScrollbarArgs
    label: CTkLabelArgs

class CTkScrollableFrame(tkinter.Frame, CTkAppearanceModeBaseClass, CTkScalingBaseClass):
    def __init__(self,
                 master: tkinter.Misc,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkScrollableFrameArgs]) -> None:

        self._theme_info: CTkScrollableFrameArgs = ThemeManager.get_info("CTkScrollableFrame", theme_key, **kwargs)

        frame_kwargs = self._theme_info["frame"]
        frame_kwargs["width"] = 0
        frame_kwargs["height"] = 0
        self._parent_frame = CTkFrame(master=master, **frame_kwargs)
        self._parent_canvas = tkinter.Canvas(master=self._parent_frame, highlightthickness=0)
        self._set_scroll_increments()

        scrollbar_kwargs = self._theme_info["scrollbar"]
        scrollbar_kwargs["orientation"] = self._theme_info["orientation"]
        if self._theme_info["orientation"] == "horizontal":
            self._scrollbar = CTkScrollbar(master=self._parent_frame, command=self._parent_canvas.xview, **scrollbar_kwargs)
            self._parent_canvas.configure(xscrollcommand=self._scrollbar.set)
        elif self._theme_info["orientation"] == "vertical":
            self._scrollbar = CTkScrollbar(master=self._parent_frame, command=self._parent_canvas.yview, **scrollbar_kwargs)
            self._parent_canvas.configure(yscrollcommand=self._scrollbar.set)

        label_kwargs = self._theme_info["label"]
        label_kwargs["corner_radius"] = self._parent_frame.cget("corner_radius")
        self._label = CTkLabel(self._parent_frame, **label_kwargs)

        tkinter.Frame.__init__(self, master=self._parent_canvas, highlightthickness=0)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        self._create_grid()

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._theme_info["width"]),
                                      height=self._apply_widget_scaling(self._theme_info["height"]))

        self.bind("<Configure>", lambda _: self._parent_canvas.configure(scrollregion=self._parent_canvas.bbox("all")))
        self._parent_canvas.bind("<Configure>", self._fit_frame_dimensions_to_canvas)

        if "linux" in sys.platform:
            self.bind_all("<Button-4>", self._mouse_wheel_all, add=True)
            self.bind_all("<Button-5>", self._mouse_wheel_all, add=True)
        else:
            self.bind_all("<MouseWheel>", self._mouse_wheel_all, add=True)

        self.bind_all("<KeyPress-Shift_L>", self._keyboard_shift_press_all, add=True)
        self.bind_all("<KeyPress-Shift_R>", self._keyboard_shift_press_all, add=True)
        self.bind_all("<KeyRelease-Shift_L>", self._keyboard_shift_release_all, add=True)
        self.bind_all("<KeyRelease-Shift_R>", self._keyboard_shift_release_all, add=True)
        self._create_window_id: int = self._parent_canvas.create_window(0, 0, window=self, anchor="nw")

        if self._parent_frame.cget("fg_color") == "transparent":
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
        else:
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

        self._shift_pressed: bool = False

    def destroy(self) -> None:
        tkinter.Frame.destroy(self)
        self._parent_frame.destroy()
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    def _create_grid(self) -> None:
        border_spacing = self._apply_widget_scaling(self._parent_frame.cget("corner_radius") + self._parent_frame.cget("border_width"))

        if self._theme_info["orientation"] == "horizontal":
            border_padding = (0, self._parent_frame.cget("border_width") + 1)
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew", padx=border_spacing, pady=(border_spacing, 0))
            self._scrollbar.grid(row=2, column=0, sticky="nsew", padx=border_spacing, pady=border_padding)

            if self._label.cget("text") != "":
                self._label.grid(row=0, column=0, sticky="ew", padx=border_spacing, pady=border_spacing)
            else:
                self._label.grid_forget()

        elif self._theme_info["orientation"] == "vertical":
            border_padding = (0, self._parent_frame.cget("border_width") + 1)
            self._parent_frame.grid_columnconfigure(0, weight=1)
            self._parent_frame.grid_rowconfigure(1, weight=1)
            self._parent_canvas.grid(row=1, column=0, sticky="nsew", padx=(border_spacing, 0), pady=border_spacing)
            self._scrollbar.grid(row=1, column=1, sticky="nsew", padx=border_padding, pady=border_spacing)

            if self._label.cget("text") != "":
                self._label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=border_spacing, pady=border_spacing)
            else:
                self._label.grid_forget()

    def _set_appearance_mode(self, mode: Literal["light", "dark"]) -> None:
        super()._set_appearance_mode(mode)

        if self._parent_frame.cget("fg_color") == "transparent":
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
        else:
            tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
            self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._theme_info["width"]),
                                      height=self._apply_widget_scaling(self._theme_info["height"]))

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        if width is not None:
            self._theme_info["width"] = width
        if height is not None:
            self._theme_info["height"] = height

        self._parent_canvas.configure(width=self._apply_widget_scaling(self._theme_info["width"]),
                                      height=self._apply_widget_scaling(self._theme_info["height"]))

    def configure(self, **kwargs: Unpack[CTkScrollableFrameArgs]) -> None:
        if "width" in kwargs:
            self._set_dimensions(width=kwargs.pop("width"))

        if "height" in kwargs:
            self._set_dimensions(height=kwargs.pop("height"))

        if "frame" in kwargs:
            frame_kwargs = kwargs.pop("frame")

            if "corner_radius" in frame_kwargs:
                corner_radius = frame_kwargs.pop("corner_radius")
                self._theme_info["frame"]["corner_radius"] = corner_radius
                self._parent_frame.configure(corner_radius=corner_radius)
                if self._label is not None:
                    self._label.configure(corner_radius=corner_radius)
                self._create_grid()

            if "border_width" in frame_kwargs:
                self._theme_info["frame"]["border_width"] = frame_kwargs.pop("border_width")
                self._parent_frame.configure(border_width=self._theme_info["frame"]["border_width"])
                self._create_grid()

            if "fg_color" in frame_kwargs:
                self._theme_info["frame"]["fg_color"] = self._check_color_type(frame_kwargs.pop("fg_color"), transparency=True)
                self._parent_frame.configure(fg_color=self._theme_info["frame"]["fg_color"])

                if self._parent_frame.cget("fg_color") == "transparent":
                    tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
                    self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("bg_color")))
                else:
                    tkinter.Frame.configure(self, bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))
                    self._parent_canvas.configure(bg=self._apply_appearance_mode(self._parent_frame.cget("fg_color")))

                for child in self.winfo_children():
                    if isinstance(child, CTkBaseClass):
                        child.configure(bg_color=self._parent_frame.cget("fg_color"))

            if frame_kwargs:
                self._parent_frame.configure(**frame_kwargs)

        if "scrollbar" in kwargs:
            self._scrollbar.configure(**kwargs.pop("scrollbar"))

        if "label" in kwargs:
            self._label.configure(**kwargs.pop("label"))

        self._parent_frame.configure(**kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "orientation":
            return self._theme_info["orientation"]
        elif attribute_name.startswith("frame_"):
            return self._parent_frame.cget(attribute_name.removeprefix("frame_"))
        elif attribute_name.startswith("scrollbar_"):
            return self._scrollbar.cget(attribute_name.removeprefix("scrollbar_"))
        elif attribute_name.startswith("label_"):
            return self._label.cget(attribute_name.removeprefix("label_"))
        else:
            return self._parent_frame.cget(attribute_name)

    def _fit_frame_dimensions_to_canvas(self, _: tkinter.Event) -> None:
        if self._theme_info["orientation"] == "horizontal":
            self._parent_canvas.itemconfigure(self._create_window_id, height=self._parent_canvas.winfo_height())
        elif self._theme_info["orientation"] == "vertical":
            self._parent_canvas.itemconfigure(self._create_window_id, width=self._parent_canvas.winfo_width())

    def _set_scroll_increments(self) -> None:
        if sys.platform.startswith("win"):
            self._parent_canvas.configure(xscrollincrement=1, yscrollincrement=1)
        elif sys.platform == "darwin":
            self._parent_canvas.configure(xscrollincrement=4, yscrollincrement=8)
        else:
            self._parent_canvas.configure(xscrollincrement=30, yscrollincrement=30)

    def _mouse_wheel_all(self, event: tkinter.Event) -> None:
        if self._check_if_valid_scroll(event.widget):
            if sys.platform.startswith("win"):
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -int(event.delta / 6), "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview("scroll", -int(event.delta / 6), "units")
            elif sys.platform == "darwin":
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview("scroll", -event.delta, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview("scroll", -event.delta, "units")
            else:
                if self._shift_pressed:
                    if self._parent_canvas.xview() != (0.0, 1.0):
                        self._parent_canvas.xview_scroll(-1 if event.num == 4 else 1, "units")
                else:
                    if self._parent_canvas.yview() != (0.0, 1.0):
                        self._parent_canvas.yview_scroll(-1 if event.num == 4 else 1, "units")


    def _keyboard_shift_press_all(self, _: tkinter.Event) -> None:
        self._shift_pressed = True

    def _keyboard_shift_release_all(self, _: tkinter.Event) -> None:
        self._shift_pressed = False

    def _check_if_valid_scroll(self, widget: tkinter.Misc) -> bool:
        if widget == self._parent_canvas:
            return True
        elif isinstance(widget, (CTkScrollbar, CTkSlider, CTkTextbox)):
            return False
        elif isinstance(widget, CTkScrollableFrame):
            return widget._parent_canvas == self._parent_canvas
        elif widget.master is not None:
            return self._check_if_valid_scroll(widget.master)
        else:
            return False

    def pack(self, **kwargs: Any) -> None:
        return self._parent_frame.pack(**kwargs)

    def place(self, **kwargs: Any) -> None:
        return self._parent_frame.place(**kwargs)

    def grid(self, **kwargs: Any) -> None:
        return self._parent_frame.grid(**kwargs)

    def pack_forget(self) -> None:
        return self._parent_frame.pack_forget()

    def place_forget(self) -> None:
        return self._parent_frame.place_forget()

    def grid_forget(self) -> None:
        return self._parent_frame.grid_forget()

    def grid_remove(self) -> None:
        return self._parent_frame.grid_remove()

    def grid_propagate(self, **kwargs: Any) -> bool | None:
        return self._parent_frame.grid_propagate(**kwargs)

    def grid_info(self) -> Any:
        return self._parent_frame.grid_info()

    def lift(self, aboveThis: Any | None = None) -> None:
        return self._parent_frame.lift(aboveThis)

    def lower(self, belowThis: Any | None = None) -> None:
        return self._parent_frame.lower(belowThis)
