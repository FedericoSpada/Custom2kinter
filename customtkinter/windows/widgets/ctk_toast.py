from __future__ import annotations

import tkinter
from dataclasses import dataclass
from typing import Any, Callable
from typing_extensions import Literal, Unpack, TypeAlias

from .core_widget_classes import CTkWidget
from .theme import TransparentColorType, ThemeManager
from .font import CTkFont
from .ctk_floating_frame import CTkFloatingFrame, CTkFloatingFrameArgs, CTkFloatingFrameThemedArgs
from .ctk_label import CTkLabel, CTkLabelArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors, get_monitor_info, opposite_direction, get_string, Stringable


AnchorType: TypeAlias = Literal["ne", "se", "sw", "nw"]


class CTkToastThemedArgs(CTkFloatingFrameThemedArgs, total=False, closed=True):
    fg_color_header: TransparentColorType | None
    border_spacing: int
    internal_spacing: int
    x_offset: int
    y_offset: int
    anchor: AnchorType
    compound: Literal["left", "right", "top", "bottom"]
    duration: int  #[ms], if 0, the widget is closed only when clicked or with close()
    label: CTkLabelArgs

class CTkToastArgs(CTkToastThemedArgs, total=False, closed=True):
    style: Literal["info", "success", "warning", "error"]  #valid only if fg_color_header is None
    close_on_interaction: bool
    pre_command: Callable[[], Literal["break"] | None] | None
    command: Callable[[], None] | None
    title: Stringable | None
    text: Stringable | None


