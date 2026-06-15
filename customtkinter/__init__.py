__version__ = "5.3.0"

import os
import sys
from tkinter import Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, TclVersion
from tkinter.constants import *
import tkinter.filedialog as filedialog
from typing_extensions import Literal

# import manager classes
from .windows.widgets.appearance_mode import AppearanceModeTracker
from .windows.widgets.font import FontManager
from .windows.widgets.scaling import ScalingTracker
from .windows.widgets.theme import ThemeManager
from .windows.widgets.core_rendering import DRAWING_METHODS
from .windows.widgets.core_rendering import Arrow
from .windows.widgets.core_rendering import Bar
from .windows.widgets.core_rendering import BaseShape
from .windows.widgets.core_rendering import BorderedRoundedRect
from .windows.widgets.core_rendering import Checkmark
from .windows.widgets.core_rendering import RoundedRect

# import base widgets
from .windows.widgets.core_rendering import CTkCanvas
from .windows.widgets.core_widget_classes import CTkContainer
from .windows.widgets.core_widget_classes import CTkScrollable
from .windows.widgets.core_widget_classes import CTkWidget

# import widgets
from .windows.widgets import CTkButton
from .windows.widgets import CTkCheckBox
from .windows.widgets import CTkComboBox
from .windows.widgets import CTkEntry
from .windows.widgets import CTkFloatingFrame
from .windows.widgets import CTkFrame
from .windows.widgets import CTkLabel
from .windows.widgets import CTkOptionMenu
from .windows.widgets import CTkProgressBar
from .windows.widgets import CTkRadioButton
from .windows.widgets import CTkScrollbar
from .windows.widgets import CTkSegmentedButton
from .windows.widgets import CTkSlider
from .windows.widgets import CTkSpinBox
from .windows.widgets import CTkSwitch
from .windows.widgets import CTkTabview
from .windows.widgets import CTkTextbox
from .windows.widgets import CTkToolTip
from .windows.widgets import CTkScrollableFrame

# import windows
from .windows import CTk
from .windows import CTkToplevel
from .windows import CTkInputDialog

# import auxiliary classes
from .windows.widgets.font import CTkFont
from .windows.widgets.image import CTkImage

# import type aliases
from .windows.widgets.theme import AnchorType
from .windows.widgets.theme import ColorType
from .windows.widgets.theme import TransparentColorType
from .windows.widgets.core_rendering import DrawingMethodType
from .windows.widgets.core_rendering import SectionType
from .windows.widgets.font import FontType
from .windows.widgets.image import ImageType

from .windows import ctk_tk

_ = Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, CENTER, filedialog  # prevent IDE from removing unused imports


def set_appearance_mode(mode: Literal["light", "dark", "system"]) -> None:
    """ possible values: light, dark, system """
    AppearanceModeTracker.set_appearance_mode(mode)


def get_appearance_mode() -> Literal["light", "dark"]:
    """ get current state of the appearance mode (light or dark) """
    if AppearanceModeTracker.get_mode() == 0:
        return "light"
    elif AppearanceModeTracker.get_mode() == 1:
        return "dark"
    raise RuntimeError("Something went very wrong")


def set_default_color_theme(theme_name_or_path: str) -> None:
    """ set theme info with built-in color scheme or load custom theme file by passing the path """
    ThemeManager.load_theme(theme_name_or_path, add=False)


def add_color_theme(theme_path: str) -> None:
    """ update theme info by appending custom theme file by passing the path """
    ThemeManager.load_theme(theme_path, add=True)


def set_widget_scaling(scaling_value: float) -> None:
    """ set scaling for the widget dimensions """
    ScalingTracker.set_widget_scaling(scaling_value)


def set_window_scaling(scaling_value: float) -> None:
    """ set scaling for window dimensions """
    ScalingTracker.set_window_scaling(scaling_value)


def deactivate_automatic_dpi_awareness() -> None:
    """ deactivate DPI awareness of current process (windll.shcore.SetProcessDpiAwareness(0)) """
    ScalingTracker.deactivate_automatic_dpi_awareness = True


