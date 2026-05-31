from __future__ import annotations

import tkinter
import sys
from typing import Any, Callable
from typing_extensions import Literal, Unpack

from .appearance_mode import CTkAppearanceModeBaseClass
from .scaling import CTkScalingBaseClass
from .core_widget_classes import CTkContainer
from .theme import ColorType, ThemeManager
from .ctk_frame import CTkFrame, CTkFrameArgs
from .ctk_scrollbar import CTkScrollbar, CTkScrollbarArgs
from .ctk_slider import CTkSlider
from .ctk_textbox import CTkTextbox
from .ctk_label import CTkLabel, CTkLabelArgs


class CTkScrollableFrameArgs(CTkFrameArgs, total=False):
    border_spacing: int
    orientation: Literal["horizontal", "vertical", "both"]
    activate_scrollbars: bool
    scrollbar: CTkScrollbarArgs
    label: CTkLabelArgs


class CTkScrollableFrame(tkinter.Frame, CTkAppearanceModeBaseClass, CTkScalingBaseClass, CTkContainer):

    _scrollbar_update_time: int = 200  # interval in ms, to check if scrollbars are needed

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkScrollableFrameArgs]) -> None:

        self._theme_info: CTkScrollableFrameArgs = ThemeManager.get_info("CTkScrollableFrame", theme_key, **kwargs)

        # parent frame
        # In theory, this IS a CTkFrame, but we can't inherit it because we would inherit tkinter.Frame twice,
        # which is collapsed into just a single one, but we actually need two separate frames.
        frame_kwargs = {key: self._theme_info[key] for key in CTkFrameArgs.__annotations__}
        self._parent_frame = CTkFrame(master=master, **frame_kwargs)
        self._pf_original_configure: Callable = self._parent_frame.configure
        self._parent_frame.configure = self._parent_frame_configure
        self._pf_original_draw: Callable = self._parent_frame._draw
        self._parent_frame._draw = self._parent_frame_draw

        # canvas
        self._parent_canvas = tkinter.Canvas(master=self._parent_frame, highlightthickness=0, width=0, height=0)
        self._set_scroll_increments()

        # scrollbars
        scrollbar_kwargs = self._theme_info["scrollbar"]
        scrollbar_kwargs["length"] = 0

        self._hide_hor_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "horizontal"
        self._hor_scrollbar = CTkScrollbar(self._parent_frame, command=self._parent_canvas.xview, **scrollbar_kwargs)

        self._hide_ver_scrollbar: bool = True
        scrollbar_kwargs["orientation"] = "vertical"
        self._ver_scrollbar = CTkScrollbar(self._parent_frame, command=self._parent_canvas.yview, **scrollbar_kwargs)

        self._parent_canvas.configure(xscrollcommand=self._hor_scrollbar.set, yscrollcommand=self._ver_scrollbar.set)

        # label
        label_kwargs = self._theme_info["label"]
        self._label = CTkLabel(self._parent_frame, **label_kwargs)

        tkinter.Frame.__init__(self, master=self._parent_canvas, highlightthickness=0)
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")
        CTkContainer.__init__(self, fg_color="transparent")

        self._update_geometry()
        self._create_bindings()
        self._window_id: int = self._parent_canvas.create_window(0, 0, window=self, anchor="nw")

        self._loop_after_id: str = self.after(50, self._check_if_scrollbars_needed, True)
        self._draw(force_colors_update=True)

        self._shift_pressed: bool = False

    def _create_bindings(self, sequence: str | None = None) -> None:
        if sequence is None or sequence == "<Configure>":
            #called when a widget is added to the frame
            self.bind("<Configure>", self._set_scrollregion)
            #called when the canvas changes size
            self._parent_canvas.bind("<Configure>", self._fit_frame_dimensions_to_canvas)
        if sequence is None or sequence == "<KeyPress-Shift_L>":
            self.bind_all("<KeyPress-Shift_L>", self._keyboard_shift_press_all, add=True)
        if sequence is None or sequence == "<KeyPress-Shift_R>":
            self.bind_all("<KeyPress-Shift_R>", self._keyboard_shift_press_all, add=True)
        if sequence is None or sequence == "<KeyRelease-Shift_L>":
            self.bind_all("<KeyRelease-Shift_L>", self._keyboard_shift_release_all, add=True)
        if sequence is None or sequence == "<KeyRelease-Shift_R>":
            self.bind_all("<KeyRelease-Shift_R>", self._keyboard_shift_release_all, add=True)
        if "linux" in sys.platform:
            if sequence is None or sequence == "<Button-4>":
                self.bind_all("<Button-4>", self._mouse_wheel_all, add=True)
            if sequence is None or sequence == "<Button-5>":
                self.bind_all("<Button-5>", self._mouse_wheel_all, add=True)
        else:
            if sequence is None or sequence == "<MouseWheel>":
                self.bind_all("<MouseWheel>", self._mouse_wheel_all, add=True)

    def _check_if_scrollbars_needed(self, continue_loop: bool = False) -> None:
        if self._theme_info["activate_scrollbars"]:
            new_hide_hor_scrollbar = self._parent_canvas.xview() == (0.0, 1.0) #horizontal scrollbar not needed
            new_hide_ver_scrollbar = self._parent_canvas.yview() == (0.0, 1.0) #vertical scrollbar not needed
        else:
            new_hide_hor_scrollbar = True
            new_hide_ver_scrollbar = True

        if new_hide_hor_scrollbar != self._hide_hor_scrollbar or new_hide_ver_scrollbar != self._hide_ver_scrollbar:
            self._hide_hor_scrollbar = new_hide_hor_scrollbar
            self._hide_ver_scrollbar = new_hide_ver_scrollbar
            self._update_geometry()

        if self._parent_canvas.winfo_exists() and continue_loop:
            self._loop_after_id = self.after(self._scrollbar_update_time, self._check_if_scrollbars_needed, True)

    def destroy(self) -> None:
        self.after_cancel(self._loop_after_id)
        tkinter.Frame.destroy(self)
        self._parent_frame.destroy()
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    def _update_geometry(self) -> None:
        info = self._parent_frame._rounded_rect.info.get
        hide_label = self._label.cget("text") == ""
        border_spacing = self._apply_scaling(self._theme_info["border_spacing"])
        inscribed_spacing = info("inscribed_spacing", 0)
        border_width = info("border_width", 0)

        canvas_spacing = inscribed_spacing + border_spacing
        mean_spacing = (info("flat_spacing", 0) + inscribed_spacing) / 2 + border_spacing
        label_border = border_width + border_spacing * 2
        scrollbar_border = border_width + border_spacing
        delta_spacing = max(0, mean_spacing - canvas_spacing)

        #force the frame to keep specified dimensions and not shrink to fit its content
        self._parent_frame.grid_propagate(False)

        # configure 3x2 grid
        self._parent_frame.grid_rowconfigure(0, weight=0, minsize=canvas_spacing)
        self._parent_frame.grid_rowconfigure(1, weight=1)
        self._parent_frame.grid_rowconfigure(2, weight=0, minsize=canvas_spacing)
        self._parent_frame.grid_columnconfigure(0, weight=1)
        self._parent_frame.grid_columnconfigure(1, weight=0, minsize=canvas_spacing)

        if not hide_label:
            self._label.grid(row=0, column=0, sticky="sew", columnspan=2,
                             padx=(mean_spacing, mean_spacing),
                             pady=(label_border, border_spacing),
                             apply_scaling=False)
        else:
            self._label.grid_forget()

        self._parent_canvas.grid(row=1, column=0, sticky="nsew", padx=(canvas_spacing, 0))

        if not self._hide_hor_scrollbar:
            self._hor_scrollbar.grid(row=2, column=0, sticky="ew",
                                     padx=(mean_spacing, delta_spacing),
                                     pady=(border_spacing, scrollbar_border),
                                     apply_scaling=False)
        else:
            self._hor_scrollbar.grid_forget()

        if not self._hide_ver_scrollbar:
            self._ver_scrollbar.grid(row=1, column=1, sticky="ns",
                                     padx=(border_spacing, scrollbar_border),
                                     pady=delta_spacing,
                                     apply_scaling=False)
        else:
            self._ver_scrollbar.grid_forget()

    def _set_appearance_mode(self) -> None:
        self._draw(force_colors_update=True)
        super().update_idletasks()

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        self._update_geometry()

    def _draw(self, force_colors_update: bool = False) -> None:
        if force_colors_update:
            fg_color = self._apply_appearance_mode(self._parent_frame.get_fg_color())

            tkinter.Frame.configure(self, bg=fg_color)
            self._parent_canvas.configure(bg=fg_color)

    def _parent_frame_configure(self, **kwargs: Unpack[CTkFrameArgs]) -> None:
        # since this object is not a direct child of its master, when fg_color is propagated,
        # we would interrupt the chain of invocations. To fix it, we intercept the event by
        # replacing the original configure() method of the parent CTkFrame with this function,
        # which calls the original method but also updates this widget and propagates the
        # fg_color to its children
        self._pf_original_configure(**kwargs)
        self._update_geometry()
        self._draw(force_colors_update=True)
        self.propagate_fg_color(self.winfo_children())

    def _parent_frame_draw(self, **kwargs) -> None:
        # to update the geometry properly, we have to intercept the draw event of the parent frame
        # by replacing the original _draw() method of the parent CTkFrame with this function,
        # which calls the original method but also updates the geometry when required
        self._pf_original_draw(**kwargs)
        if self._parent_frame._rounded_rect.info["spacings_changed"]:
            self._update_geometry()

    def configure(self, **kwargs: Unpack[CTkScrollableFrameArgs]) -> None:
        if "border_spacing" in kwargs:
            self._theme_info["border_spacing"] = kwargs.pop("border_spacing")
            self._update_geometry()

        if "activate_scrollbars" in kwargs:
            self._theme_info["activate_scrollbars"] = kwargs.pop("activate_scrollbars")

        if "scrollbar" in kwargs:
            scrollbar_kwargs = kwargs.pop("scrollbar")
            self._hor_scrollbar.configure(**scrollbar_kwargs)
            self._ver_scrollbar.configure(**scrollbar_kwargs)

        if "label" in kwargs:
            self._label.configure(**kwargs.pop("label"))

        self._parent_frame.configure(**kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name in CTkFrameArgs.__annotations__:
            return self._parent_frame.cget(attribute_name)
        elif attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        elif attribute_name.startswith("scrollbar_"):
            return self._ver_scrollbar.cget(attribute_name.removeprefix("scrollbar_"))
        elif attribute_name.startswith("label_"):
            return self._label.cget(attribute_name.removeprefix("label_"))
        else:
            raise ValueError(f"'{attribute_name}' is not a supported argument. Look at the documentation for supported arguments.")

    def get_fg_color(self) -> ColorType:
        return self._parent_frame.get_fg_color()

    def _set_scrollregion(self, _: tkinter.Event) -> None:
        self._parent_canvas.configure(scrollregion=self._parent_canvas.bbox("all"))

    def _fit_frame_dimensions_to_canvas(self, event: tkinter.Event) -> None:
        #If the frame can be scrolled just in one direction, we change the dimension
        # of the other one so that the frame is entirely contained in the canvas,
        # so no scroll is needed. Also, this allows the drawn widgets to expand in
        # all available space.
        orientation = self._theme_info["orientation"]
        if orientation == "horizontal":
            self._parent_canvas.itemconfigure(self._window_id, height=event.height)
        elif orientation == "vertical":
            self._parent_canvas.itemconfigure(self._window_id, width=event.width)

    def _set_scroll_increments(self) -> None:
        if sys.platform.startswith("win"):
            self._parent_canvas.configure(xscrollincrement=1, yscrollincrement=1)
        elif sys.platform == "darwin":
            self._parent_canvas.configure(xscrollincrement=4, yscrollincrement=8)
        else:
            self._parent_canvas.configure(xscrollincrement=30, yscrollincrement=30)

    def _mouse_wheel_all(self, event: tkinter.Event) -> None:
        if self._check_if_valid_scroll(event.widget):
            if self._shift_pressed:
                view_method = self._parent_canvas.xview
                view_scroll_method = self._parent_canvas.xview_scroll
            else:
                view_method = self._parent_canvas.yview
                view_scroll_method = self._parent_canvas.yview_scroll

            if view_method() != (0.0, 1.0):
                if sys.platform.startswith("win"):
                    view_method("scroll", -int(event.delta / 6), "units")
                elif sys.platform == "darwin":
                    view_method("scroll", -event.delta, "units")
                else:
                    view_scroll_method(-1 if event.num == 4 else 1, "units")


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
            return widget == self
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