class CTkToast(CTkFloatingFrame):
    """
    Toast notification widget that floats on top of the parent window.
    Shows a message with a colored accent stripe, auto-dismisses after a configurable duration
    or when the user clicks it, and stacks when multiple toasts are active.
    For detailed information check out the documentation.
    """

    fade_out_duration: int = 300  #[ms]
    update_time: int = 40   # interval in [ms], to update transparency on closure

    style_colors = {"info":    "#3B8ED0",
                    "success": "#2CC985",
                    "warning": "#E8A838",
                    "error":   "#E04545"}

    _open_toasts: dict[tuple[tkinter.Misc | None, AnchorType], list[_ToastInfo]] = {}

    def __init__(self,
                 master: CTkWidget | None = None,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkToastArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkToastThemedArgs.__annotations__)
        self._theme_to_info: CTkToastThemedArgs = ThemeManager.get_info("CTkToast", theme_key, **theme_args)

        #validity checks
        if self._theme_to_info["fg_color_header"] is None:
            self._theme_to_info["fg_color_header"] = self.style_colors[kwargs.pop("style", "info")]

        check_colors(self._theme_to_info, CTkToastThemedArgs)

        #frame
        frame_kwargs = {key: self._theme_to_info[key] for key in CTkFloatingFrameThemedArgs.__annotations__}
        super().__init__(master=master, **frame_kwargs)

        #functionality
        self._widget: CTkWidget = master
        self._close_on_interaction: bool = kwargs.pop("close_on_interaction", True)
        self._pre_command: Callable[[], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[], None] | None = kwargs.pop("command", None)
        self._title: Stringable | None = kwargs.pop("title", None)
        self._text: Stringable | None = kwargs.pop("text", None)
        self._after_id: str | None = None

        #labels
        self._title_label = CTkLabel(self, **self._theme_to_info["label"])
        self._text_label = CTkLabel(self, **self._theme_to_info["label"])

        font: CTkFont = self._title_label.cget("font")
        font.configure(weight="bold")

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._update_geometry()
        self._create_bindings()

    def _create_bindings(self, sequence: str | None = None) -> None:
        if sequence is None or sequence == "<Button>":
            self.bind("<Button>", self.invoke, add=True)
        if sequence is None:
            self._title_label.bind("<Button>", self.invoke, add=True)
            self._text_label.bind("<Button>", self.invoke, add=True)

    def _draw(self, force_colors_update: bool = False) -> None:
        compound = self._theme_to_info["compound"]
        if compound in ("top", "bottom"):
            kwargs = {"top_section_height": 0 if compound == "top" else 1e12}
        else:
            kwargs = {"left_section_width": 0 if compound == "left" else 1e12}

        requires_recoloring = self._rounded_rect.update(self._current_width,
                                                        self._current_height,
                                                        self._apply_scaling(self._theme_info["corner_radius"]),
                                                        self._apply_scaling(self._theme_info["border_width"]),
                                                        **kwargs)

        if force_colors_update or requires_recoloring:
            fg_color = self._apply_appearance_mode(self.get_fg_color())
            fg_color_header = self._apply_appearance_mode(self._theme_to_info["fg_color_header"], if_transparent=fg_color)
            not_compound = opposite_direction(compound)

            self._canvas.configure(bg=self._apply_appearance_mode(self._bg_color))
            self._rounded_rect.set_border_color(self._apply_appearance_mode(self._theme_info["border_color"]), not_compound)
            self._rounded_rect.set_main_color(fg_color, not_compound)
            self._rounded_rect.set_border_color(fg_color_header, compound)
            self._rounded_rect.set_main_color(fg_color_header, compound)

    def _update_geometry(self) -> None:
        is_vert = self._theme_to_info["compound"] in ("top", "bottom")
        if self._theme_to_info["fg_color_header"] == "transparent":
            flat_spacing = 0
        else:
            flat_spacing = self._rounded_rect.info["flat_spacing"]
        border_spacing = self._apply_scaling(self._theme_to_info["border_spacing"])
        labels_spacing = self._apply_scaling(self._theme_to_info["internal_spacing"])
        padx = border_spacing + (0 if is_vert else flat_spacing)
        pady = border_spacing + (flat_spacing if is_vert else 0)

        if self._title is not None:
            self._title_label.grid(row=0, column=0, sticky="ew",
                                   padx=padx,
                                   pady=(pady, pady if self._text is None else labels_spacing),
                                   apply_scaling=False)
        else:
            self._title_label.grid_forget()
        if self._text is not None:
            self._text_label.grid(row=1, column=0, sticky="ew",
                                  padx=padx,
                                  pady=(pady if self._title is None else 0, pady),
                                  apply_scaling=False)
        else:
            self._text_label.grid_forget()
        self.update_dimensions()

    def destroy(self) -> None:
        self.close(immediate=True)
        super().destroy()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkToastArgs]) -> None:
        require_geometry = False

        if "fg_color_header" in kwargs:
            self._theme_to_info["fg_color_header"] = kwargs.pop("fg_color_header")
            require_redraw = True

        if "border_spacing" in kwargs:
            self._theme_to_info["border_spacing"] = kwargs.pop("border_spacing")
            require_geometry = True

        if "internal_spacing" in kwargs:
            self._theme_to_info["internal_spacing"] = kwargs.pop("internal_spacing")
            require_geometry = True

        if "x_offset" in kwargs:
            self._theme_to_info["x_offset"] = kwargs.pop("x_offset")

        if "y_offset" in kwargs:
            self._theme_to_info["y_offset"] = kwargs.pop("y_offset")

        if "anchor" in kwargs:
            self._theme_to_info["anchor"] = kwargs.pop("anchor")

        if "compound" in kwargs:
            self._theme_to_info["compound"] = kwargs.pop("compound")
            require_redraw = True
            require_geometry = True

        if "duration" in kwargs:
            self._theme_to_info["duration"] = kwargs.pop("duration")

        if "style" in kwargs:
            self._theme_to_info["fg_color_header"] = self.style_colors[kwargs.pop("style")]
            require_redraw = True

        if "close_on_interaction" in kwargs:
            self._close_on_interaction = kwargs.pop("close_on_interaction")

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "title" in kwargs:
            self._title = kwargs.pop("title")
            require_geometry = True
            if self.is_open() and self._title is not None:
                self._title_label.configure(text=get_string(self._title))

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            require_geometry = True
            if self.is_open() and self._text is not None:
                self._text_label.configure(text=get_string(self._text))

        if "label" in kwargs:
            label_kwargs = kwargs.pop("label")
            self._title_label.configure(**label_kwargs)
            self._text_label.configure(**label_kwargs)

        super().configure(require_redraw=require_redraw, **kwargs)
        if require_geometry:
            self._update_geometry()

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "close_on_interaction":
            return self._close_on_interaction
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name == "title":
            return self._title
        elif attribute_name == "text":
            return self._text
        elif attribute_name in self._theme_to_info and attribute_name not in CTkFloatingFrameArgs.__annotations__:
            return self._theme_to_info[attribute_name]
        elif attribute_name.startswith("label_"):
            return self._text_label.cget(attribute_name.removeprefix("label_"))
        else:
            return super().cget(attribute_name)

    def show(self) -> None:
        """ Shows the widget or updates the position if already visible. """
        self.close(immediate=True)

        title_str = get_string(self._title)
        text_str = get_string(self._text)
        if title_str is not None:
            self._title_label.configure(text=title_str)
        if text_str is not None:
            self._text_label.configure(text=text_str)

        #if there are only callbacks that returned "", toast is not shown
        if title_str or text_str or (self._title is None and self._text is None):
            key = (self._widget, self._theme_to_info["anchor"])
            info = _ToastInfo(self,
                              x_offset=self._apply_scaling(self._theme_to_info["x_offset"]),
                              y_offset=self._apply_scaling(self._theme_to_info["y_offset"]))

            self._open_toasts.setdefault(key, []).append(info)

            #restore transparency in case of a second opening
            super().configure(transparency=self._theme_to_info["transparency"])

            # schedule auto-closure
            if self._theme_to_info["duration"] > 0:
                self._after_id = self.after(self._theme_to_info["duration"], self.close)

            self._restack(key)

    def close(self, immediate: bool = False) -> None:
        self._unschedule()
        if immediate or self.fade_out_duration <= 0:
            super().close()
            for toasts in self._open_toasts.values():
                try:
                    toasts.remove(self)
                except ValueError:
                    pass
        else:
            delta = (1.0 - self._theme_to_info["transparency"]) * self.update_time / self.fade_out_duration
            self._fade_out(delta)

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """ Closes the widget if the 'pre_command' allows it.\n
        Can be called to simulate the user who clicks on the widget. """
        retval = "" if self._pre_command is None else self._pre_command()

        #if _pre_command() returns exactly "break", operation is stopped
        if retval != "break":
            if self._close_on_interaction:
                self.close()

            if self._command is not None:
                self._command()

    def _fade_out(self, delta: float) -> None:
        transparency = super().cget("transparency") + delta
        if transparency < 1.0:
            super().configure(transparency=transparency)
            self._after_id = self.after(self.update_time, self._fade_out, delta)
        else:
            self.close(immediate=True)

    def _unschedule(self) -> None:
        if self._after_id is not None:
            self.after_cancel(self._after_id)
            self._after_id = None


    @classmethod
    def _restack(cls, key: tuple[tkinter.Misc | None, AnchorType]) -> None:
        widget, anchor = key

        if widget is None:
            root: tkinter.Misc = tkinter._get_default_root()
            try:
                x_left, y_top, x_right, y_bottom = get_monitor_info(root.winfo_rootx(), root.winfo_rooty())
            except Exception:
                x_left = 0
                y_top = 0
                x_right = root.winfo_vrootwidth()
                y_bottom = root.winfo_vrootheight()
        else:
            x_left = widget.winfo_rootx()
            y_top = widget.winfo_rooty()
            x_right = x_left + widget.winfo_width()
            y_bottom = y_top + widget.winfo_height()

        done = False
        while not done:
            y_pos = y_bottom if "s" in anchor else y_top
            sign = -1 if "s" in anchor else +1

            for toastinfo in cls._open_toasts[key]:
                x_pos = (x_right - toastinfo.x_offset) if "e" in anchor else (x_left + toastinfo.x_offset)
                y_pos += sign * toastinfo.y_offset
                toastinfo.toast.open(x_pos, y_pos, anchor)
                y_pos += sign * toastinfo.toast.winfo_height()

            #if the last toast is outside target area, close the oldest toast and reopen the others
            if y_pos <= y_top and sign < 0 or y_pos >= y_bottom and sign > 0:
                cls._open_toasts[key][0].toast.close(immediate=True)
            else:
                done = True


@dataclass()
class _ToastInfo():
    toast: CTkToast
    x_offset: int
    y_offset: int

    def __eq__(self, other: object) -> bool:
        if isinstance(other, _ToastInfo):
            return self.toast == other.toast
        else:
            return self.toast == other
