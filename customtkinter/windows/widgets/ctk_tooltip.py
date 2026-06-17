from __future__ import annotations

import tkinter
from typing import Any, Callable, Iterable
from typing_extensions import Literal, Unpack

from .core_widget_classes import CTkWidget
from .theme import AnchorType, ThemeManager
from .font import CTkFont
from .ctk_floating_frame import CTkFloatingFrame, CTkFloatingFrameArgs, CTkFloatingFrameThemedArgs
from .ctk_label import CTkLabel, CTkLabelArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, get_monitor_info


class CTkToolTipThemedArgs(CTkFloatingFrameThemedArgs, total=False, closed=True):
    border_spacing: int
    internal_spacing: int
    x_offset: int
    y_offset: int
    anchor: Literal["n", "ne", "e", "se", "s", "sw", "w", "nw"]  #"center" not allowed
    delay: int  #[ms], if negative, the widget is shown only when show() is called
    label: CTkLabelArgs

class CTkToolTipArgs(CTkToolTipThemedArgs, total=False, closed=True):
    mode: Literal["master", "mouse", "live_mouse"]
    state: Literal["normal", "disabled"]
    close_on_interaction: bool
    command: Callable[[], Literal["break"] | None] | None
    title: str | Callable[[], str] | None
    text: str | Iterable[str] | Callable[[], str | Iterable[str]] | None


