from __future__ import annotations

import tkinter
import math
import itertools
from dataclasses import dataclass, field
from typing import Callable, ClassVar, TYPE_CHECKING
from typing_extensions import Literal, TypeAlias, TypedDict

if TYPE_CHECKING:
    from ..core_rendering import CTkCanvas


DRAWING_METHODS: list[str] = ["polygons", "font", "circles"]

DrawingMethodType: TypeAlias = Literal["polygons", "font", "circles"]
SectionType: TypeAlias = Literal["top", "bottom", "left", "right", "top_left", "top_right", "bottom_right", "bottom_left"]

class RoundedRectInfo(TypedDict, total=False):
    x_start: int
    y_start: int
    x_end: int
    y_end: int
    width: int
    height: int
    corner_radius: int
    left_section_width: int
    right_section_width: int
    top_section_height: int
    bottom_section_height: int

class BorderedRoundedRectInfo(RoundedRectInfo, total=False):
    inner_width: int
    inner_height: int
    inner_corner_radius: int
    border_width: int
    flat_spacing: int
    inscribed_spacing: float | int
    spacings_changed: bool


def rototraslation(points: tuple[tuple[float | int, float | int], ...],
                   angle: float | int = 0,
                   x_pos: float | int = 0,
                   y_pos: float | int = 0) -> tuple[tuple[float | int, float | int], ...]:
    """ Performs a Rotation+Translation of all provided points.\n
    The Rotation is performed always around the origin (0, 0) using an angles expressed in 360 degrees.\n
    Provided coordinates are then added to perform the Translation. """

    cos = math.cos(angle*math.pi/180)
    sin = math.sin(angle*math.pi/180)
    return tuple((x*cos - y*sin + x_pos, x*sin + y*cos + y_pos) for x, y in points)


@dataclass(frozen=True)
class BaseShape:
    """ Provides common attributes and methods to all Shapes. """

    preferred_drawing_method: ClassVar[DrawingMethodType] = "circles"

    canvas: CTkCanvas
    drawing_method: DrawingMethodType = None

    _name: str = field(default="", init=False)

    def __post_init__(self) -> None:
        if self.drawing_method is None:
            super().__setattr__("drawing_method", self.preferred_drawing_method)
        super().__setattr__("_name", f"shape{self.canvas.shapes_counter}")
        self.canvas.shapes_counter += 1

    def raise_(self) -> None:
        self.canvas.tag_raise(self._name)

    def delete(self) -> None:
        self.canvas.delete(self._name)

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True) -> str:
        #When the font method is used, if the event happens outside but near the rounded
        # parts, it triggers anyway because the drawn character always has a square area,
        # even if part of it is empty
        return self.canvas.tag_bind(self._name, sequence, func, add)

    def unbind(self, sequence: str, funcid: None = None) -> None:
        self.canvas.tag_unbind(self._name, sequence, funcid)


