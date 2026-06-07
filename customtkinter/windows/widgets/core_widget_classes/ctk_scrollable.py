from __future__ import annotations

import tkinter
import sys
from abc import ABC, abstractmethod
from typing_extensions import Literal


class CTkScrollable(ABC):

    scroll_duration: int = 500  #extra time in [ms] that is waited before declaring the scroll session finished

    __bind_all_done: bool = False
    __scrolled_widget: CTkScrollable | None = None
    __after_id: str | None = None

    def __init__(self, root: tkinter.Misc) -> None:
        #if at least 1 scrollable widget is used, bind the scroll dispatcher to all widgets
        if not CTkScrollable.__bind_all_done:
            CTkScrollable.__bind_all_done = True
            if sys.platform == "darwin" or sys.platform.startswith("win"):
                root.bind_all("<MouseWheel>", self.__mouse_scroll_event, add=True)
            else:
                root.bind_all("<Button-4>", self.__mouse_scroll_event, add=True)
                root.bind_all("<Button-5>", self.__mouse_scroll_event, add=True)

    @abstractmethod
    def _on_scroll(self,
                   event: tkinter.Event,
                   is_up: bool,
                   normalized_delta: int,
                   modifier: Literal["", "shift", "ctrl"]) -> str | None:
        #called when the user scrolls on the widget
        pass

    def is_scroll_ongoing(self) -> bool:
        return self is self.__scrolled_widget


    @classmethod
    def __mouse_scroll_event(cls, event: tkinter.Event) -> str | None:
        #stop "after" callback in any case: it will be restarted if needed
        if cls.__after_id is not None:
            event.widget.winfo_toplevel().after_cancel(cls.__after_id)
            cls.__after_id = None

        #if the current scrolled widget is not in the hierarchy of the targeted widget,
        # the mouse has been moved outside the scrolled widget, so the scroll session ends immediately
        if cls.__scrolled_widget is not None:
            widget = event.widget
            while widget is not None:
                if widget is cls.__scrolled_widget:
                    break
                widget = widget.master
            else:
                cls.__scrolled_widget = None

        #if no widget is already being scrolled, look for the first scrollable object in
        # the hierarchy of the targeted widget
        if cls.__scrolled_widget is None:
            widget = event.widget
            while widget is not None:
                if isinstance(widget, CTkScrollable):
                    #if found, it is the new target of the scroll session
                    cls.__scrolled_widget = widget
                    break
                widget = widget.master

        #there actually is a widget being scrolled
        if cls.__scrolled_widget is not None:
            #schedule the end of the scrolling session
            cls.__after_id = event.widget.winfo_toplevel().after(cls.scroll_duration, cls.__end_scroll_callback)

            #run callback
            is_up = event.delta > 0 or event.num == 4

            if sys.platform.startswith("win"):
                delta = event.delta // 120
            elif sys.platform == "darwin":
                delta = event.delta
            else:
                delta = 1 if event.num == 4 else -1

            if event.state & 0x1:
                modifier = "shift"
            elif event.state & 0x4:
                modifier = "ctrl"
            else:
                modifier = ""

            return cls.__scrolled_widget._on_scroll(event, is_up, delta, modifier)
        return None

    @classmethod
    def __end_scroll_callback(cls) -> None:
        cls.__scrolled_widget = None
        cls.__after_id = None