class CTkToolTip(CTkFloatingFrame):
    """
    Frame that appears when the user moves the mouse on the master widget.\n
    It is filled with up to 2 CTkLabels if 'title' and 'text' are provided, but it can contain other widgets as well.\n
    'command' is invoked before the widget is displayed: if "break" is returned, the widget is not shown.\n
    'title' and 'text' can also be Iterable[str] (combined with "\\n" to produce the actual string) or
    functions that are invoked before the widget is displayed to retrieve the value to be shown.\n
    The position of this widget depends on the mode:
    - "master": it is relative to the position of the linked widget (the corner can be changed with 'anchor');
    - "mouse": it is placed where the mouse is at the moment of opening;
    - "live_mouse": it follows the mouse position while it is moving over the linked widget.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkWidget,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkToolTipArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkToolTipThemedArgs.__annotations__)
        self._theme_tt_info: CTkToolTipThemedArgs = ThemeManager.get_info("CTkToolTip", theme_key, **theme_args)

        #validity checks
        for key in self._theme_tt_info:
            if "_color" in key:
                self._theme_tt_info[key] = self._check_color_type(self._theme_tt_info[key],
                                                                  transparency=key == "fg_color")

        #frame
        frame_kwargs = {key: self._theme_tt_info[key] for key in CTkFloatingFrameThemedArgs.__annotations__}
        super().__init__(master=master, **frame_kwargs)

        #functionality
        self._widget: CTkWidget = master
        self._mode: Literal["master", "mouse", "live_mouse"] = kwargs.pop("mode", "master")
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._close_on_interaction: bool = kwargs.pop("close_on_interaction", True)
        self._command: Callable[[], Literal["break"] | None] | None = kwargs.pop("command", None)
        self._title: str | Callable[[], str] | None = kwargs.pop("title", None)
        self._text: str | Iterable[str] | Callable[[], str | Iterable[str]] | None = kwargs.pop("text", None)
        self._after_id: str | None = None

        #labels
        self._title_label = CTkLabel(self, **self._theme_tt_info["label"])
        self._text_label = CTkLabel(self, **self._theme_tt_info["label"])

        font: CTkFont = self._title_label.cget("font")
        font.configure(weight="bold")

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._update_geometry()
        self._create_bindings()

    def _create_bindings(self, sequence: str | None = None) -> None:
        if sequence is None or sequence == "<Enter>":
            self._widget.bind("<Enter>", self._on_enter, add = True)
        if sequence is None or sequence == "<Leave>":
            self._widget.bind("<Leave>", self._on_leave, add = True)
        if self._close_on_interaction:
            if sequence is None or sequence == "<Button>":
                self._widget.bind("<Button>", self._on_leave, add = True)
        if self._mode == "live_mouse":
            if sequence is None or sequence == "<Motion>":
                self._widget.bind("<Motion>", self._on_motion, add = True)

    def _update_geometry(self) -> None:
        border_spacing = self._theme_tt_info["border_spacing"]
        labels_spacing = self._theme_tt_info["internal_spacing"]
        if self._title is not None:
            self._title_label.grid(row=0, column=0, sticky="ew",
                                   padx = border_spacing,
                                   pady = (border_spacing, border_spacing if self._text is None else labels_spacing))
        else:
            self._title_label.grid_forget()
        if self._text is not None:
            self._text_label.grid(row=1, column=0, sticky="ew",
                                  padx = border_spacing,
                                  pady = (border_spacing if self._title is None else 0, border_spacing))
        else:
            self._text_label.grid_forget()
        self.update_dimensions()

    def destroy(self) -> None:
        self._unschedule()
        try:
            self._widget.unbind("<Enter>")
            self._widget.unbind("<Leave>")
            self._widget.unbind("<ButtonPress>")
            self._widget.unbind("<Destroy>")
            if self._mode == "live_mouse":
                self._widget.unbind("<Motion>")
        except tkinter.TclError:
            pass
        super().destroy()

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkToolTipArgs]) -> None:
        require_geometry = False
        require_show = False

        if "border_spacing" in kwargs:
            self._theme_tt_info["border_spacing"] = kwargs.pop("border_spacing")
            require_geometry = True

        if "internal_spacing" in kwargs:
            self._theme_tt_info["internal_spacing"] = kwargs.pop("internal_spacing")
            require_geometry = True

        if "x_offset" in kwargs:
            self._theme_tt_info["x_offset"] = kwargs.pop("x_offset")
            require_show = True

        if "y_offset" in kwargs:
            self._theme_tt_info["y_offset"] = kwargs.pop("y_offset")
            require_show = True

        if "anchor" in kwargs:
            self._theme_tt_info["anchor"] = kwargs.pop("anchor")
            require_show = True

        if "delay" in kwargs:
            self._theme_tt_info["delay"] = kwargs.pop("delay")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            if self._state != tkinter.NORMAL:
                self.close()

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "title" in kwargs:
            self._title = kwargs.pop("title")
            require_geometry = True
            if self.is_open() and self._title is not None:
                self._title_label.configure(text=self._get_string(self._title))

        if "text" in kwargs:
            self._text = kwargs.pop("text")
            require_geometry = True
            if self.is_open() and self._text is not None:
                self._text_label.configure(text=self._get_string(self._text))

        if "label" in kwargs:
            label_kwargs = kwargs.pop("label")
            self._title_label.configure(**label_kwargs)
            self._text_label.configure(**label_kwargs)

        # "mode" is not changeable after creation

        if require_geometry:
            self._update_geometry()
        if require_show and self.is_open():
            self.show()

        super().configure(require_redraw=require_redraw, **kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "mode":
            return self._mode
        elif attribute_name == "state":
            return self._state
        elif attribute_name == "title":
            return self._title
        elif attribute_name == "text":
            return self._text
        elif attribute_name in CTkFloatingFrameArgs.__annotations__:
            return super().cget(attribute_name)
        elif attribute_name in self._theme_tt_info:
            return self._theme_tt_info[attribute_name]
        elif attribute_name.startswith("label_"):
            return self._text_label.cget(attribute_name.removeprefix("label_"))
        else:
            return super().cget(attribute_name)

    def show(self) -> None:
        """ Shows the widget immediately or updates the position if already visible. """
        retval = "" if self._command is None else self._command()

        #if _command() returns exactly "break", tooltip is not shown
        if retval != "break":
            title_str = self._get_string(self._title)
            text_str = self._get_string(self._text)
            if title_str is not None:
                self._title_label.configure(text=title_str)
            if text_str is not None:
                self._text_label.configure(text=text_str)

            #if there are only callbacks that returned "", tooltip is not shown
            if title_str or text_str or (self._title is None and self._text is None):
                if self._mode == "master":
                    x_root, y_root, anchor = self._master_mode()
                else:
                    x_root, y_root, anchor = self._mouse_mode()

                self.open(x_root, y_root, anchor)

    def close(self) -> None:
        self._unschedule()
        super().close()

    def _on_enter(self, _: tkinter.Event) -> None:
        self._unschedule()
        delay = self._theme_tt_info["delay"]
        if self._state == tkinter.NORMAL:
            if delay > 0:
                self._after_id = self._widget.after(delay, self.show)
            elif delay == 0:
                self.show()

    def _on_leave(self, _: tkinter.Event) -> None:
        if self._theme_tt_info["delay"] >= 0:
            self.close()

    def _on_motion(self, _: tkinter.Event) -> None:
        if self.is_open():
            self.show()

    def _unschedule(self) -> None:
        if self._after_id is not None:
            self._widget.after_cancel(self._after_id)
            self._after_id = None

    def _get_string(self, target: str | Iterable[str] | Callable[[], str | Iterable[str]] | None) -> str | None:
        if callable(target):
            target = target()

        if isinstance(target, str):
            string = target
        elif isinstance(target, Iterable):
            string = "\n".join(target)
        elif target is None:
            string = None
        else:
            raise TypeError(f"CTkToolTip title and text must be a string, iterable of strings, or a "
                            f"callable returning them, not {type(target)}.")
        return string

    def _master_mode(self) -> tuple[int, int, AnchorType]:
        self._toplevel.update_idletasks()
        x_widget = self._widget.winfo_rootx()
        y_widget = self._widget.winfo_rooty()
        w_widget = self._widget.winfo_width()
        h_widget = self._widget.winfo_height()
        w_frame = self.winfo_reqwidth()
        h_frame = self.winfo_reqheight()
        try:
            mon_left, mon_top, mon_right, mon_bottom = get_monitor_info(
                self._widget.winfo_pointerx(), self._widget.winfo_pointery()
            )
        except Exception:
            mon_left = 0
            mon_top = 0
            mon_right = self.winfo_vrootwidth()
            mon_bottom = self.winfo_vrootheight()
        x_offset = self._apply_scaling(self._theme_tt_info["x_offset"])
        y_offset = self._apply_scaling(self._theme_tt_info["y_offset"])
        anchor = self._theme_tt_info["anchor"]

        #check if the frame is outside the display horizontally
        if "w" in anchor:
            if x_widget + x_offset + w_frame + x_offset <= mon_right:
                h_anchor = "w"
            else:
                h_anchor = "e"
        elif "e" in anchor:
            if x_widget - x_offset - w_frame - x_offset >= mon_left:
                h_anchor = "e"
            else:
                h_anchor = "w"
        else:
            if x_widget + round(w_widget / 2) + x_offset + round(w_frame / 2) + x_offset > mon_right:
                h_anchor = "e"
            elif x_widget + round(w_widget / 2) - round(w_frame / 2) < mon_left:
                h_anchor = "w"
            else:
                h_anchor = ""

        if h_anchor == "":
            x_root = x_widget + round(w_widget / 2) + x_offset
        else:
            x_root = (x_widget + w_widget - x_offset) if h_anchor == "e" else (x_widget + x_offset)

        #if starting position is still outside the display, clamp to monitor edge
        if x_root > mon_right:
            x_root = mon_right - x_offset
        elif x_root < mon_left:
            x_root = mon_left + x_offset

        #check if the frame is outside the display vertically
        if "n" in anchor:
            if y_widget - y_offset - h_frame - y_offset >= mon_top:
                v_anchor = "s"
            else:
                v_anchor = "n"
        else:
            if y_widget + h_widget + y_offset + h_frame + y_offset <= mon_bottom:
                v_anchor = "n"
            else:
                v_anchor = "s"

        y_root = (y_widget + h_widget + y_offset) if v_anchor == "n" else (y_widget - y_offset)

        return x_root, y_root, v_anchor + h_anchor

    def _mouse_mode(self) -> tuple[int, int, AnchorType]:
        x_mouse = self._widget.winfo_pointerx()
        y_mouse = self._widget.winfo_pointery()
        x_offset = self._apply_scaling(self._theme_tt_info["x_offset"])
        y_offset = self._apply_scaling(self._theme_tt_info["y_offset"])

        anchor = self._theme_tt_info["anchor"]
        if "e" in anchor:
            x_offset *= -1
        if "s" in anchor:
            y_offset *= -1

        return x_mouse + x_offset, y_mouse + y_offset, anchor