@dataclass(frozen=True)
class RoundedRect(BaseShape):
    """ Draws a rounded rectangle at (x_start, y_start).\n
    It can be divided into left/right-top/bottom sections that can be managed separately. """

    info: RoundedRectInfo = field(default_factory=RoundedRectInfo, init=False, compare=False)

    _tags: dict[str, str] = field(default_factory=dict, init=False, compare=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        #section = None => _name
        self._tags[None] = self._name

        sections = ("top", "bottom", "left", "right")
        for sec in sections:
            #top, bottom, left, right
            self._tags[sec] = f"{self._name}_{sec}"

        for vsec in sections[0:2]:
            for hsec in sections[2:4]:
                #top_left, top_right, bottom_left, bottom_right
                key = f"{vsec}_{hsec}"
                self._tags[key] = f"{self._name}_{key}"

                for shape in ("oval", "rect"):
                    for n in (1, 2):
                        #(oval|rect)_(t|b)(l|r)_(1|2)
                        key = f"{shape}_{vsec[0]}{hsec[0]}_{n}"
                        self._tags[key] = f"{self._name}_{key}"

    def update(self,
               x_start: float | int,
               y_start: float | int,
               width: float | int,
               height: float | int,
               corner_radius: float | int,
               left_section_width: float | int | None = None,
               top_section_height: float | int | None = None) -> bool:
        """Returns True if recoloring is necessary."""

        split_mode = left_section_width is not None or top_section_height is not None

        #correct provided values
        x_start = round(x_start)
        y_start = round(y_start)
        width = int(width)
        height = int(height)
        corner_radius = int(min(corner_radius,
                                width / (2 if left_section_width is None else 3),
                                height / (2 if top_section_height is None else 3)))
        left_section_width = width if left_section_width is None else round(left_section_width)
        top_section_height = height if top_section_height is None else round(top_section_height)
        left_section_width = max(corner_radius, min(left_section_width, width - corner_radius))
        top_section_height = max(corner_radius, min(top_section_height, height - corner_radius))

        #calculate internal values
        x_end = x_start + width
        y_end = y_start + height
        x_center_l = x_start + corner_radius
        x_center_r = x_end - corner_radius
        y_center_t = y_start + corner_radius
        y_center_b = y_end - corner_radius
        x_mid = x_start + left_section_width
        y_mid = y_start + top_section_height

        #update info
        self.info["y_start"] = y_start
        self.info["x_start"] = x_start
        self.info["x_end"] = x_end
        self.info["y_end"] = y_end
        self.info["width"] = width
        self.info["height"] = height
        self.info["corner_radius"] = corner_radius
        self.info["left_section_width"] = left_section_width
        self.info["right_section_width"] = width - left_section_width
        self.info["top_section_height"] = top_section_height
        self.info["bottom_section_height"] = height - top_section_height

        if corner_radius > 0:
            if self.drawing_method == "polygons":
                requires_recoloring_1 = self._polygons_method(x_center_l, x_center_r, y_center_t, y_center_b, corner_radius, split_mode)
            elif self.drawing_method == "font":
                requires_recoloring_1 = self._font_method(x_center_l, x_center_r, y_center_t, y_center_b, corner_radius)
            else:
                requires_recoloring_1 = self._circles_method(x_start, y_start, x_end, y_end, corner_radius)
        else:
            requires_recoloring_1 = False
            for vsec, hsec, n in itertools.product(("t", "b"), ("l", "r"), (1, 2)):
                self.canvas.delete(self._tags[f"oval_{vsec}{hsec}_{n}"])

        #_polygons_method draws the entire shape if split mode is not used
        if corner_radius > 0 and self.drawing_method == "polygons" and not split_mode:
            requires_recoloring_2 = False
        else:
            requires_recoloring_2 = self._common_rectangles(x_start, x_mid, x_end, x_center_l, x_center_r,
                                                            y_start, y_mid, y_end, y_center_t, y_center_b)

        if requires_recoloring_1 or requires_recoloring_2:
            for vsec, hsec, n in itertools.product(("t", "b"), ("l", "r"), (1, 2)):
                self.canvas.tag_raise(self._tags[f"rect_{vsec}{hsec}_{n}"])

        return requires_recoloring_1 or requires_recoloring_2

    def set_color(self, color: str, section: SectionType | None = None) -> None:
        self.canvas.itemconfig(self._tags[section], outline=color, fill=color)

    def delete(self) -> None:
        self.info.clear()
        return super().delete()

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True,
             section: SectionType | None = None) -> None:
        self.canvas.tag_bind(self._tags[section], sequence, func, add)

    def unbind(self, sequence: str, funcid: None = None, section: SectionType | None = None) -> None:
        self.canvas.tag_unbind(self._tags[section], sequence, funcid)

    def _polygons_method(self,
                         x_center_l: int,
                         x_center_r: int,
                         y_center_t: int,
                         y_center_b: int,
                         corner_radius: int,
                         split_mode: bool) -> bool:
        requires_recoloring = False
        t = self._tags

        if not self.canvas.find_withtag(t["oval_tl_1"]):
            self.canvas.create_polygon((0, 0, 0, 0), tags=(t["oval_tl_1"], t["top_left"], t["top"], t["left"], self._name), joinstyle=tkinter.ROUND)
            requires_recoloring = True

        if split_mode:
            if not self.canvas.find_withtag(t["oval_tr_1"]):
                self.canvas.create_polygon((0, 0, 0, 0), tags=(t["oval_tr_1"], t["top_right"], t["top"], t["right"], self._name), joinstyle=tkinter.ROUND)
                self.canvas.create_polygon((0, 0, 0, 0), tags=(t["oval_br_1"], t["bottom_right"], t["bottom"], t["right"], self._name), joinstyle=tkinter.ROUND)
                self.canvas.create_polygon((0, 0, 0, 0), tags=(t["oval_bl_1"], t["bottom_left"], t["bottom"], t["left"], self._name), joinstyle=tkinter.ROUND)
                requires_recoloring = True
        else:
            self.canvas.delete(t["oval_tr_1"], t["oval_br_1"], t["oval_bl_1"],
                               t["oval_tr_2"], t["oval_br_2"], t["oval_bl_2"])

        if not split_mode:
            self.canvas.coords(t["oval_tl_1"], x_center_l, y_center_t,
                                               x_center_r, y_center_t,
                                               x_center_r, y_center_b,
                                               x_center_l, y_center_b)
            self.canvas.itemconfig(t["oval_tl_1"], width=corner_radius * 2)
        else:
            self.canvas.coords(t["oval_tl_1"], x_center_l, y_center_t, x_center_l + 1, y_center_t + 1)
            self.canvas.coords(t["oval_tr_1"], x_center_r, y_center_t, x_center_r - 1, y_center_t + 1)
            self.canvas.coords(t["oval_br_1"], x_center_r, y_center_b, x_center_r - 1, y_center_b - 1)
            self.canvas.coords(t["oval_bl_1"], x_center_l, y_center_b, x_center_l + 1, y_center_b - 1)

            self.canvas.itemconfig(t["oval_tl_1"], width=corner_radius * 2)
            self.canvas.itemconfig(t["oval_tr_1"], width=corner_radius * 2)
            self.canvas.itemconfig(t["oval_br_1"], width=corner_radius * 2)
            self.canvas.itemconfig(t["oval_bl_1"], width=corner_radius * 2)

        return requires_recoloring

    def _font_method(self,
                     x_center_l: int,
                     x_center_r: int,
                     y_center_t: int,
                     y_center_b: int,
                     corner_radius: int) -> bool:
        requires_recoloring = False
        t = self._tags

        circles_info = [
            ("top"   , "left" , (x_center_l, y_center_t, corner_radius)),
            ("top"   , "right", (x_center_r, y_center_t, corner_radius)),
            ("bottom", "right", (x_center_r, y_center_b, corner_radius)),
            ("bottom", "left" , (x_center_l, y_center_b, corner_radius))
        ]

        for idx, (vsec, hsec, coordinates) in enumerate(circles_info):
            tags1 = (t[f"oval_{vsec[0]}{hsec[0]}_1"], t[f"{vsec}_{hsec}"], t[vsec], t[hsec], self._name)
            tags2 = (t[f"oval_{vsec[0]}{hsec[0]}_2"], t[f"{vsec}_{hsec}"], t[vsec], t[hsec], self._name)

            #look if the same exact circle has already been drawn in a previous one
            already_drawn = False
            for _, _, prev_coordinates in circles_info[:idx]:
                if prev_coordinates == coordinates:
                    already_drawn = True
                    break

            if not already_drawn:
                if not self.canvas.find_withtag(tags1[0]):
                    self.canvas.create_aa_circle(0, 0, 0, tags=tags1, anchor=tkinter.CENTER)
                    self.canvas.create_aa_circle(0, 0, 0, tags=tags2, anchor=tkinter.CENTER, angle=180)
                    requires_recoloring = True
                self.canvas.coords(tags1[0], *coordinates)
                self.canvas.coords(tags2[0], *coordinates)
            else:
                self.canvas.delete(tags1[0], tags2[0])

        return requires_recoloring

    def _circles_method(self,
                        x_start: int,
                        y_start: int,
                        x_end: int,
                        y_end: int,
                        corner_radius: int) -> bool:
        requires_recoloring = False
        t = self._tags

        diam = 2 * corner_radius
        circles_info = [
            ("top"   , "left" , (x_start     , y_start     , x_start + diam - 1, y_start + diam - 1)),
            ("top"   , "right", (x_end - diam, y_start     , x_end          - 1, y_start + diam - 1)),
            ("bottom", "right", (x_end - diam, y_end - diam, x_end          - 1, y_end          - 1)),
            ("bottom", "left" , (x_start     , y_end - diam, x_start + diam - 1, y_end          - 1))
        ]

        for idx, (vsec, hsec, coordinates) in enumerate(circles_info):
            tags = (t[f"oval_{vsec[0]}{hsec[0]}_1"], t[f"{vsec}_{hsec}"], t[vsec], t[hsec], self._name)

            #look if the same exact circle has already been drawn in a previous one
            already_drawn = False
            for _, _, prev_coordinates in circles_info[:idx]:
                if prev_coordinates == coordinates:
                    already_drawn = True
                    break

            if not already_drawn:
                if not self.canvas.find_withtag(tags[0]):
                    self.canvas.create_oval(0, 0, 0, 0, width=0, tags=tags)
                    requires_recoloring = True
                self.canvas.coords(tags[0], *coordinates)
            else:
                self.canvas.delete(tags[0])

        return requires_recoloring

    def _common_rectangles(self, x_start: int, x_mid: int, x_end: int, x_center_l: int, x_center_r: int,
                                 y_start: int, y_mid: int, y_end: int, y_center_t: int, y_center_b: int) -> bool:
        requires_recoloring = False
        t = self._tags

        rects_info = [
            ("top"   , "left" , 1, (x_center_l, y_start   , x_mid     , y_mid     )),
            ("top"   , "left" , 2, (x_start   , y_center_t, x_mid     , y_mid     )),
            ("top"   , "right", 1, (x_mid     , y_start   , x_center_r, y_mid     )),
            ("top"   , "right", 2, (x_mid     , y_center_t, x_end     , y_mid     )),
            ("bottom", "right", 1, (x_mid     , y_mid     , x_center_r, y_end     )),
            ("bottom", "right", 2, (x_mid     , y_mid     , x_end     , y_center_b)),
            ("bottom", "left" , 1, (x_center_l, y_mid     , x_mid     , y_end     )),
            ("bottom", "left" , 2, (x_start   , y_mid     , x_mid     , y_center_b))
        ]

        for vsec, hsec, n, coordinates in rects_info:
            tags = (t[f"rect_{vsec[0]}{hsec[0]}_{n}"], t[f"{vsec}_{hsec}"], t[vsec], t[hsec], self._name)

            #if rect is at least 1-pixel high/wide
            if coordinates[2] > coordinates[0] and coordinates[3] > coordinates[1]:
                if not self.canvas.find_withtag(tags[0]):
                    self.canvas.create_rectangle((0, 0, 0, 0), width=0, tags=tags)
                    requires_recoloring = True
                self.canvas.coords(tags[0], *coordinates)
            else:
                self.canvas.delete(tags[0])

        return requires_recoloring