def run_showroom() -> None:
    set_appearance_mode("light")
    set_default_color_theme("blue")

    new_instance: bool = True
    while new_instance:
        app = _Showroom()
        app.mainloop()
        new_instance = app.new_instance_requested


class _Showroom(CTk):
    SPACING = 20

    def __init__(self) -> None:
        super().__init__()

        # configure window
        self.title("CustomTkinter Showroom")
        self.geometry("+200+50")

        self.new_instance_requested: bool = False

        customtkinter_directory = os.path.dirname(os.path.abspath(__file__))
        self.image = CTkImage(light_image=os.path.join(customtkinter_directory, "assets", "icons", "CustomTkinter_icon_Windows.ico"),
                              height=20)

        # create sidebar frame with widgets
        self.sidebar_frame = CTkFrame(self, width=140, corner_radius=0)
        self.logo_label = CTkLabel(self.sidebar_frame, text="CustomTkinter", font=CTkFont(size=20, weight="bold"))
        self.theme_label = CTkLabel(self.sidebar_frame, text="Theme:", anchor="w")
        self.theme_optionmenu = CTkOptionMenu(self.sidebar_frame, values=ThemeManager._built_in_themes,
                                              command=self._change_theme)
        self.theme_optionmenu.set(ThemeManager._last_loaded_theme)
        self.appearance_mode_label = CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_optionemenu = CTkOptionMenu(self.sidebar_frame, values=["light", "dark", "system"],
                                                         command=set_appearance_mode)
        self.appearance_mode_optionemenu.set(get_appearance_mode())
        self.scaling_label = CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_spinbox = CTkSpinBox(self.sidebar_frame, from_=0.5, to=2.0, buttonincrement=0.1, format="{:.0%}",
                                          command=set_widget_scaling,
                                          border_width=0,
                                          fg_color=self.theme_optionmenu.cget("fg_color"),
                                          button_color=self.theme_optionmenu.cget("button_color"),
                                          button_hover_color=self.theme_optionmenu.cget("button_hover_color"),
                                          text_color=self.theme_optionmenu.cget("text_color"))
        self.scaling_spinbox.set(ScalingTracker._widget_scaling)
        self.drawing_label = CTkLabel(self.sidebar_frame, text="Drawing method:", anchor="w")
        self.drawing_optionmenu = CTkOptionMenu(self.sidebar_frame, values=DRAWING_METHODS,
                                                command=self._change_drawing)
        self.drawing_optionmenu.set(BaseShape.preferred_drawing_method)

        py_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        self.versions_label = CTkLabel(self.sidebar_frame,
                                       text=f"Library v{__version__}\nPython v{py_version}\nTcl/Tk v{TclVersion}",
                                       text_color=("gray66", "gray37"),
                                       anchor="w",
                                       justify="left")

        self.sidebar_frame.pack(side=LEFT, fill=Y)
        self.logo_label.pack(side=TOP, fill=X, padx=5, pady=5)
        self.theme_label.pack(side=TOP, fill=X, padx=20, pady=(20, 5))
        self.theme_optionmenu.pack(side=TOP, fill=X, padx=20, pady=(0, 10))
        self.appearance_mode_label.pack(side=TOP, fill=X, padx=20, pady=(20, 5))
        self.appearance_mode_optionemenu.pack(side=TOP, fill=X, padx=20, pady=(0, 10))
        self.scaling_label.pack(side=TOP, fill=X, padx=20, pady=(20, 5))
        self.scaling_spinbox.pack(side=TOP, fill=X, padx=20, pady=(0, 10))
        self.drawing_label.pack(side=TOP, fill=X, padx=20, pady=(20, 5))
        self.drawing_optionmenu.pack(side=TOP, fill=X, padx=20, pady=(0, 10))

        self.versions_label.pack(side=BOTTOM, fill=X, padx=20, pady=(20, 5))

        # create main tabview
        self.main_tabview = CTkTabview(self)

        self.main_tabview.pack(side=LEFT, fill=BOTH, expand=True, padx=5, pady=5)

        # buttons
        self.buttons_frame: CTkFrame = self.main_tabview.add("Buttons")

        self.button_1 = CTkButton(self.buttons_frame)
        self.button_2 = CTkButton(self.buttons_frame, hover=False, text="No Hover")
        self.button_3 = CTkButton(self.buttons_frame, state="disabled", text="disabled")
        self.button_4 = CTkButton(self.buttons_frame, text="Max radius", corner_radius=1000)
        self.button_5 = CTkButton(self.buttons_frame, text="With image", image=self.image)
        self.button_6 = CTkButton(self.buttons_frame, text="", image=self.image, fg_color="transparent", width=0, height=0)

        self.button_1.pack(padx=20, pady=(self.SPACING, 5))
        self.button_2.pack(padx=20, pady=(0, 5))
        self.button_3.pack(padx=20, pady=(0, 5))
        self.button_4.pack(padx=20, pady=(0, 5))
        self.button_5.pack(padx=20, pady=(0, 5))
        self.button_6.pack(padx=20, pady=(0, 5))

        # choices
        self.choices_frame: CTkFrame = self.main_tabview.add("Choices")
        self.topchoices_frame = CTkFrame(self.choices_frame, fg_color="transparent")
        self.combo_frame = CTkFrame(self.topchoices_frame, fg_color="transparent")
        self.combobox_1 = CTkComboBox(self.combo_frame, placeholder_text="Placeholder text",
                                      values=["CTkComboBox", "Value 2", "Value 3", "User can also", "write any text"])
        self.combobox_1.set("CTkComboBox")
        self.combobox_2 = CTkComboBox(self.combo_frame, state="readonly",
                                      values=["readonly", "Value 2", "Value 3", "User can only", "choose a value"])
        self.combobox_2.set("readonly")
        self.combobox_3 = CTkComboBox(self.combo_frame, state="disabled", values=["disabled"], corner_radius=1000)
        self.combobox_3.set("disabled")
        self.combobox_4 = CTkComboBox(self.combo_frame, mode="toggle", separator=", ", width=200,
                                      values=["toggle mode", "Values", "are added", "(if missing)", "or removed", "(if present)", "when selected"])
        self.combobox_4.set("toggle mode")
        self.combobox_5 = CTkComboBox(self.combo_frame, mode="type", width=200,
                                      values=["type mode", "Values", "are used", "as placeholders", "to indicate", "a different usage"])
        self.combobox_6 = CTkComboBox(self.combo_frame, mode="command", command=self._combo_command, width=200,
                                      values=["command mode", "only command is invoked", "UPPERCASE", "lowercase", "Title Case", "Strip whitespaces"])
        self.combobox_6.set("  command mode  ")

        self.optionspin_frame = CTkFrame(self.topchoices_frame, fg_color="transparent")
        self.optionmenu_1 = CTkOptionMenu(self.optionspin_frame, values=["CTkOptionMenu", "Value 2", "Value 3"])
        self.optionmenu_2 = CTkOptionMenu(self.optionspin_frame, values=["disabled", "Value 2", "Value 3"], state="disabled", corner_radius=1000)
        self.optionmenu_3 = CTkOptionMenu(self.optionspin_frame, values=["compound left", "anchor e", "Value 3"], compound="left", anchor="e")
        self.spinbox_1 = CTkSpinBox(self.optionspin_frame, width=120,
                                    values=["CTkSpinBox", "with values", "which are", "shown one", "at a time"])
        self.spinbox_1.set("CTkSpinBox")
        self.spinbox_2 = CTkSpinBox(self.optionspin_frame, from_=1.0, to=60.0, buttonincrement=0.2, scrollincrement=1.0, format="{:.2f} s", justify="center", corner_radius=1000)
        self.spinbox_2.set("From-To")
        self.spinbox_3 = CTkSpinBox(self.optionspin_frame, from_=0x0, to=0xFFFF, buttonincrement=0x1, scrollincrement=0x100, format="0x{:04X}", compound="left")
        self.spinbox_3.set(0x0000)

        self.seg_button_1 = CTkSegmentedButton(self.choices_frame, values=["CTkSegmentedButton", "Value 2", "Value 3"])
        self.seg_button_1.set("CTkSegmentedButton")
        self.seg_button_2 = CTkSegmentedButton(self.choices_frame, values=["vertical", "Max radius", "Value 3"], orientation="vertical", corner_radius=1000, height=35)
        self.seg_button_2.set("vertical")

        self.topchoices_frame.pack()
        self.combo_frame.pack(side="left")
        self.optionspin_frame.pack(side="left")
        self.combobox_1.pack(padx=20, pady=(self.SPACING, 5))
        self.combobox_2.pack(padx=20, pady=(0, 5))
        self.combobox_3.pack(padx=20, pady=(0, 5))
        self.combobox_4.pack(padx=20, pady=(0, 5))
        self.combobox_5.pack(padx=20, pady=(0, 5))
        self.combobox_6.pack(padx=20, pady=(0, 5))
        self.optionmenu_1.pack(padx=20, pady=(self.SPACING, 5))
        self.optionmenu_2.pack(padx=20, pady=(0, 5))
        self.optionmenu_3.pack(padx=20, pady=(0, 5))
        self.spinbox_1.pack(padx=20, pady=(self.SPACING, 5))
        self.spinbox_2.pack(padx=20, pady=(0, 5))
        self.spinbox_3.pack(padx=20, pady=(0, 5))
        self.seg_button_1.pack(padx=20, pady=(self.SPACING, 5))
        self.seg_button_2.pack(padx=20, pady=(0, 5))

        # text
        self.text_frame: CTkFrame = self.main_tabview.add("Text")
        self.label_1 = CTkLabel(self.text_frame, text="CTkLabel", height=1)
        self.label_2 = CTkLabel(self.text_frame, text="with border", border_width=2, corner_radius=6)
        self.label_3 = CTkLabel(self.text_frame, text="with image", image=self.image, compound="right")
        self.entry_1 = CTkEntry(self.text_frame, placeholder_text="CTkEntry")
        self.entry_2 = CTkEntry(self.text_frame, placeholder_text="Password", show="*", justify="center", corner_radius=1000)
        self.textboxes_frame = CTkFrame(self.text_frame, fg_color="transparent")
        self.textbox_1 = CTkTextbox(self.textboxes_frame, width=300)
        self.textbox_1.insert("0.0", "CTkTextbox\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)
        self.textbox_2 = CTkTextbox(self.textboxes_frame, corner_radius=1000, border_width=3, wrap="none")
        self.textbox_2.insert("0.0", "Max radius - no wrap\n\n" + "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20)

        self.label_1.pack(padx=20, pady=(self.SPACING, 5))
        self.label_2.pack(padx=20, pady=(0, 5))
        self.label_3.pack(padx=20, pady=(0, 5))
        self.entry_1.pack(padx=20, pady=(self.SPACING, 5))
        self.entry_2.pack(padx=20, pady=(0, 5))
        self.textboxes_frame.pack(padx=20, pady=(self.SPACING, 5))
        self.textbox_1.pack(side=LEFT, padx=5)
        self.textbox_2.pack(side=LEFT, padx=5)

        # boolean
        self.boolean_frame: CTkFrame = self.main_tabview.add("Boolean")
        self.radio_var = IntVar(value=0)
        self.radio_button_1 = CTkRadioButton(self.boolean_frame, variable=self.radio_var, value=0, width=130)
        self.radio_button_2 = CTkRadioButton(self.boolean_frame, variable=self.radio_var, value=1, text="Fixed settings", hover=False, border_width_checked=8, border_width_unchecked=6, width=130)
        self.radio_button_3 = CTkRadioButton(self.boolean_frame, variable=self.radio_var, value=2, state="disabled", text="disabled", width=130)
        self.radio_button_4 = CTkRadioButton(self.boolean_frame, variable=self.radio_var, value=3, compound="top", text="compound top", internal_spacing=0, width=130)
        self.checkbox_var = BooleanVar(value=True)
        self.checkbox_1 = CTkCheckBox(self.boolean_frame, variable=self.checkbox_var, width=130)
        self.checkbox_2 = CTkCheckBox(self.boolean_frame, state="disabled", text="disabled ON", width=130)
        self.checkbox_2.select()
        self.checkbox_3 = CTkCheckBox(self.boolean_frame, state="disabled", text="disabled OFF", width=130)
        self.switch_var = BooleanVar(value=True)
        self.switch_1 = CTkSwitch(self.boolean_frame, variable=self.switch_var, width=130)
        self.switch_2 = CTkSwitch(self.boolean_frame, border_width=-3, text="negative border", width=130)
        self.switch_3 = CTkSwitch(self.boolean_frame, orientation="vertical", text="vertical", corner_radius=5, button_length=2, border_width=0)
        self.switch_4 = CTkSwitch(self.boolean_frame, text="Fixed settings", hover=False, compound="bottom", corner_radius=0, button_length=5, border_width=5, thickness=30, internal_spacing=0, width=130)

        self.radio_button_1.pack(padx=20, pady=(self.SPACING, 5))
        self.radio_button_2.pack(padx=20, pady=(0, 5))
        self.radio_button_3.pack(padx=20, pady=(0, 5))
        self.radio_button_4.pack(padx=20, pady=(0, 5))
        self.checkbox_1.pack(padx=20, pady=(self.SPACING, 5))
        self.checkbox_2.pack(padx=20, pady=(0, 5))
        self.checkbox_3.pack(padx=20, pady=(0, 5))
        self.switch_1.pack(padx=20, pady=(self.SPACING, 5))
        self.switch_2.pack(padx=20, pady=(0, 5))
        self.switch_3.pack(padx=20, pady=(0, 5))
        self.switch_4.pack(padx=20, pady=(0, 5))

        # bars
        self.bars_frame: CTkFrame = self.main_tabview.add("Bars")
        self.bar_var = DoubleVar(value=0.5)
        self.label_progbar_1 = CTkLabel(self.bars_frame, text="CTkProgressBar - determinate", height=1)
        self.progressbar_1 = CTkProgressBar(self.bars_frame, mode="determinate")
        self.label_progbar_2 = CTkLabel(self.bars_frame, text="CTkProgressBar - indeterminate", height=1)
        self.progressbar_2 = CTkProgressBar(self.bars_frame, mode="indeterminate", progress_speed=0.25)
        self.label_progbar_3 = CTkLabel(self.bars_frame, text="CTkProgressBar - single_run", height=1)
        self.progressbar_3 = CTkProgressBar(self.bars_frame, mode="single_run", show_value=True, thickness=20)
        self.label_slider_1 = CTkLabel(self.bars_frame, text="CTkSlider - with steps", height=1)
        self.slider_1 = CTkSlider(self.bars_frame, number_of_steps=4)
        self.slider_2 = CTkSlider(self.bars_frame, mode="in_range", number_of_steps=9, from_=1, to=10, format="{:.0f} seconds")
        self.label_slider_2 = CTkLabel(self.bars_frame, text="CTkSlider - continuous", height=1)
        self.slider_3 = CTkSlider(self.bars_frame, from_=10, to=100)
        self.slider_4 = CTkSlider(self.bars_frame, mode="out_range", from_=100, to=-100, corner_radius=0, button_length=4, border_width=4)
        self.label_scrollbar_1 = CTkLabel(self.bars_frame, text="CTkScrollbar", height=1)
        self.scrollbar_1 = CTkScrollbar(self.bars_frame, orientation="horizontal")
        self.scrollbar_1.set(0, 0.3)

        self.label_vertical = CTkLabel(self.bars_frame, text="vertical", height=1)
        self.frame_vertical = CTkFrame(self.bars_frame, fg_color="transparent")
        self.progressbar_4 = CTkProgressBar(self.frame_vertical, orientation="vertical", variable=self.bar_var, corner_radius=3, thickness=40, show_value=True)
        self.slider_5 = CTkSlider(self.frame_vertical, orientation="vertical", variable1=self.bar_var, corner_radius=2, button_length=4, show_value=False)
        self.slider_6 = CTkSlider(self.frame_vertical, orientation="vertical", mode="any_range", format="{:.2%}", tooltip={"delay": 0})
        self.scrollbar_2 = CTkScrollbar(self.frame_vertical, orientation="vertical", corner_radius=2, border_width=0, thickness=8)
        self.scrollbar_2.set(0, 0.3)

        self.progressbar_1.start()
        self.progressbar_2.start()
        self.progressbar_3.bind("<Button-1>", self._start_progress_single_run)
        self.progressbar_3.set(text="Click me")
        self.slider_1.set(0.5)
        self.slider_2.set(2, 9)
        self.slider_3.set(55)
        self.slider_4.set(50, -50)
        self.slider_6.set(0.3, 0.7)

        self.label_progbar_1.pack(padx=20, pady=(self.SPACING, 5))
        self.progressbar_1.pack(padx=20, pady=(0, 5))
        self.label_progbar_2.pack(padx=20, pady=(0, 5))
        self.progressbar_2.pack(padx=20, pady=(0, 5))
        self.label_progbar_3.pack(padx=20, pady=(0, 5))
        self.progressbar_3.pack(padx=20, pady=(0, 5))
        self.label_slider_1.pack(padx=20, pady=(self.SPACING, 5))
        self.slider_1.pack(padx=20, pady=(0, 5))
        self.slider_2.pack(padx=20, pady=(0, 5))
        self.label_slider_2.pack(padx=20, pady=(0, 5))
        self.slider_3.pack(padx=20, pady=(0, 5))
        self.slider_4.pack(padx=20, pady=(0, 5))
        self.label_scrollbar_1.pack(padx=20, pady=(self.SPACING, 5))
        self.scrollbar_1.pack(padx=20, pady=(0, 5))

        self.label_vertical.pack(padx=20, pady=(self.SPACING, 5))
        self.frame_vertical.pack(padx=20, pady=(0, 5))
        self.progressbar_4.pack(side=LEFT, padx=20)
        self.slider_5.pack(side=LEFT, padx=20)
        self.slider_6.pack(side=LEFT, padx=20)
        self.scrollbar_2.pack(side=LEFT, padx=20)

        # frames
        self.frames_frame: CTkFrame = self.main_tabview.add("Frames")
        self.scrollable_frames = CTkFrame(self.frames_frame, fg_color="transparent")
        self.scrollable_frame_1 = CTkScrollableFrame(self.scrollable_frames, label={"text": "CTkScrollableFrame"})
        self.scrollable_frame_2 = CTkScrollableFrame(self.scrollable_frames, orientation=BOTH, corner_radius=1000)
        self.tabview = CTkTabview(self.frames_frame)
        tab1 = self.tabview.add("CTkTabview")
        tab2 = self.tabview.add("Tab 2")
        tab3 = self.tabview.add("Tab 3")
        CTkButton(tab1, text="Widget on 1st Tab").pack(pady = 5)
        CTkCheckBox(tab2, text="Widget on 2nd Tab").pack(pady = 5)
        CTkSwitch(tab3, text="Widget on 3rd Tab").pack(pady = 5)
        self.floating_frame = CTkFloatingFrame(self, corner_radius=20, border_width=5)
        label = CTkLabel(self.floating_frame, text="A frame detached from any window,\nalways on top of everything,\nthat can contain anything.", width=200, height=200)
        label.pack(fill=BOTH, expand=True, padx=10, pady=10)
        self.open_floating_frame = CTkButton(self.frames_frame, text="Open CTkFloatingFrame", command=lambda: self.floating_frame.open(1000, 500))
        self.close_floating_frame = CTkButton(self.frames_frame, text="Close", command=self.floating_frame.close)

        for i in range(100):
            switch = CTkSwitch(self.scrollable_frame_1, text=f"CTkSwitch {i+1}")
            switch.pack(padx=20, pady=5)

        for r in range(10):
            frame = CTkFrame(self.scrollable_frame_2, width=0, height=0, corner_radius=0, fg_color="transparent")
            frame.pack(side=TOP)
            for c in range(10):
                checkbox = CTkCheckBox(frame, text="", width=0, corner_radius=0, border_width=1)
                checkbox.pack(side=LEFT)
                if (r + c) % 2 == 0:
                    checkbox.select()

        self.scrollable_frames.pack(padx=20, pady=(self.SPACING, 5))
        self.scrollable_frame_1.pack(side=LEFT, padx=(0, 5))
        self.scrollable_frame_2.pack(side=LEFT, padx=(5, 0))
        self.tabview.pack(padx=20, pady=(self.SPACING, 5))
        self.open_floating_frame.pack(padx=20, pady=(self.SPACING, 5))
        self.close_floating_frame.pack(padx=20, pady=(0, 5))

        # windows
        self.windows_frame: CTkFrame = self.main_tabview.add("Windows")
        self.open_toplevel = CTkButton(self.windows_frame, text="Open CTkToplevel", command=self._open_ctktoplevel)
        self.open_dialog_1 = CTkButton(self.windows_frame, text="Open CTkInputDialog", command=self._open_input_dialog_1)
        self.open_dialog_2 = CTkButton(self.windows_frame, text="with values", command=self._open_input_dialog_2)
        self.button_withtt_1 = CTkButton(self.windows_frame, text="CTkToolTip")
        self.tooltip_1 = CTkToolTip(self.button_withtt_1, label={"wraplength": 200},
                                    title="CTkToolTip",
                                    text="Little window that opens when the user hovers over the linked widget, which usually contains an explanation of the object.")
        self.button_withtt_2 = CTkButton(self.windows_frame, text="with any widgets")
        self.tooltip_2 = CTkToolTip(self.button_withtt_2, mode="live_mouse", anchor="s", fg_color="transparent",
                                    close_on_interaction=False,
                                    command=self._update_progressbar_ontt)
        self.progressbar_ontt = CTkProgressBar(self.tooltip_2, orientation="horizontal", thickness=30, show_value=True)
        self.progressbar_ontt.pack()

        self.open_toplevel.pack(padx=20, pady=(self.SPACING, 5))
        self.open_dialog_1.pack(padx=20, pady=(self.SPACING, 5))
        self.open_dialog_2.pack(padx=20, pady=(0, 5))
        self.button_withtt_1.pack(padx=20, pady=(self.SPACING, 5))
        self.button_withtt_2.pack(padx=20, pady=(0, 5))

    def _combo_command(self, value: str) -> None:
        if value == "UPPERCASE":
            self.combobox_6.set(self.combobox_6.get().upper())
        elif value == "lowercase":
            self.combobox_6.set(self.combobox_6.get().lower())
        elif value == "Title Case":
            self.combobox_6.set(self.combobox_6.get().title())
        elif value == "Strip whitespaces":
            self.combobox_6.set(self.combobox_6.get().strip())

    def _start_progress_single_run(self, _: Event) -> None:
        self.progressbar_3.set(0.0)
        self.progressbar_3.start()

    def _open_ctktoplevel(self) -> None:
        toplevel = CTkToplevel(self, title="CTkToplevel")
        toplevel.geometry(f"{500}x{250}")
        toplevel.resizable(True, True)
        label = CTkLabel(toplevel, text="A new window that can contains anything")
        label.pack(padx=5, pady=5)
        self.after(50, toplevel.lift)

    def _open_input_dialog_1(self) -> None:
        dialog = CTkInputDialog(title="CTkInputDialog",
                                text="Description of requested input",
                                default_value="default value")
        dialog.get_input()

    def _open_input_dialog_2(self) -> None:
        dialog = CTkInputDialog(title="CTkInputDialog with values",
                                text="You can choose just one of the valid inputs",
                                values=["value 1", "value 2", "value 3", "value 4"])
        dialog.get_input()

    def _update_progressbar_ontt(self) -> str:
        if self.tooltip_2.is_open():
            if self.progressbar_ontt.get() < 1.0:
                self.progressbar_ontt.step(0.005)
            else:
                self.tooltip_2.close()
                return "break"
        else:
            self.progressbar_ontt.set(0.0, "Move the mouse")
        return ""

    def _change_theme(self, new_theme: str) -> None:
        set_default_color_theme(new_theme)
        self.new_instance_requested = True
        self.destroy()

    def _change_drawing(self, new_drawing_method: str) -> None:
        BaseShape.preferred_drawing_method = new_drawing_method
        self.new_instance_requested = True
        self.destroy()
