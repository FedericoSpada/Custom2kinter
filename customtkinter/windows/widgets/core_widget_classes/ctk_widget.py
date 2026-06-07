from __future__ import annotations

import tkinter
import tkinter.ttk as ttk
from abc import ABC, abstractmethod
from typing import Any, Callable
from typing_extensions import Literal, TypedDict, Unpack

from ..appearance_mode import CTkAppearanceModeBaseClass
from ..scaling import CTkScalingBaseClass
from .ctk_container import CTkContainer
from ..theme import AnchorType, ColorType, TransparentColorType
from ..utility import pop_from_dict_by_iterable, check_kwargs_empty


class ValidTkFrameArgs(TypedDict, total=False):
    cursor: str

class CTkWidgetArgs(ValidTkFrameArgs, total=False):
    width: int
    height: int
    bg_color: TransparentColorType


class CTkWidget(tkinter.Frame, CTkAppearanceModeBaseClass, CTkScalingBaseClass, ABC):
    """ Base class of every CTk widget, handles the dimensions, bg_color,
        appearance_mode changes, scaling, bg changes of master if master is not a CTk widget """

    def __init__(self,
                 master: CTkContainer,
                 **kwargs: Unpack[CTkWidgetArgs]) -> None:

        # call init methods of super classes
        tkinter.Frame.__init__(self,
                               master=master,
                               width=0,
                               height=0,
                               **pop_from_dict_by_iterable(kwargs, ValidTkFrameArgs.__annotations__))
        CTkAppearanceModeBaseClass.__init__(self)
        CTkScalingBaseClass.__init__(self, scaling_type="widget")

        # dimensions
        # _desired_width and _desired_height represent desired size set by width and height and
        # don't consider the scaling factor
        self._desired_width: int | float = kwargs.pop("width", 0)
        self._desired_height: int | float = kwargs.pop("height", 0)
        # _current_width and _current_height represent the actual size of the widget,
        # which consider both the scaling factor and the stretch behaviour mandated by the geometry manager
        self._current_width: int | float = self._apply_scaling(self._desired_width)
        self._current_height: int | float = self._apply_scaling(self._desired_height)

        super().configure(width=self._current_width, height=self._current_height)

        # background color: it is used to fill the whole area of the widget.
        # if requested color is "transparent", it is set equal to the fg_color of the parent widget,
        # so that this widget seems to be transparent
        bg_color = kwargs.pop("bg_color", "transparent")
        self._bg_color: ColorType = self._detect_color_of_master() if bg_color == "transparent" else self._check_color_type(bg_color)

        # save latest geometry function and kwargs
        class GeometryCallDict(TypedDict):
            function: Callable
            apply_scaling: bool
            kwargs: dict
        self._last_geometry_manager_call: GeometryCallDict | None = None

        # targets for basic operations that child classes can fill as needed
        self._bind_targets: list[tkinter.Misc] = []
        self._focus_target: tkinter.Misc | None = None

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        # add configure callback to tkinter.Frame
        super().bind("<Configure>", self._update_dimensions_event)

        # overwrite configure methods of master when master is tkinter widget, so that bg changes get applied on child CTk widget as well
        if (isinstance(self.master, (tkinter.Tk, tkinter.Toplevel, tkinter.Frame, tkinter.LabelFrame, ttk.Frame, ttk.LabelFrame, ttk.Notebook)) and
            not isinstance(self.master, (CTkContainer, CTkWidget))):
            master_old_configure = self.master.config

            def new_configure(*args: Any, **kwargs: Any) -> None:
                if "bg" in kwargs:
                    self.configure(bg_color=kwargs["bg"])
                elif "background" in kwargs:
                    self.configure(bg_color=kwargs["background"])

                # args[0] is dict when attribute gets changed by widget[<attribute>] syntax
                elif len(args) > 0 and isinstance(args[0], dict):
                    if "bg" in args[0]:
                        self.configure(bg_color=args[0]["bg"])
                    elif "background" in args[0]:
                        self.configure(bg_color=args[0]["background"])
                master_old_configure(*args, **kwargs)

            self.master.config = new_configure
            self.master.configure = new_configure

    def destroy(self) -> None:
        """ Destroy this and all descendants widgets. """

        # call destroy methods of super classes
        tkinter.Frame.destroy(self)
        CTkAppearanceModeBaseClass.destroy(self)
        CTkScalingBaseClass.destroy(self)

    @abstractmethod
    def _draw(self, force_colors_update: bool = False) -> None:
        """ Called when some attributes have changed and the widget has to be redrawn """

    def config(self, *args: Any, **kwargs: Any) -> None:
        raise AttributeError("'config' is not implemented for CTk widgets. For consistency, always use 'configure' instead.")

    def configure(self, require_redraw: bool = False, **kwargs: Any) -> None:
        if "width" in kwargs or "height" in kwargs:
            self._set_dimensions(width=kwargs.pop("width", None),
                                 height=kwargs.pop("height", None))

        if "bg_color" in kwargs:
            new_bg_color = self._check_color_type(kwargs.pop("bg_color"), transparency=True)
            if new_bg_color == "transparent":
                self._bg_color = self._detect_color_of_master()
            else:
                self._bg_color = new_bg_color
            require_redraw = True

        super().configure(**pop_from_dict_by_iterable(kwargs, ValidTkFrameArgs.__annotations__))

        # if there are still items in the kwargs dict, raise ValueError
        check_kwargs_empty(kwargs, raise_error=True)

        if require_redraw:
            self._draw(force_colors_update=True)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "bg_color":
            return self._bg_color
        elif attribute_name == "width":
            return self._desired_width
        elif attribute_name == "height":
            return self._desired_height
        elif attribute_name in ValidTkFrameArgs.__annotations__:
            return super().cget(attribute_name)
        else:
            raise ValueError(f"'{attribute_name}' is not a supported argument.\nLook at the documentation for supported arguments.")

    def _update_dimensions_event(self, event: tkinter.Event) -> None:
        """ Called when the window has been reshaped, and so contained widgets changed dimensions """
        # only redraw if dimensions changed (for performance)
        if self._current_width != event.width or self._current_height != event.height:
            self._current_width = event.width
            self._current_height = event.height
            self._draw()  # faster drawing without color changes

    def _detect_color_of_master(self) -> ColorType:
        """ Detects foreground color of master widget for bg_color and transparent color """

        if isinstance(self.master, CTkContainer):
            return self.master.get_fg_color()

        elif isinstance(self.master, (ttk.Frame, ttk.LabelFrame, ttk.Notebook, ttk.Label)):  # master is ttk widget
            try:
                ttk_style = ttk.Style()
                return ttk_style.lookup(self.master.winfo_class(), "background")
            except Exception:
                pass

        else:  # master is normal tkinter widget
            try:
                return self.master.cget("bg")  # try to get bg color by .cget() method
            except Exception:
                pass
        return "#FFFFFF", "#000000"

    def _set_appearance_mode(self) -> None:
        self._draw(force_colors_update=True)
        super().update_idletasks()

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)

        super().configure(width=self._apply_scaling(self._desired_width),
                          height=self._apply_scaling(self._desired_height))

        if self._last_geometry_manager_call is not None:
            if self._last_geometry_manager_call["apply_scaling"]:
                kwargs = self._apply_argument_scaling(self._last_geometry_manager_call["kwargs"])
            else:
                kwargs = self._last_geometry_manager_call["kwargs"]
            self._last_geometry_manager_call["function"](**kwargs)

    def _set_dimensions(self, width: int | float | None = None, height: int | float | None = None) -> None:
        """ Called when desired dimensions change """
        if width is not None:
            self._desired_width = width
        if height is not None:
            self._desired_height = height

        super().configure(width=self._apply_scaling(self._desired_width),
                          height=self._apply_scaling(self._desired_height))

    def _create_bindings(self, sequence: str | None = None) -> None:
        """ Called after an "unbind" operation to restore internal binded methods """

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> None:
        #"sequence" semantics is reported here: https://tkdocs.com/shipman/event-sequences.html
        if not self._bind_targets:
            raise NotImplementedError
        if not (add == "+" or add is True):
            raise ValueError("'add' argument can only be '+' or True to preserve internal callbacks")
        for obj in self._bind_targets:
            obj.bind(sequence, func, add=True)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        if not self._bind_targets:
            raise NotImplementedError
        if funcid is not None:
            raise ValueError("'funcid' argument can only be None, because there is a bug in" +
                             " tkinter and its not clear whether the internal callbacks will be unbinded or not")
        for obj in self._bind_targets:
            obj.unbind(sequence, None)
        self._create_bindings(sequence=sequence)  # restore internal callbacks for sequence

    def bind_all(self,
                 sequence: str | None = None,
                 func: Callable[[tkinter.Event], None] | None = None,
                 add: str | bool = True) -> None:
        raise AttributeError("'bind_all' is not allowed, could result in undefined behavior")

    def unbind_all(self, sequence: str) -> None:
        raise AttributeError("'unbind_all' is not allowed, because it would delete necessary internal callbacks for all widgets")

    def focus(self) -> None:
        if self._focus_target is None:
            raise NotImplementedError
        return self._focus_target.focus()

    def focus_set(self) -> None:
        if self._focus_target is None:
            raise NotImplementedError
        return self._focus_target.focus_set()

    def focus_force(self) -> None:
        if self._focus_target is None:
            raise NotImplementedError
        return self._focus_target.focus_force()

    class _PlaceArgs(TypedDict, total=False):
        x: float | int | str
        y: float | int | str
        relx: float | str
        rely: float | str
        relwidth: float | str
        relheight: float | str
        in_: tkinter.Misc
        anchor: AnchorType
        bordermode: Literal["inside", "outside", "ignore"]

    def place(self, apply_scaling: bool = True, **kwargs: Unpack[_PlaceArgs]) -> None:
        """ Map this widget using the 'place' geometry manager. 
        Additional information is reported here: https://www.tcl-lang.org/man/tcl8.6/TkCmd/place.htm """

        if "width" in kwargs or "height" in kwargs:
            raise ValueError("'width' and 'height' arguments must be passed to the constructor of the widget, not the place method")
        self._last_geometry_manager_call = {"function": super().place, "apply_scaling": apply_scaling, "kwargs": kwargs}
        if apply_scaling:
            kwargs = self._apply_argument_scaling(kwargs)
        return super().place(**kwargs)

    def place_forget(self) -> None:
        """ Unmap this widget. """
        self._last_geometry_manager_call = None
        return super().place_forget()

    class _PackArgs(TypedDict, total=False):
        side: Literal["top", "bottom", "left", "right"]
        fill: Literal["none", "x", "y", "both"]
        expand: bool
        after: tkinter.Misc
        before: tkinter.Misc
        in_: tkinter.Misc
        anchor: AnchorType
        ipadx: float | int | str
        ipady: float | int | str
        padx: float | int | str | tuple[float | int | str, float | int | str]
        pady: float | int | str | tuple[float | int | str, float | int | str]

    def pack(self, apply_scaling: bool = True, **kwargs: Unpack[_PackArgs]) -> None:
        """ Map this widget using the 'pack' geometry manager. 
        Additional information is reported here: https://www.tcl-lang.org/man/tcl8.6/TkCmd/pack.htm """

        self._last_geometry_manager_call = {"function": super().pack, "apply_scaling": apply_scaling, "kwargs": kwargs}
        if apply_scaling:
            kwargs = self._apply_argument_scaling(kwargs)
        return super().pack(**kwargs)

    def pack_forget(self) -> None:
        """ Unmap this widget. """
        self._last_geometry_manager_call = None
        return super().pack_forget()

    class _GridArgs(TypedDict, total=False):
        column: int
        row: int
        columnspan: int
        rowspan: int
        in_: tkinter.Misc
        sticky: str
        ipadx: float | int | str
        ipady: float | int | str
        padx: float | int | str | tuple[float | int | str, float | int | str]
        pady: float | int | str | tuple[float | int | str, float | int | str]

    def grid(self, apply_scaling: bool = True, **kwargs: Unpack[_GridArgs]) -> None:
        """ Map this widget using the 'grid' geometry manager. 
        Additional information is reported here: https://www.tcl-lang.org/man/tcl8.6/TkCmd/grid.htm """

        self._last_geometry_manager_call = {"function": super().grid, "apply_scaling": apply_scaling, "kwargs": kwargs}
        if apply_scaling:
            kwargs = self._apply_argument_scaling(kwargs)
        return super().grid(**kwargs)

    def grid_forget(self) -> None:
        """ Unmap this widget. """
        self._last_geometry_manager_call = None
        return super().grid_forget()