@dataclass(frozen=True)
class BorderedRoundedRect(BaseShape):
    """ Draws a rounded rectangle with an optional border.\n
    It can be divided into left/right-top/bottom sections that can be managed separately. """

    spacings_tolerance: ClassVar[int] = 1

    info: BorderedRoundedRectInfo = field(default_factory=BorderedRoundedRectInfo, init=False, compare=False)

    _border: RoundedRect = field(default=None, init=False, compare=False)
    _main: RoundedRect = field(default=None, init=False, compare=False)

    def __post_init__(self) -> None:
        super().__post_init__()

        for attribute in ("_border", "_main"):
            super().__setattr__(attribute, RoundedRect(self.canvas, self.drawing_method))

    def update(self,
               width: float | int,
               height: float | int,
               corner_radius: float | int,
               border_width: float | int,
               left_section_width: float | int | None = None,
               top_section_height: float | int | None = None) -> bool:
        """Returns True if recoloring is necessary."""

        border_width = round(border_width)
        inner_width = max(0, width - 2 * border_width)
        inner_height = max(0, height - 2 * border_width)

        if border_width > 0:
            requires_recoloring_1 = self._border.update(0, 0,
                                                        width, height,
                                                        corner_radius,
                                                        left_section_width, top_section_height)
        else:
            requires_recoloring_1 = False
            self._border.delete()

        #if there is actually space to display something in the middle
        if inner_width > 0 and inner_height > 0:
            inner_corner_radius = max(0, self._border.info.get("corner_radius", corner_radius) - border_width)
            if left_section_width is not None:
                left_section_width -= border_width
            if top_section_height is not None:
                top_section_height -= border_width

            requires_recoloring_2 = self._main.update(border_width, border_width,
                                                      inner_width, inner_height,
                                                      inner_corner_radius,
                                                      left_section_width, top_section_height)
        else:
            requires_recoloring_2 = False
            self._main.delete()

        if requires_recoloring_1 or requires_recoloring_2:
            self._border.raise_()
            self._main.raise_()

        self.info.update(self._border.info if border_width > 0 else self._main.info)
        self.info["inner_corner_radius"] = self._main.info.get("corner_radius", 0)
        self.info["inner_width"] = self._main.info.get("width", 0)
        self.info["inner_height"] = self._main.info.get("height", 0)
        self.info["border_width"] = border_width

        #to avoid too frequent updates, we consider a change in the spacings only when
        # the difference with the previous value is big enough (spacings_tolerance).
        self.info["spacings_changed"] = False

        #flat_spacing: distance between the edge of the canvas and a rectangle entirely
        # drawn inside the shape, with 2 sides coinciding with the drawn border.
        # |<---------->|
        # |         @@@@@@@@@@@@
        # |      @@@@@@@@@@@@@@@
        # |    @@@@@@@@.--------
        # |  @@@@@@@@  |
        # |@@@@@@@@    |
        # |@@@@@@      |
        # |@@@@@@      |
        spacing = border_width + self.info["inner_corner_radius"]
        if abs(spacing - self.info.get("flat_spacing", -1000)) > self.spacings_tolerance:
            self.info["flat_spacing"] = spacing
            self.info["spacings_changed"] = True

        #inscribed_spacing: distance between the edge of the canvas and an inscribed rectangle entirely
        # drawn inside the shape (its angles are placed in the middle of the rounded segment, if any).
        # |<-------->|                   |<------->|
        # |         @@@@@@@@@@@@         |         @@@@@@@@@@@@
        # |      @@@@@@@@@@@@@@@         |      @@@@@@@@@@@@@@@
        # |    @@@@@@@@                  |    @@@@@@@@@@@@@@@@@
        # |  @@@@@@@@.----------   OR    |  @@@@@@@.-----------
        # |@@@@@@@@  |                   |@@@@@@@@@|
        # |@@@@@@    |                   |@@@@@@@@@|
        # |@@@@@@    |                   |@@@@@@@@@|
        spacing = max(
            self.info.get("corner_radius", 0) - self.info["inner_corner_radius"] * 0.7071, #cos(45°)
            border_width
        )
        if abs(spacing - self.info.get("inscribed_spacing", -1000)) > self.spacings_tolerance:
            self.info["inscribed_spacing"] = spacing
            self.info["spacings_changed"] = True

        return requires_recoloring_1 or requires_recoloring_2

    def set_border_color(self, color: str, section: SectionType | None = None) -> None:
        self._border.set_color(color, section)

    def set_main_color(self, color: str, section: SectionType | None = None) -> None:
        self._main.set_color(color, section)

    def raise_(self) -> None:
        self._border.raise_()
        self._main.raise_()

    def delete(self) -> None:
        self.info.clear()
        self._border.delete()
        self._main.delete()

    def bind(self,
             sequence: str | None = None,
             func: Callable[[tkinter.Event], None] | None = None,
             add: str | bool = True,
             section: SectionType | None = None) -> None:
        self._border.bind(sequence, func, add, section)
        self._main.bind(sequence, func, add, section)

    def unbind(self, sequence: str, funcid: None = None, section: SectionType | None = None) -> None:
        self._border.unbind(sequence, funcid, section)
        self._main.unbind(sequence, funcid, section)


