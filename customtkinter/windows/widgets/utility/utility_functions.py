from __future__ import annotations

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
