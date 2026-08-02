from __future__ import annotations

import tkinter
import copy
import math
from functools import partial
from typing import Any, Callable
from typing_extensions import Literal, Unpack

from .core_widget_classes import CTkContainer
from .theme import ThemeManager
from .ctk_scrollable_frame import CTkScrollableFrame, CTkScrollableFrameThemedArgs, CTkScrollableFrameArgs
from .ctk_togglebutton import CTkToggleButton, CTkToggleButtonThemedArgs
from .utility import pop_from_dict_by_iterable, check_kwargs_empty, deep_update, first_value


class CTkListBoxThemedArgs(CTkScrollableFrameThemedArgs, total=False, closed=True):
    internal_spacing: int
    columns: int
    rows: int
    togglebutton: CTkToggleButtonThemedArgs

class CTkListBoxArgs(CTkListBoxThemedArgs, total=False, closed=True):
    state: Literal["normal", "disabled"]
    values: list[str]
    min_selected: int
    max_selected: int  #"0" means no limit
    deselect_oldest: bool
    pre_command: Callable[[str], Literal["break"] | None] | None
    command: Callable[[str], None] | None


class CTkListBox(CTkScrollableFrame):
    """
    ListBox with corner radius, border width, multi-columns/rows and multi-selection support.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: CTkContainer,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkListBoxArgs]) -> None:

        theme_args = pop_from_dict_by_iterable(kwargs, CTkListBoxThemedArgs.__annotations__)
        self._theme_lb_info: CTkListBoxThemedArgs = ThemeManager.get_info("CTkListBox", theme_key, **theme_args)

        frame_kwargs = {key: self._theme_lb_info[key] for key in CTkScrollableFrameThemedArgs.__annotations__}
        super().__init__(master=master, **frame_kwargs)

        #functionality
        self._state: Literal["normal", "disabled"] = kwargs.pop("state", tkinter.NORMAL)
        self._pre_command: Callable[[str], Literal["break"] | None] | None = kwargs.pop("pre_command", None)
        self._command: Callable[[str], None] | None = kwargs.pop("command", None)
        self._min_selected: int = kwargs.pop("min_selected", 0)
        self._max_selected: int = kwargs.pop("max_selected", 1)
        self._deselect_oldest: bool = kwargs.pop("deselect_oldest", self._max_selected == 1)
        self._values: list[str] = kwargs.pop("values", [])
        self._selected_values: list[str] = self._values[:self._min_selected]
        self._buttons: dict[str, CTkToggleButton] = {}

        # check for unknown arguments
        check_kwargs_empty(kwargs, raise_error=True)

        self._create_buttons_from_values()
        self._update_buttons_geometry()

    def _set_scaling(self, new_widget_scaling: float, new_window_scaling: float) -> None:
        super()._set_scaling(new_widget_scaling, new_window_scaling)
        self._update_buttons_geometry()

    def _create_buttons_from_values(self) -> None:
        if len(self._values) != len(set(self._values)):
            raise ValueError("CTkListBox values are not unique")

        for button in self._buttons.values():
            button.destroy()
        self._buttons.clear()
        button_kwargs = self._theme_lb_info["togglebutton"]
        for value in self._values:
            self._buttons[value] = CTkToggleButton(self,
                                                   text=value,
                                                   state=self._state,
                                                   pre_command=partial(self.invoke, value),
                                                   corner_radius=self._theme_lb_info["corner_radius"],
                                                   **button_kwargs)
            if value in self._selected_values:
                self._buttons[value].set(state=True)

    def _update_buttons_geometry(self) -> None:
        spacing = self._apply_scaling(self._theme_lb_info["internal_spacing"])
        n_cols = self._theme_lb_info["columns"]
        n_rows = self._theme_lb_info["rows"]

        #if both are "0", set proper value based on the orientation
        if n_cols == 0 and n_rows == 0:
            orientation = self._theme_info["orientation"]
            if orientation == "vertical":
                n_cols = 1
            elif orientation == "horizontal":
                n_rows = 1
            else:
                n_cols = math.ceil(math.sqrt(len(self._values)))

        #calculate the other based on the provided one ("columns" has priority)
        if n_cols != 0:
            n_rows = math.ceil(len(self._values) / n_cols)
        else:
            n_cols = math.ceil(len(self._values) / n_rows)

        if n_cols > 0:
            self.grid_columnconfigure(tuple(range(n_cols)), weight=1)
        if n_rows > 0:
            self.grid_rowconfigure(tuple(range(n_rows)), weight=1)
        prev_cols, prev_rows = self.grid_size()
        if prev_cols > n_cols:
            self.grid_columnconfigure(tuple(range(n_cols, prev_cols)), weight=0)
        if prev_rows > n_rows:
            self.grid_rowconfigure(tuple(range(n_rows, prev_rows)), weight=0)

        for n, value in enumerate(self._values):
            row = n // n_cols
            colunm = n % n_cols
            self._buttons[value].grid(row=row,
                                      column=colunm,
                                      sticky="nsew",
                                      padx=(0, spacing if colunm < n_cols - 1 else 0),
                                      pady=(0, spacing if row < n_rows - 1 else 0))

    def configure(self, **kwargs: Unpack[CTkListBoxArgs]) -> None:
        require_geometry = False

        if "internal_spacing" in kwargs:
            self._theme_lb_info["internal_spacing"] = kwargs.pop("internal_spacing")
            require_geometry = True

        if "columns" in kwargs:
            self._theme_lb_info["columns"] = kwargs.pop("columns")
            require_geometry = True

        if "rows" in kwargs:
            self._theme_lb_info["rows"] = kwargs.pop("rows")
            require_geometry = True

        if "state" in kwargs:
            self._state = kwargs.pop("state")
            for button in self._buttons.values():
                button.configure(state=self._state)

        if "values" in kwargs:
            self._values = kwargs.pop("values")
            self._create_buttons_from_values()
            require_geometry = True

        if "deselect_oldest" in kwargs:
            self._deselect_oldest = kwargs.pop("deselect_oldest")

        if "min_selected" in kwargs:
            self._min_selected = kwargs.pop("min_selected")

        if "max_selected" in kwargs:
            self._max_selected = kwargs.pop("max_selected")
            if self._deselect_oldest:
                while len(self._selected_values) > self._max_selected:
                    self._buttons[self._selected_values.pop(0)].set(state=False)

        if "pre_command" in kwargs:
            self._pre_command = kwargs.pop("pre_command")

        if "command" in kwargs:
            self._command = kwargs.pop("command")

        if "togglebutton" in kwargs:
            button_kwargs = kwargs.pop("togglebutton")
            deep_update(self._theme_lb_info["togglebutton"], button_kwargs)
            for button in self._buttons.values():
                button.configure(**button_kwargs)

        super().configure(**kwargs)
        if require_geometry:
            self._update_buttons_geometry()

    def cget(self, attribute_name: str) -> Any:
        if attribute_name == "state":
            return self._state
        elif attribute_name == "values":
            return copy.copy(self._values)
        elif attribute_name == "min_selected":
            return self._min_selected
        elif attribute_name == "max_selected":
            return self._max_selected
        elif attribute_name == "deselect_oldest":
            return self._deselect_oldest
        elif attribute_name == "pre_command":
            return self._pre_command
        elif attribute_name == "command":
            return self._command
        elif attribute_name in self._theme_lb_info and attribute_name not in CTkScrollableFrameArgs.__annotations__:
            return self._theme_lb_info[attribute_name]
        elif attribute_name.startswith("togglebutton_"):
            return first_value(self._buttons).cget(attribute_name.removeprefix("togglebutton_"))
        else:
            return super().cget(attribute_name)

    def button(self, name: str) -> CTkToggleButton:
        """ Returns reference to the button with given name. """
        if name in self._buttons:
            return self._buttons[name]
        else:
            raise ValueError(f"CTkListBox has no value '{name}'")

    def invoke(self, value: str, _: bool | None = None) -> str:
        """ Toggles the active status for the provided value.\n
        Can be called to simulate the user who clicks on a specific button. """
        if self._state == tkinter.NORMAL:
            retval = "" if self._pre_command is None else self._pre_command(value)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                run_command = False

                #value has been selected
                if value not in self._selected_values:
                    #if there are no limits or auto-deselect mode is active or upper limit has not been reached
                    if self._max_selected == 0 or self._deselect_oldest or len(self._selected_values) < self._max_selected:
                        self._selected_values.append(value)
                        self._buttons[value].set(state=True)
                        run_command = True

                        #if auto-deselect mode is active, deselect oldest values until the limit is respected
                        if self._deselect_oldest:
                            while len(self._selected_values) > self._max_selected:
                                self._buttons[self._selected_values.pop(0)].set(state=False)
                #value has been deselected
                else:
                    #if lower limit has not been reached
                    if len(self._selected_values) > self._min_selected:
                        self._selected_values.remove(value)
                        self._buttons[value].set(state=False)
                        run_command = True

                if run_command and self._command is not None:
                    self._command(value)

        #toggle_buttons' state is changed directly using set(), so we block the normal change
        return "break"

    def set(self, selected_values: list[str]) -> None:
        """ Changes the selected values to the desired ones,
        regardless of the widget's state and admissible values. """
        for value in self._values:
            if value not in self._selected_values and value in selected_values:
                self._buttons[value].set(state=True)
            elif value in self._selected_values and value not in selected_values:
                self._buttons[value].set(state=False)
        self._selected_values.clear()
        self._selected_values.extend(selected_values)

    def get(self, index: int | None = None) -> str | list[str]:
        """ Returns the current active values, in the order the user selected them.\n
        If an index is provided, returns the value in that position. """
        if index is None:
            return copy.copy(self._selected_values)
        else:
            return self._values[index]

    def index(self, value: str | None = None) -> int | list[int]:
        """ Returns index of all selected values, raises ValueError if any value is missing.\n
        If the parameter is provided, returns the associated index or raises ValueError if the value is not found. """
        if value is None:
            return [self._values.index(value) for value in self._selected_values]
        else:
            return self._values.index(value)