@dataclass(frozen=True)
class Arrow(BaseShape):
    """ Draws an arrow at (x_position, y_position) with given size and rotation.\n
    - angle ==  0 degrees => arrow points up.\n
    - angle == 90 degrees => arrow points right. """

    def update(self,
               x_position: float | int,
               y_position: float | int,
               size: float | int,
               angle: float | int) -> bool:
        """Returns True if recoloring is necessary."""

        x_position = round(x_position)
        y_position = round(y_position)
        size = round(size)
        requires_recoloring = False

        if self.drawing_method == "font":
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_text(0, 0, text="Y",
                                        font=("CustomTkinter_shapes_font", -size),
                                        angle=180-angle,
                                        tags=self._name,
                                        anchor=tkinter.CENTER)
                requires_recoloring = True

            self.canvas.coords(self._name, x_position, y_position)
            self.canvas.itemconfigure(self._name, font=("CustomTkinter_shapes_font", -size))

        else:
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_line(0, 0, 0, 0,
                                        tags=self._name,
                                        width=round(size / 4),
                                        joinstyle=tkinter.ROUND,
                                        capstyle=tkinter.ROUND)
                requires_recoloring = True

            #points for arrow centered in (0, 0) pointing up
            points = ((- size / 2, + size / 5),
                      (    0     , - size / 5),
                      (+ size / 2, + size / 5))
            points = rototraslation(points, angle, x_position, y_position)

            #older Python versions require the coordinates to be passed individually...
            self.canvas.coords(self._name, *points[0], *points[1], *points[2])
            self.canvas.itemconfigure(self._name, width=round(size / 4))

        return requires_recoloring

    def set_color(self, color: str) -> None:
        self.canvas.itemconfig(self._name, fill=color)


