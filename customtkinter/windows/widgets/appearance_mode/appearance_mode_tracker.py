from __future__ import annotations

import tkinter
from typing import Callable
from typing_extensions import Literal
import darkdetect


class AppearanceModeTracker:

    callback_list: list[Callable[[Literal["light", "dark"]], None]] = []
    app_list: list[tkinter.Tk] = []
    update_loop_running: bool = False
    update_loop_interval: int = 30  # milliseconds

    appearance_mode_set_by: Literal["user", "system"] = "system"
    appearance_mode: int = 0  # 0: "Light" 1: "Dark"

    @classmethod
    def init_appearance_mode(cls) -> None:
        if cls.appearance_mode_set_by == "system":
            new_appearance_mode = cls.detect_appearance_mode()

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

    @classmethod
    def add(cls,
            callback: Callable[[Literal["light", "dark"]], None],
            widget: tkinter.Widget | None = None) -> None:
        cls.callback_list.append(callback)

        if widget is not None:
            app = cls.get_tk_root_of_widget(widget)
            if app not in cls.app_list:
                cls.app_list.append(app)

                if not cls.update_loop_running:
                    app.after(cls.update_loop_interval, cls.update)
                    cls.update_loop_running = True

    @classmethod
    def remove(cls, callback: Callable[[Literal["light", "dark"]], None]) -> None:
        try:
            cls.callback_list.remove(callback)
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
    def get_tk_root_of_widget(cls, widget: tkinter.Misc) -> tkinter.Tk:
        current_widget = widget

        while isinstance(current_widget, tkinter.Tk) is False:
            current_widget = current_widget.master

        return current_widget

    @classmethod
    def update_callbacks(cls) -> None:
        if cls.appearance_mode == 0:
            for callback in cls.callback_list:
                try:
                    callback("light")
                except Exception:
                    continue

        elif cls.appearance_mode == 1:
            for callback in cls.callback_list:
                try:
                    callback("dark")
                except Exception:
                    continue

    @classmethod
    def update(cls) -> None:
        if cls.appearance_mode_set_by == "system":
            new_appearance_mode = cls.detect_appearance_mode()

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        # find an existing tkinter.Tk object for the next call of .after()
        for app in cls.app_list:
            try:
                app.after(cls.update_loop_interval, cls.update)
                return
            except Exception:
                continue

        cls.update_loop_running = False

    @classmethod
    def get_mode(cls) -> int:
        return cls.appearance_mode

    @classmethod
    def set_appearance_mode(cls, mode: Literal["light", "dark", "system"]) -> None:
        if mode.lower() == "dark":
            cls.appearance_mode_set_by = "user"
            new_appearance_mode = 1

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        elif mode.lower() == "light":
            cls.appearance_mode_set_by = "user"
            new_appearance_mode = 0

            if new_appearance_mode != cls.appearance_mode:
                cls.appearance_mode = new_appearance_mode
                cls.update_callbacks()

        elif mode.lower() == "system":
            cls.appearance_mode_set_by = "system"
