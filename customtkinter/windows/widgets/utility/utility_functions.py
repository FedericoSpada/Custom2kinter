from __future__ import annotations

import ctypes
import ctypes.util
import tkinter
import sys
import re
from typing import Iterable, TypeVar, TYPE_CHECKING
from typing_extensions import Literal

if TYPE_CHECKING:
    from ..theme import AnchorType

KT = TypeVar("KT")
VT = TypeVar("VT")

def pop_from_dict_by_iterable(dictionary: dict[KT, VT], valid_keys: Iterable[KT]) -> dict[KT, VT]:
    """ removes and creates new dict with key value pairs of dictionary, where key is in valid_keys """
    new_dictionary: dict[KT, VT] = {}

    for key in list(dictionary.keys()):
        if key in valid_keys:
            new_dictionary[key] = dictionary.pop(key)

    return new_dictionary


def check_kwargs_empty(kwargs: dict, raise_error: bool = False) -> bool:
    """ returns True if kwargs are empty, False otherwise, raises error if not empty """

    if len(kwargs) > 0:
        if raise_error:
            arguments = "', '".join(kwargs.keys())
            phrase = "is not a supported argument" if len(kwargs) == 1 else "are not supported arguments"
            raise ValueError(f"'{arguments}' {phrase}.\nLook at the documentation for supported arguments.")
        else:
            return True
    else:
        return False


def deep_update(base: dict[KT, VT], new: dict[KT, VT]) -> None:
    """ performs the 'update' operation of the old dict with the new one, recursively for any sub-dict contained as value """

    for key, value in new.items():
        if isinstance(value, dict):
            deep_update(base.setdefault(key, {}), value)
        else:
            base[key] = value


def parse_geometry_string(geometry_string: str) -> tuple[int | None, ...]:
    #                 index:   1                   2           3          4             5       6
    # regex group structure: ('<width>x<height>', '<width>', '<height>', '+-<x>+-<y>', '-<x>', '-<y>')
    result = re.search(r"((\d+)x(\d+)){0,1}(\+{0,1}([+-]{0,1}\d+)\+{0,1}([+-]{0,1}\d+)){0,1}", geometry_string)

    width = int(result.group(2)) if result.group(2) is not None else None
    height = int(result.group(3)) if result.group(3) is not None else None
    x = int(result.group(5)) if result.group(5) is not None else None
    y = int(result.group(6)) if result.group(6) is not None else None

    return width, height, x, y


def get_window_root_of_widget(widget: tkinter.Misc) -> tkinter.Tk | tkinter.Toplevel:
    current_widget = widget
    while not isinstance(current_widget, (tkinter.Tk, tkinter.Toplevel)):
        current_widget = current_widget.master
    return current_widget


def get_proper_cursor(mode: Literal["normal", "clickable"]) -> str | None:
    retval = None
    if mode == "normal":
        if sys.platform == "darwin" or sys.platform.startswith("win"):
            retval="arrow"
    elif mode == "clickable":
        if sys.platform == "darwin":
            retval="pointinghand"
        elif sys.platform.startswith("win"):
            retval="hand2"
    return retval


def get_width_height_from_orientation(orientation: Literal["horizontal", "vertical"],
                                      thickness: int,
                                      length: int) -> tuple[int, int]:
    if orientation == "vertical":
        width = thickness
        height = length
    else:
        width = length
        height = thickness
    return width, height


def get_monitor_info(x: int, y: int) -> tuple[int, int, int, int]:
    """Return (left, top, right, bottom) of the physical monitor containing (x, y).

    Raises NotImplementedError on Linux.
    """
    if sys.platform.startswith("win"):
        from ctypes import windll, wintypes, Structure, byref

        class _RECT(Structure):
            _fields_ = [("left", wintypes.LONG), ("top", wintypes.LONG),
                        ("right", wintypes.LONG), ("bottom", wintypes.LONG)]

        class _MONITORINFO(Structure):
            _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", _RECT),
                        ("rcWork", _RECT), ("dwFlags", wintypes.DWORD)]

        pt = wintypes.POINT()
        pt.x, pt.y = x, y
        monitor = windll.user32.MonitorFromPoint(pt, 2)  # MONITOR_DEFAULTTONEAREST
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        windll.user32.GetMonitorInfoW(monitor, byref(info))
        r = info.rcMonitor
        return r.left, r.top, r.right, r.bottom

    elif sys.platform == "darwin":
        CG = ctypes.cdll.LoadLibrary(
            ctypes.util.find_library("CoreGraphics")
            or "/System/Library/Frameworks/CoreGraphics.framework/CoreGraphics"
        )
        CGPoint = ctypes.c_double * 2
        point = CGPoint(float(x), float(y))
        display_ids = (ctypes.c_uint32 * 8)()
        count = ctypes.c_uint32(0)
        CG.CGGetDisplaysWithPoint.restype = ctypes.c_int
        CG.CGGetDisplaysWithPoint(point, 8, display_ids, ctypes.byref(count))
        display = display_ids[0] if count.value > 0 else CG.CGMainDisplayID()
        CG.CGDisplayBounds.restype = ctypes.c_double * 4
        bounds = CG.CGDisplayBounds(display)
        lft, top, w, h = float(bounds[0]), float(bounds[1]), float(bounds[2]), float(bounds[3])
        return int(lft), int(top), int(lft + w), int(top + h)

    else:
        raise NotImplementedError(f"get_monitor_info is not supported on {sys.platform}")