@dataclass(frozen=True)
class Bar(BaseShape):
    """ Draws a rounded bar at (x_position, y_position) with given size and rotation.\n
    - angle ==  0 degrees => |.\n
    - angle == 90 degrees => -. """

    def update(self,
               x_position: float | int,
               y_position: float | int,
               size: float | int,
               angle: float | int) -> bool:
        """Returns True if recoloring is necessary."""

        x_position = round(x_position)
        y_position = round(y_position)
        size = round(size)
        requires_recoloring = False

        if self.drawing_method == "font":
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_text(0, 0, text="X",
                                        font=("CustomTkinter_shapes_font", -size),
                                        angle=90-angle,
                                        tags=self._name,
                                        anchor=tkinter.CENTER)
                requires_recoloring = True

            self.canvas.coords(self._name, x_position, y_position)
            self.canvas.itemconfigure(self._name, font=("CustomTkinter_shapes_font", -size))

        else:
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_line(0, 0, 0, 0,
                                        tags=self._name,
                                        width=round(size / 6),
                                        joinstyle=tkinter.ROUND,
                                        capstyle=tkinter.ROUND)
                requires_recoloring = True

            #points for vertical line centered in (0, 0)
            points = ((0, + size / 2),
                      (0, - size / 2))
            points = rototraslation(points, angle, x_position, y_position)

            #older Python versions require the coordinates to be passed individually...
            self.canvas.coords(self._name, *points[0], *points[1])
            self.canvas.itemconfigure(self._name, width=round(size / 6))

        return requires_recoloring

    def set_color(self, color: str) -> None:
        self.canvas.itemconfig(self._name, fill=color)


