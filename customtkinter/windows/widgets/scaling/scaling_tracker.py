from __future__ import annotations

import tkinter
import sys
from typing import Callable


class ScalingTracker:
    deactivate_automatic_dpi_awareness: bool = False

    # contains window objects as keys with list of widget callbacks as elements
    window_widgets_dict: dict[tkinter.Tk | tkinter.Toplevel, list[Callable[[float, float], None]]] = {}

    # contains window objects as keys and corresponding scaling factors
    window_dpi_scaling_dict: dict[tkinter.Tk | tkinter.Toplevel, float] = {}

    # user values which multiply to detected window scaling factor
    widget_scaling: float = 1.0
    window_scaling: float = 1.0

    update_loop_running: bool = False
    update_loop_interval: int = 100  # ms
    loop_pause_after_new_scaling: int = 1500  # ms

    @classmethod
    def get_widget_scaling(cls, widget: tkinter.Widget) -> float:
        window_root = cls.get_window_root_of_widget(widget)
        return cls.window_dpi_scaling_dict[window_root] * cls.widget_scaling

    @classmethod
    def get_window_scaling(cls, window: tkinter.Tk | tkinter.Toplevel) -> float:
        window_root = cls.get_window_root_of_widget(window)
        return cls.window_dpi_scaling_dict[window_root] * cls.window_scaling

    @classmethod
    def set_widget_scaling(cls, widget_scaling_factor: float) -> None:
        cls.widget_scaling = max(widget_scaling_factor, 0.4)
        cls.update_scaling_callbacks_all()

    @classmethod
    def set_window_scaling(cls, window_scaling_factor: float) -> None:
        cls.window_scaling = max(window_scaling_factor, 0.4)
        cls.update_scaling_callbacks_all()

    @classmethod
    def get_window_root_of_widget(cls, widget: tkinter.Misc) -> tkinter.Tk | tkinter.Toplevel:
        current_widget = widget

        while isinstance(current_widget, tkinter.Tk) is False and\
                isinstance(current_widget, tkinter.Toplevel) is False:
            current_widget = current_widget.master

        return current_widget

    @classmethod
    def update_scaling_callbacks_all(cls) -> None:
        for window, callback_list in cls.window_widgets_dict.items():
            for set_scaling_callback in callback_list:
                if not cls.deactivate_automatic_dpi_awareness:
                    set_scaling_callback(cls.window_dpi_scaling_dict[window] * cls.widget_scaling,
                                         cls.window_dpi_scaling_dict[window] * cls.window_scaling)
                else:
                    set_scaling_callback(cls.widget_scaling,
                                         cls.window_scaling)

    @classmethod
    def update_scaling_callbacks_for_window(cls, window: tkinter.Tk | tkinter.Toplevel) -> None:
        for set_scaling_callback in cls.window_widgets_dict[window]:
            if not cls.deactivate_automatic_dpi_awareness:
                set_scaling_callback(cls.window_dpi_scaling_dict[window] * cls.widget_scaling,
                                     cls.window_dpi_scaling_dict[window] * cls.window_scaling)
            else:
                set_scaling_callback(cls.widget_scaling,
                                     cls.window_scaling)

    @classmethod
    def add_widget(cls,
                   widget_callback: Callable[[float, float], None],
                   widget: tkinter.Widget) -> None:
        window_root = cls.get_window_root_of_widget(widget)

        if window_root not in cls.window_widgets_dict:
            cls.window_widgets_dict[window_root] = [widget_callback]
        else:
            cls.window_widgets_dict[window_root].append(widget_callback)

        if window_root not in cls.window_dpi_scaling_dict:
            cls.window_dpi_scaling_dict[window_root] = cls.get_window_dpi_scaling(window_root)

        if not cls.update_loop_running:
            window_root.after(100, cls.check_dpi_scaling)
            cls.update_loop_running = True

    @classmethod
    def remove_widget(cls,
                      widget_callback: Callable[[float, float], None],
                      widget: tkinter.Widget) -> None:
        window_root = cls.get_window_root_of_widget(widget)
        try:
            cls.window_widgets_dict[window_root].remove(widget_callback)
        except Exception:
            pass

    @classmethod
    def remove_window(cls, window: tkinter.Tk | tkinter.Toplevel) -> None:
        try:
            del cls.window_widgets_dict[window]
        except Exception:
            pass

    @classmethod
    def add_window(cls,
                   window_callback: Callable[[float, float], None],
                   window: tkinter.Tk | tkinter.Toplevel) -> None:
        if window not in cls.window_widgets_dict:
            cls.window_widgets_dict[window] = [window_callback]
        else:
            cls.window_widgets_dict[window].append(window_callback)

        if window not in cls.window_dpi_scaling_dict:
            cls.window_dpi_scaling_dict[window] = cls.get_window_dpi_scaling(window)

    @classmethod
    def activate_high_dpi_awareness(cls) -> None:
        """ make process DPI aware, customtkinter elements will get scaled automatically,
            only gets activated when CTk object is created """

        if not cls.deactivate_automatic_dpi_awareness:
            if sys.platform == "darwin":
                pass  # high DPI scaling works automatically on macOS

            elif sys.platform.startswith("win"):
                import ctypes

                # Values for SetProcessDpiAwareness and SetProcessDpiAwarenessContext:
                # internal enum PROCESS_DPI_AWARENESS
                # {
                #     Process_DPI_Unaware = 0,
                #     Process_System_DPI_Aware = 1,
                #     Process_Per_Monitor_DPI_Aware = 2
                # }
                #
                # internal enum DPI_AWARENESS_CONTEXT
                # {
                #     DPI_AWARENESS_CONTEXT_UNAWARE = 16,
                #     DPI_AWARENESS_CONTEXT_SYSTEM_AWARE = 17,
                #     DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE = 18,
                #     DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = 34
                # }

                # ctypes.windll.user32.SetProcessDpiAwarenessContext(34)  # Non client area scaling at runtime (titlebar)
                # does not work with resizable(False, False), window starts growing on monitor with different scaling (weird tkinter bug...)
                # ctypes.windll.user32.EnableNonClientDpiScaling(hwnd) does not work for some reason (tested on Windows 11)

                # It's too bad, that these Windows API methods don't work properly with tkinter. But I tested days with multiple monitor setups,
                # and I don't think there is anything left to do. So this is the best option at the moment:

                ctypes.windll.shcore.SetProcessDpiAwareness(2)  # Titlebar does not scale at runtime
            else:
                pass  # DPI awareness on Linux not implemented

    @classmethod
    def get_window_dpi_scaling(cls, window: tkinter.Tk | tkinter.Toplevel) -> float:
        if not cls.deactivate_automatic_dpi_awareness:
            if sys.platform == "darwin":
                return 1.0  # scaling works automatically on macOS

            elif sys.platform.startswith("win"):
                from ctypes import windll, pointer, wintypes

                DPI100pc = 96  # DPI 96 is 100% scaling
                DPI_type = 0  # MDT_EFFECTIVE_DPI = 0, MDT_ANGULAR_DPI = 1, MDT_RAW_DPI = 2
                window_hwnd = wintypes.HWND(window.winfo_id())
                monitor_handle = windll.user32.MonitorFromWindow(window_hwnd, wintypes.DWORD(2))  # MONITOR_DEFAULTTONEAREST = 2
                x_dpi, y_dpi = wintypes.UINT(), wintypes.UINT()
                windll.shcore.GetDpiForMonitor(monitor_handle, DPI_type, pointer(x_dpi), pointer(y_dpi))
                return (x_dpi.value + y_dpi.value) / (2 * DPI100pc)

            else:
                return 1.0  # DPI awareness on Linux not implemented
        else:
            return 1.0

    @classmethod
    def check_dpi_scaling(cls) -> None:
        new_scaling_detected = False

        # check for every window if scaling value changed
        for window in cls.window_widgets_dict:
            if window.winfo_exists() and not window.state() == "iconic":
                current_dpi_scaling_value = cls.get_window_dpi_scaling(window)
                if current_dpi_scaling_value != cls.window_dpi_scaling_dict[window]:
                    cls.window_dpi_scaling_dict[window] = current_dpi_scaling_value

                    if sys.platform.startswith("win"):
                        window.attributes("-alpha", 0.15)

                    window.block_update_dimensions_event()
                    cls.update_scaling_callbacks_for_window(window)
                    window.unblock_update_dimensions_event()

                    if sys.platform.startswith("win"):
                        window.attributes("-alpha", 1)

                    new_scaling_detected = True

        # find an existing tkinter object for the next call of .after()
        for window in cls.window_widgets_dict:
            try:
                if new_scaling_detected:
                    window.after(cls.loop_pause_after_new_scaling, cls.check_dpi_scaling)
                else:
                    window.after(cls.update_loop_interval, cls.check_dpi_scaling)
                return
            except Exception:
                continue

        cls.update_loop_running = False
