from __future__ import annotations

import tkinter
from typing_extensions import TypedDict, Unpack

from .ctk_toplevel import CTkToplevel
from .widgets import CTkLabel
from .widgets.ctk_button import CTkButton, CTkButtonArgs
from .widgets.ctk_entry import CTkEntry, CTkEntryArgs
from .widgets.font.ctk_font import CTkFont, CTkFontArgs
from .widgets.theme import ThemeManager


class CTkInputDialogArgs(TypedDict, total=False):
    fg_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    title: str
    text: str
    font: CTkFontArgs | CTkFont | tuple | str
    button: CTkButtonArgs
    entry: CTkEntryArgs


class CTkInputDialog(CTkToplevel):
    """
    Dialog with extra window, message, entry widget, cancel and ok button.
    For detailed information check out the documentation.
    """

    def __init__(self,
                 master: tkinter.Misc | None = None,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkInputDialogArgs]) -> None:

        self._theme_id_info: CTkInputDialogArgs = ThemeManager.get_info("CTkInputDialog", theme_key, **kwargs)

        #validity checks
        for key in self._theme_id_info:
            if "_color" in key:
                self._theme_id_info[key] = self._check_color_type(self._theme_id_info[key], transparency=False)

        super().__init__(master=master,
                         fg_color=self._theme_id_info["fg_color"],
                         title=self._theme_id_info["title"])

        self._user_input: str | None = None
        self._running: bool = False

        self._font: CTkFont = CTkFont.from_parameter(self._theme_id_info["font"])
        self._label: CTkLabel
        self._entry: CTkEntry
        self._ok_button: CTkButton
        self._cancel_button: CTkButton

        self.lift()  # lift window on top
        self.attributes("-topmost", True)  # stay on top
        self.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.after(10, self._create_widgets)  # create widgets with slight delay, to avoid white flickering of background
        self.resizable(False, False)
        self.grab_set()  # make other windows not clickable

    def _create_widgets(self) -> None:
        self.grid_columnconfigure((0, 1), weight=1)
        self.rowconfigure(0, weight=1)

        self._label = CTkLabel(master=self,
                               width=300,
                               wraplength=300,
                               fg_color="transparent",
                               text_color=self._theme_id_info["text_color"],
                               text=self._theme_id_info["text"],
                               font=self._font)
        self._label.grid(row=0, column=0, columnspan=2, padx=20, pady=20, sticky="ew")

        entry_kwargs = self._theme_id_info["entry"]
        entry_kwargs["font"] = self._font
        self._entry = CTkEntry(master=self, **entry_kwargs)
        self._entry.grid(row=1, column=0, columnspan=2, padx=20, pady=(0, 20), sticky="ew")

        button_kwargs = self._theme_id_info["button"]
        button_kwargs["font"] = self._font
        button_kwargs["width"] = 100

        self._ok_button = CTkButton(master=self,
                                    command=self._ok_event,
                                    text="Ok",
                                    **button_kwargs)
        self._ok_button.grid(row=2, column=0, columnspan=1, padx=(20, 10), pady=(0, 20), sticky="ew")

        self._cancel_button = CTkButton(master=self,
                                        command=self._cancel_event,
                                        text="Cancel",
                                        **button_kwargs)
        self._cancel_button.grid(row=2, column=1, columnspan=1, padx=(10, 20), pady=(0, 20), sticky="ew")

        self.after(150, self._entry.focus)  # set focus to entry with slight delay, otherwise it won't work
        self._entry.bind("<Return>", self._ok_event)

    def _ok_event(self, _: tkinter.Event | None = None) -> None:
        self._user_input = self._entry.get()
        self.grab_release()
        self.destroy()

    def _on_closing(self) -> None:
        self.grab_release()
        self.destroy()

    def _cancel_event(self) -> None:
        self.grab_release()
        self.destroy()

    def get_input(self) -> str | None:
        self.master.wait_window(self)
        return self._user_input
