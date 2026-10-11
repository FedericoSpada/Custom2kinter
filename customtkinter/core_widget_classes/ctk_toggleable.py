from __future__ import annotations

import tkinter
from abc import ABC
from threading import Lock
from typing import Callable
from typing_extensions import Literal


class CTkToggleable(ABC):
    """
    Base class of every widget with 2 internal states ("on"/"off").

    The states are associated with 'onvalue' and 'offvalue', and optionally kept in sync with a 'variable'.
    It provides get(), set(), select(), deselect() and invoke(), plus the 'pre_command' and 'command' callbacks.
    """

    def __init__(self) -> None:
        self._check_state: bool = False
        self._onvalue: int | float | str | bool = True
        self._offvalue: int | float | str | bool = False

        self._state: Literal["normal", "disabled"] = tkinter.NORMAL
        self._pre_command: Callable[[int | float | str | bool], Literal["break"] | None] | None = None
        self._command: Callable[[int | float | str | bool], None] | None = None
        self._variable: tkinter.Variable | None = None
        self._variable_callback_name: str | None = None
        self._block_value_propagation: Lock = Lock()

    def _update_variable(self, variable: tkinter.Variable | None) -> None:
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)
        self._variable = variable
        if self._variable is not None:
            self._variable_callback_name = self._variable.trace_add("write", self._variable_callback)
            self._variable_callback()

    def _variable_callback(self, *_: str) -> None:
        if not self._block_value_propagation.locked():
            with self._block_value_propagation:
                if self._variable.get() == self._onvalue:
                    self.set(state=True)
                elif self._variable.get() == self._offvalue:
                    self.set(state=False)

    def destroy(self) -> None:
        """Stops tracking the linked 'variable' (to be called when the widget is destroyed)."""
        if self._variable is not None:
            self._variable.trace_remove("write", self._variable_callback_name)

    def set(self, value: int | float | str | bool | None = None, state: bool | None = None) -> None:
        """
        Changes the internal state, regardless of the widget's 'state', without invoking any callback.

        Args:
            value: 'onvalue' to set the "on" state, any other value for "off" (None to use 'state' instead).
            state: True for "on", False for "off" (used only if 'value' is None).
        """
        if value is not None:
            self._check_state = value == self._onvalue
        elif state is not None:
            self._check_state = state

        if self._variable is not None and not self._block_value_propagation.locked():
            with self._block_value_propagation:
                self._variable.set(self._onvalue if self._check_state else self._offvalue)

    def invoke(self, _: tkinter.Event | None = None) -> None:
        """
        Toggles the internal state between "on" and "off" if the widget is not disabled and
        'pre_command' doesn't return "break"; then 'command' is invoked.
        Can be called to simulate the user who clicks on the widget.
        """
        if self._state == tkinter.NORMAL:
            new_value = self._offvalue if self._check_state else self._onvalue
            retval = "" if self._pre_command is None else self._pre_command(new_value)

            #if _pre_command() returns exactly "break", operation is stopped
            if retval != "break":
                self.set(state=not self._check_state)

                if self._command is not None:
                    self._command(self._onvalue if self._check_state else self._offvalue)

    def select(self) -> None:
        """Sets the internal state to "on" (shortcut for set(state=True))."""
        self.set(state=True)

    def deselect(self) -> None:
        """Sets the internal state to "off" (shortcut for set(state=False))."""
        self.set(state=False)

    def get(self) -> int | float | str | bool:
        """Returns 'onvalue' or 'offvalue' based on the internal state."""
        return self._onvalue if self._check_state else self._offvalue
