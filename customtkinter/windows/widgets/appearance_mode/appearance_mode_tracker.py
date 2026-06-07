from __future__ import annotations

import tkinter
from typing import Callable
from typing_extensions import Literal
import darkdetect
from ..utility import get_window_root_of_widget


class AppearanceModeTracker:

    update_loop_interval: int = 100  # [ms]

    _callback_list: list[Callable[[Literal["light", "dark"]], None]] = []
    _app_list: list[tkinter.Tk | tkinter.Toplevel] = []
    _update_loop_running: bool = False
    _appearance_mode_set_by: Literal["user", "system"] = "system"
    _appearance_mode: int = 0  # 0: "light" 1: "dark"

    @classmethod
    def init_appearance_mode(cls) -> None:
        cls.update()

    @classmethod
    def set_appearance_mode(cls, mode: Literal["light", "dark", "system"]) -> None:
        if mode.lower() == "dark":
            cls._appearance_mode_set_by = "user"
            cls._activate_mode(1)

        elif mode.lower() == "light":
            cls._appearance_mode_set_by = "user"
            cls._activate_mode(0)

        elif mode.lower() == "system":
            cls._appearance_mode_set_by = "system"
            cls._start_update_loop()

    @classmethod
    def get_mode(cls) -> int:
        return cls._appearance_mode

    @classmethod
    def add(cls,
            callback: Callable[[Literal["light", "dark"]], None],
            widget: tkinter.Widget | None = None) -> None:
        cls._callback_list.append(callback)

        if widget is not None:
            app = get_window_root_of_widget(widget)
            if app not in cls._app_list:
                cls._app_list.append(app)

                #if the loop is not running (maybe because there weren't any apps available),
                # we try to start it
                if not cls._update_loop_running:
                    cls._start_update_loop()

    @classmethod
    def remove(cls, callback: Callable[[Literal["light", "dark"]], None]) -> None:
        try:
            cls._callback_list.remove(callback)
        except ValueError:
            pass

    @staticmethod
    def detect_appearance_mode() -> int:
        try:
            if darkdetect.theme() == "Dark":
                return 1  # Dark
            else:
                return 0  # Light
        except NameError:
            return 0  # Light

    @classmethod
    def update(cls) -> None:
        #check that system mode is still active
        if cls._appearance_mode_set_by == "system":
            cls._activate_mode(cls.detect_appearance_mode())

        cls._start_update_loop()

    @classmethod
    def _start_update_loop(cls) -> None:
        if cls._appearance_mode_set_by == "system":
            # find an existing tkinter.Tk object for the call of .after()
            for app in cls._app_list:
                try:
                    app.after(cls.update_loop_interval, cls.update)
                    cls._update_loop_running = True
                    return
                except Exception:
                    continue

        # no window has been found or conditions not met -> loop is not running
        cls._update_loop_running = False

    @classmethod
    def _activate_mode(cls, mode: int) -> None:
        if mode != cls._appearance_mode:
            cls._appearance_mode = mode
            for callback in cls._callback_list:
                try:
                    callback()
                except Exception:
                    continue
