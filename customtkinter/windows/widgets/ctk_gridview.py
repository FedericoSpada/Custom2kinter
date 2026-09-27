from __future__ import annotations

import tkinter
from functools import partial
from typing import Any, Callable
from typing_extensions import Literal, Unpack

from .core_widget_classes import CTkContainer
from .core_widget_classes.ctk_widget import CTkWidgetArgs
from .theme import ColorType, ThemeManager
from .ctk_frame import CTkFrame, CTkFrameThemedArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, check_colors, get_proper_cursor


class CTkGridViewThemedArgs(CTkFrameThemedArgs, total=False, closed=True):
    thickness: int
    border_spacing: int
    hover_color: ColorType
    hover: bool

class CTkGridViewArgs(CTkGridViewThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    min_rows_size: float     # minimal rows dimension in [%] w.r.t. overall height
    min_columns_size: float  # minimal columns dimension in [%] w.r.t. overall width
    pre_command: Callable[[int | None, int | None], Literal["break"] | None] | None
    command: Callable[[int | None, int | None], None] | None


class CTkGridView(CTkFrame):
    """
    A collection of frames displayed in a Grid, with rows and columns that the user can resize.
    Right-clicking a separator will make the affected rows/columns the same size.
    For detailed information check out the documentation.
    """

    update_time: int = 40   # interval in [ms], to update rows/columns sizes
    hover_delay: int = 100  # time after which the hover effect is applied
    min_size_limit: float = 0.05
    base_weight: int = 1000

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkGridViewArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkGridViewThemedArgs.__annotations__)
        self._theme_gv_info: CTkGridViewThemedArgs = ThemeManager.get_info("CTkGridView", theme_key, **theme_args)

        #validity checks
        check_colors(self._theme_gv_info, CTkGridViewThemedArgs)

        super().__init__(master=master,
                         width=self._theme_gv_info["width"],
                         height=self._theme_gv_info["height"],
                         bg_color=self._theme_gv_info["bg_color"],
                         fg_color="transparent",
                         corner_radius=0)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._min_rows_size: float = kwargs.pop("min_rows_size", self.min_size_limit)
        self._min_columns_size: float = kwargs.pop("min_columns_size", self.min_size_limit)
        self._pre_command: Callable[[int | None, int| None], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[int | None, int| None], None] | None = kwargs.pop("command", None)

        self._inner_frames: dict[str, CTkFrame] = {}
        self._separators: dict[tuple[int | None, int | None], CTkFrame] = {}
        self._row_weights: list[int] = [self.base_weight]
        self._column_weights: list[int] = [self.base_weight]
        self._row_target: int | None = None
        self._column_target: int | None = None
        self._hover_after_id: str = ""
        self._loop_after_id: str = ""

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self.grid_propagate(False)
        for n, weight in enumerate(self._row_weights):
            self.grid_rowconfigure(n, weight=weight, uniform="r")
        for n, weight in enumerate(self._column_weights):
            self.grid_columnconfigure(n, weight=weight, uniform="c")

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)
        self._update_separators()

    def _on_enter(self, row: int | None = None, column: int| None = None, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL and self._theme_gv_info["hover"]:
            if self.hover_delay > 0:
                self._hover_after_id = self.after(self.hover_delay, self._hover_effects, row, column)
            else:
                self._hover_effects(row, column)

    def _hover_effects(self, row: int | None = None, column: int| None = None) -> None:
        for key, separator in self._separators.items():
            if (key[0] == row and row is not None) or (key[1] == column and column is not None):
                separator.configure(fg_color=self._theme_gv_info["hover_color"])

    def _on_leave(self, row: int | None = None, column: int| None = None, _: tkinter.Event | None = None) -> None:
        #if the dragging operation is ongoing, we avoid removing
        # the hover effect because it would be immediately reapplied
        if self._row_target is None and self._column_target is None:
            if self._hover_after_id:
                self.after_cancel(self._hover_after_id)
                self._hover_after_id = ""
            for key, separator in self._separators.items():
                if (key[0] == row and row is not None) or (key[1] == column and column is not None):
                    separator.configure(fg_color="transparent")

    def _clicked(self, row: int | None = None, column: int| None = None, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            retval = "" if self._pre_command is None else self._pre_command(row, column)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                self._row_target = row
                self._column_target = column
                self._update_loop()

    def _right_clicked(self, row: int | None = None, column: int| None = None, _: tkinter.Event | None = None) -> None:
        if self._state == tkinter.NORMAL:
            retval = "" if self._pre_command is None else self._pre_command(row, column)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                if row is not None:
                    self._avarage_weights(self._row_weights, row - 1)
                    for n, weight in enumerate(self._row_weights):
                        self.grid_rowconfigure(n, weight=weight, uniform="r")

                if column is not None:
                    self._avarage_weights(self._column_weights, column - 1)
                    for n, weight in enumerate(self._column_weights):
                        self.grid_columnconfigure(n, weight=weight, uniform="c")

                if self._command is not None:
                    self._command(row, column)

    def _on_release(self, _: tkinter.Event | None = None) -> None:
        #stop any ongoing operation
        if self._loop_after_id:
            self.after_cancel(self._loop_after_id)
            self._loop_after_id = ""
            self._row_target = None
            self._column_target = None

    def _update_loop(self) -> None:
        if self._row_target is not None:
            relpos = (self.winfo_pointery() - self.winfo_rooty()) / self.winfo_height()
            self._update_weights(self._row_weights, self._row_target - 1, relpos, self._min_rows_size)

            for n, weight in enumerate(self._row_weights):
                self.grid_rowconfigure(n, weight=weight, uniform="r")

        if self._column_target is not None:
            relpos = (self.winfo_pointerx() - self.winfo_rootx()) / self.winfo_width()
            self._update_weights(self._column_weights, self._column_target - 1, relpos, self._min_columns_size)

            for n, weight in enumerate(self._column_weights):
                self.grid_columnconfigure(n, weight=weight, uniform="c")

        if self._command is not None:
            self._command(self._row_target, self._column_target)
        self._loop_after_id = self.after(self.update_time, self._update_loop)

    def _update_weights(self, weights: list[int], target: int, relpos_requested: float, min_size: float) -> None:
        #clamp min_size to avoid crashing the application when the weights assume absurd values
        min_size = max(self.min_size_limit, min_size)

        sumweight = sum(weights)
        #relative position when the target row/column starts
        relpos_target = sum(weights[:target]) / sumweight
        #relative position when the next row/column ends
        relpos_next = 1.0 - sum(weights[target + 2:]) / sumweight

        #the new relative position of the clicked separator is clamped so that both the target and
        # the next rows/columns can't become smaller than min_size
        relpos_sep = max(relpos_target + min_size, min(relpos_requested, relpos_next - min_size))
        pos_sep = sumweight * relpos_sep

        #if the first row/column should change size
        if target == 0:
            #we rescale all other weights
            weights[1] = round((sum(weights[:2]) / pos_sep - 1) * self.base_weight)
            for n in range(2, len(weights)):
                weights[n] = round(weights[n] / pos_sep * self.base_weight)
        else:
            new_target = pos_sep - sum(weights[:target])
            new_next = sum(weights[:target + 2]) - pos_sep

            weights[target] = round(new_target)
            weights[target + 1] = round(new_next)

    def _avarage_weights(self, weights: list[int], target: int) -> None:
        #if the first row/column should change size
        if target == 0:
            #we rescale all other weights
            factor = 2 * self.base_weight / (self.base_weight + weights[1])
            weights[1] = self.base_weight
            for n in range(2, len(weights)):
                weights[n] = round(weights[n] * factor)
        else:
            #new weight is the mean of the current values
            new_value = round((weights[target] + weights[target + 1]) / 2)
            weights[target] = new_value
            weights[target + 1] = new_value

    def _extend_weights(self) -> None:
        #makes sure all weight lists have at least a number of elements equal to the used rows/columns.
        # new values are appended with a value that is the mean of the existing rows/columns.
        n_cols, n_rows = self.grid_size()

        for n in range(len(self._row_weights), n_rows):
            self._row_weights.append(round(sum(self._row_weights) / len(self._row_weights)))
            self.grid_rowconfigure(n, weight=self._row_weights[n], uniform="r")

        for n in range(len(self._column_weights), n_cols):
            self._column_weights.append(round(sum(self._column_weights) / len(self._column_weights)))
            self.grid_columnconfigure(n, weight=self._column_weights[n], uniform="c")

    def _update_separators(self) -> None:
        thickness = self._apply_scaling(self._theme_gv_info["thickness"])
        spacing = self._theme_gv_info["border_spacing"]

        actual_cols, actual_rows = self.grid_size()
        target_rows = len(self._row_weights)
        target_cols = len(self._column_weights)
        rowspan = 2 * target_rows - 1
        columnspan = 2 * target_cols - 1

        #bi-directional separators
        for row in range(1, target_rows):
            for column in range(1, target_cols):
                key = (row, column)
                separator = self._separators[key] if key in self._separators else self._create_separator(key, "both")
                separator.grid(row=2 * row - 1,
                               column=2 * column - 1,
                               sticky="nsew")
                separator.lift(self._canvas)

        #horizontal separators
        for row in range(1, max(actual_rows, target_rows)):
            #if row should be visible
            if row < target_rows:
                super().grid_rowconfigure(2 * row - 1, minsize=thickness)
                #create and show separator
                key = (row, None)
                separator = self._separators[key] if key in self._separators else self._create_separator(key, "horizontal")
                separator.grid(row=2 * row - 1,
                               column=0,
                               columnspan=columnspan,
                               sticky="nsew",
                               padx=spacing)
                separator.lift(self._canvas)
            else:
                super().grid_rowconfigure(2 * row - 1, minsize=0)
                #hide all separators assigned to this row
                for key, separator in self._separators.items():
                    if key[0] == row:
                        separator.grid_forget()

        #vertical separators
        for column in range(1, max(actual_cols, target_cols)):
            #if column should be visible
            if column < target_cols:
                super().grid_columnconfigure(2 * column - 1, minsize=thickness)
                #create and show separator
                key = (None, column)
                separator = self._separators[key] if key in self._separators else self._create_separator(key, "vertical")
                separator.grid(row=0,
                               column=2 * column - 1,
                               rowspan=rowspan,
                               sticky="nsew",
                               pady=spacing)
                separator.lift(self._canvas)
            else:
                super().grid_columnconfigure(2 * column - 1, minsize=0)
                #hide all separators assigned to this column
                for key, separator in self._separators.items():
                    if key[1] == column:
                        separator.grid_forget()

    def _create_separator(self,
                          key: tuple[int | None, int | None],
                          orientation: Literal["horizontal", "vertical", "both"]) -> CTkFrame:
        separator = CTkFrame(self,
                             width=0,
                             height=0,
                             corner_radius=0 if orientation == "both" else self._theme_gv_info["corner_radius"],
                             fg_color="transparent")
        separator.bind("<Enter>", partial(self._on_enter, *key))
        separator.bind("<Leave>", partial(self._on_leave, *key))
        separator.bind("<ButtonPress-1>", partial(self._clicked, *key))
        separator.bind("<ButtonRelease-1>", self._on_release)
        separator.bind("<Button-3>", partial(self._right_clicked, *key))
        self._separators[key] = separator
        self._set_cursor(key)
        return separator

    def _set_cursor(self, key: tuple[int | None, int | None]) -> None:
        if self._state != tkinter.NORMAL:
            mode = "normal"
        elif key[0] is None:
            mode = "move_hor"
        elif key[1] is None:
            mode = "move_ver"
        else:
            mode = "move_any"
        if cursor := get_proper_cursor(mode):
            self._separators[key].configure(cursor=cursor)

    def winfo_children(self) -> list[tkinter.Widget]:
        """ winfo_children of CTkGridView without separators,
        because they are not children but part of the CTkGridView itself """

        child_widgets = super().winfo_children()
        for separator in self._separators.values():
            try:
                child_widgets.remove(separator)
            except ValueError:
                pass
        return child_widgets

    def grid_rowconfigure(self,
                          index: int | list[int] | tuple[int, ...],
                          cnf: dict | None = None,
                          **kwargs: Any) -> Any:
        #rescale indexes to skip the rows dedicated to the separators
        index = 2 * index if isinstance(index, int) else tuple(2 * n for n in index)
        return super().grid_rowconfigure(index, cnf, **kwargs)

    def grid_columnconfigure(self,
                             index: int | list[int] | tuple[int, ...],
                             cnf: dict | None = None,
                             **kwargs: Any) -> Any:
        #rescale indexes to skip the columns dedicated to the separators
        index = 2 * index if isinstance(index, int) else tuple(2 * n for n in index)
        return super().grid_columnconfigure(index, cnf, **kwargs)

    def grid_size(self) -> tuple[int, int]:
        #convert values to omit the rows/columns dedicated to the separators
        retval = super().grid_size()
        return (retval[0] // 2 + 1, retval[1] // 2 + 1)

    def grid_slaves(self, row: int | None = None, column: int | None = None) -> list[CTkFrame]:
        """ grid_slaves of CTkGridView without separators,
        because they are not children but part of the CTkGridView itself """

        child_widgets = super().grid_slaves(None if row is None else 2 * row,
                                            None if column is None else 2 * column)
        for separator in self._separators.values():
            try:
                child_widgets.remove(separator)
            except ValueError:
                pass
        return child_widgets

    def configure(self, require_redraw: bool = False, **kwargs: Unpack[CTkGridViewArgs]) -> None:
        frame_kwargs = {}

        check_colors(kwargs, CTkGridViewThemedArgs)

        if "corner_radius" in kwargs:
            corner_radius = kwargs.pop("corner_radius")
            self._theme_gv_info["corner_radius"] = corner_radius
            frame_kwargs["corner_radius"] = corner_radius
            for key, separator in self._separators.items():
                if key[0] is None or key[1] is None:
                    separator.configure(corner_radius=corner_radius)

        if "border_width" in kwargs:
            self._theme_gv_info["border_width"] = kwargs.pop("border_width")
            frame_kwargs["border_width"] = self._theme_gv_info["border_width"]

        if "fg_color" in kwargs:
            self._theme_gv_info["fg_color"] = kwargs.pop("fg_color")
            frame_kwargs["fg_color"] = self._theme_gv_info["fg_color"]

        if "border_color" in kwargs:
            self._theme_gv_info["border_color"] = kwargs.pop("border_color")
            frame_kwargs["border_color"] = self._theme_gv_info["border_color"]

        if "thickness" in kwargs:
            self._theme_gv_info["thickness"] = kwargs.pop("thickness")
            self._update_separators()

        if "border_spacing" in kwargs:
            border_spacing = kwargs.pop("border_spacing")
            self._theme_gv_info["border_spacing"] = border_spacing
            self._update_separators()
            for frame in self._inner_frames.values():
                if frame.winfo_ismapped():
                    frame.grid(padx=border_spacing, pady=border_spacing)

        if "hover_color" in kwargs:
            self._theme_gv_info["hover_color"] = kwargs.pop("hover_color")

        if "hover" in kwargs:
            self._theme_gv_info["hover"] = kwargs.pop("hover")

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            self._on_release()
            for key in self._separators:
                self._set_cursor(key)

        if "min_rows_size" in kwargs:
            self._min_rows_size = kwargs.pop("min_rows_size")

        if "min_columns_size" in kwargs:
            self._min_columns_size = kwargs.pop("min_columns_size")

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        super().configure(require_redraw=require_redraw, **kwargs)
        if frame_kwargs:
            for frame in self._inner_frames.values():
                frame.configure(**frame_kwargs)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "min_rows_size":
            return self._min_rows_size
        elif attribute_name == "min_columns_size":
            return self._min_columns_size
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_gv_info and attribute_name not in CTkWidgetArgs.__annotations__:
            return self._theme_gv_info[attribute_name]
        else:
            return super().cget(attribute_name)

    def frame(self, name: str) -> CTkFrame:
        """ Returns reference to the frame with given name. """
        if name in self._inner_frames:
            return self._inner_frames[name]
        else:
            raise ValueError(f"CTkGridView has no frame named '{name}'")

    def insert(self,
               name: str,
               row: int | None = None,
               column: int | None = None,
               rowspan: int = 1,
               columnspan: int = 1,
               frame: CTkFrame | None = None) -> CTkFrame:
        """ Creates new frame with given name and returns it.\n
        You can also provide an already existing frame that has this widget as master.\n
        If the other parameters are provided, the new frame is placed at that position. """
        if name in self._inner_frames:
            raise ValueError(f"CTkGridView already has frame named '{name}'")

        if frame is None:
            frame = CTkFrame(self,
                             width=0,
                             height=0,
                             corner_radius=self._theme_gv_info["corner_radius"],
                             border_width=self._theme_gv_info["border_width"],
                             fg_color=self._theme_gv_info["fg_color"],
                             top_fg_color=self._theme_gv_info["top_fg_color"],
                             border_color=self._theme_gv_info["border_color"])
        elif frame.master is not self:
            raise RuntimeError("CTkGridView can't manage a CTkFrame that is not its child")

        self._inner_frames[name] = frame

        if row is not None and column is not None:
            self.show(name, row, column, rowspan, columnspan)
        return frame

    def delete(self, name: str, preserve_weights: bool = False) -> None:
        """ Deletes frame by name. """
        self.hide(name, preserve_weights)
        self._inner_frames.pop(name).destroy()

    def show(self, name: str, row: int, column: int, rowspan: int = 1, columnspan: int = 1) -> None:
        """ Shows a hidden frame by name and place it at the provided position. """
        if name not in self._inner_frames:
            raise ValueError(f"CTkGridView has no frame named '{name}'")

        spacing = self._theme_gv_info["border_spacing"]
        self._inner_frames[name].grid(row=2 * row,
                                      column=2 * column,
                                      rowspan=2 * rowspan - 1,
                                      columnspan=2 * columnspan - 1,
                                      sticky="nsew",
                                      padx=spacing, pady=spacing)
        self._extend_weights()
        self._update_separators()

    def hide(self, name: str, preserve_weights: bool = False) -> None:
        """ Hides frame by name.\n
        It is NOT deleted: it can be displayed again with show().\n
        If 'preserve_weights' is False, in case the last row/column becomes empty,
        it will be removed by redistributing the space to the other columns.\n
        If instead it is True, the size of all rows/columns won't change in any case."""
        if name not in self._inner_frames:
            raise ValueError(f"CTkGridView has no frame named '{name}'")

        self._inner_frames[name].grid_forget()

        if not preserve_weights:
            #while there are at least 2 rows
            while last_row := len(self._row_weights) - 1:
                #there are no widgets in the last row -> set its weight to 0
                if not self.grid_slaves(row=last_row):
                    self._row_weights.pop()
                    self.grid_rowconfigure(last_row, weight=0, uniform="")
                else:
                    break

            #while there are at least 2 columns
            while last_col := len(self._column_weights) - 1:
                #there are no widgets in the last column -> set its weight to 0
                if not self.grid_slaves(column=last_col):
                    self._column_weights.pop()
                    self.grid_columnconfigure(last_col, weight=0, uniform="")
                else:
                    break

            self._update_separators()

    def set(self,
            row_sizes: list[float] | None = None,
            column_sizes: list[float] | None = None) -> None:
        """ Sets all row and/or column sizes to the provided values,
        regardless of the widget's state and admissible values.\n
        The values represent [%] w.r.t. overall height/width.
        If the sum is not 1.0, the values will be rescaled accordingly.
        If you provide fewer values than needed, the mean value will be used for additional rows/columns. """
        if row_sizes is not None:
            sumvalues = sum(row_sizes)
            sumweight = self.base_weight * sumvalues / row_sizes[0]
            self._row_weights.clear()
            self._row_weights.extend(round(sumweight * value / sumvalues) for value in row_sizes)

        if column_sizes is not None:
            sumvalues = sum(column_sizes)
            sumweight = self.base_weight * sumvalues / column_sizes[0]
            self._column_weights.clear()
            self._column_weights.extend(round(sumweight * value / sumvalues) for value in column_sizes)

        self._extend_weights()

        for n, weight in enumerate(self._row_weights):
            self.grid_rowconfigure(n, weight=weight, uniform="r")
        for n, weight in enumerate(self._column_weights):
            self.grid_columnconfigure(n, weight=weight, uniform="c")

    def get(self, what: Literal["rows", "columns"]) -> list[float]:
        """ Returns the size of all rows/columns in [%] w.r.t. overall height/width. """
        if what == "rows":
            sumweight = sum(self._row_weights)
            return [weight/sumweight for weight in self._row_weights]
        elif what == "columns":
            sumweight = sum(self._column_weights)
            return [weight/sumweight for weight in self._column_weights]
        else:
            raise ValueError(f"Option '{what}' unknown.")