@dataclass(frozen=True)
class Checkmark(BaseShape):
    """ Draws a checkmark at (x_position, y_position) with given size. """

    def update(self,
               x_position: float | int,
               y_position: float | int,
               size: float | int) -> bool:
        """Returns True if recoloring is necessary."""

        x_position = round(x_position)
        y_position = round(y_position)
        size = round(size)
        requires_recoloring = False

        if self.drawing_method == "font":
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_text(0, 0, text="Z",
                                        font=("CustomTkinter_shapes_font", -size),
                                        tags=self._name,
                                        anchor=tkinter.CENTER)
                requires_recoloring = True

            self.canvas.coords(self._name, x_position, y_position)
            self.canvas.itemconfigure(self._name, font=("CustomTkinter_shapes_font", -size))

        else:
            if not self.canvas.find_withtag(self._name):
                self.canvas.create_line(0, 0, 0, 0,
                                        tags=self._name,
                                        width=round(size / 5),
                                        joinstyle=tkinter.MITER,
                                        capstyle=tkinter.ROUND)
                requires_recoloring = True

            radius = size / 2.8
            self.canvas.coords(self._name, x_position + radius    , y_position - radius,
                                           x_position - radius / 4, y_position + radius * 0.8,
                                           x_position - radius    , y_position + radius / 6)
            self.canvas.itemconfigure(self._name, width=round(size / 5))

        return requires_recoloring

    def set_color(self, color: str) -> None:
        self.canvas.itemconfig(self._name, fill=color)
