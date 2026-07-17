import os
import sys
from typing import Any
from functools import partial
from tkinter import TclVersion

from . import __version__
from . import set_appearance_mode
from . import get_appearance_mode
from . import set_default_color_theme
from . import set_widget_scaling
from . import get_widget_scaling
from . import ThemeManager
from . import ColorType
from . import BaseShape
from . import DRAWING_METHODS
from . import BooleanVar, DoubleVar, IntVar, Event
from . import CTk
from . import CTkToplevel
from . import CTkInputDialog
from . import CTkFont

from . import CTkButton
from . import CTkCheckBox
from . import CTkComboBox
from . import CTkEntry
from . import CTkFloatingFrame
from . import CTkFrame
from . import CTkGridView
from . import CTkLabel
from . import CTkListBox
from . import CTkOptionMenu
from . import CTkProgressBar
from . import CTkRadioButton
from . import CTkScrollbar
from . import CTkSectionView
from . import CTkSegmentedButton
from . import CTkSlider
from . import CTkSpinBox
from . import CTkSwitch
from . import CTkSymbolBox
from . import CTkTabview
from . import CTkTextbox
from . import CTkToggleButton
from . import CTkToolTip
from . import CTkScrollableFrame


def run_showroom() -> None:
    set_appearance_mode("light")
    set_default_color_theme("blue")

    new_instance: bool = True
    while new_instance:
        app = _Showroom()
        app.mainloop()
        new_instance = app.new_instance_requested


class _Showroom(CTk):

    def __init__(self) -> None:
        super().__init__()

        # configure window
        self.title("CustomTkinter Showroom")
        self.geometry("+200+50")

        self.new_instance_requested: bool = False

        # create left/right frames
        self.sidebar_frame = CTkFrame(self, width=140, corner_radius=0)
        self.main_frame = CTkFrame(self, corner_radius=0, fg_color="transparent")

        self.sidebar_frame.pack(side="left", fill="y")
        self.main_frame.pack(side="left", fill="both", expand=True, padx=5, pady=5)

        # fill left frame
        self.logo_label = CTkLabel(self.sidebar_frame, text="CustomTkinter", font=CTkFont(size=20, weight="bold"))
        self.theme_label = CTkLabel(self.sidebar_frame, text="Theme:", anchor="w")
        self.theme_optionmenu = CTkOptionMenu(self.sidebar_frame, values=ThemeManager._built_in_themes,
                                              command=self._change_theme)
        self.theme_optionmenu.set(ThemeManager._last_loaded_theme)
        self.appearance_mode_label = CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_optionmenu = CTkOptionMenu(self.sidebar_frame, values=["light", "dark", "system"],
                                                        command=set_appearance_mode)
        self.appearance_mode_optionmenu.set(get_appearance_mode())
        self.scaling_label = CTkLabel(self.sidebar_frame, text="UI Scaling:", anchor="w")
        self.scaling_spinbox = CTkSpinBox(self.sidebar_frame, from_=0.5, to=2.0, buttonincrement=0.1, format="{:.0%}",
                                          command=set_widget_scaling,
                                          border_width=0,
                                          fg_color=self.theme_optionmenu.cget("fg_color"),
                                          button_color=self.theme_optionmenu.cget("button_color"),
                                          button_hover_color=self.theme_optionmenu.cget("button_hover_color"),
                                          text_color=self.theme_optionmenu.cget("text_color"))
        self.scaling_spinbox.set(get_widget_scaling())
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

        self.logo_label.pack(side="top", fill="x", padx=5, pady=5)
        self.theme_label.pack(side="top", fill="x", padx=20, pady=(20, 5))
        self.theme_optionmenu.pack(side="top", fill="x", padx=20, pady=(0, 10))
        self.appearance_mode_label.pack(side="top", fill="x", padx=20, pady=(20, 5))
        self.appearance_mode_optionmenu.pack(side="top", fill="x", padx=20, pady=(0, 10))
        self.scaling_label.pack(side="top", fill="x", padx=20, pady=(20, 5))
        self.scaling_spinbox.pack(side="top", fill="x", padx=20, pady=(0, 10))
        self.drawing_label.pack(side="top", fill="x", padx=20, pady=(20, 5))
        self.drawing_optionmenu.pack(side="top", fill="x", padx=20, pady=(0, 10))

        self.versions_label.pack(side="bottom", fill="x", padx=20, pady=(20, 5))

        # create commands frame
        self.commands_frame = CTkFrame(self.main_frame, corner_radius=0, fg_color="transparent")
        self.toggle_order = CTkToggleButton(self.commands_frame,
                                            text_unchecked="Alphabetical order",
                                            text_checked="Logical order",
                                            fg_color_unchecked="transparent",
                                            fg_color_checked="transparent",
                                            border_width=0,
                                            command=self._update_sections)
        self.entry_filter = CTkEntry(self.commands_frame,
                                     placeholder_text="Filter by Name",
                                     justify="center",
                                     width=180)
        self.entry_filter.bind("<KeyRelease>", self._update_sections)

        self.commands_frame.pack(side="top", fill="x")
        self.toggle_order.pack(side="left")
        self.entry_filter.pack(side="right")

        # create main frame and sectionview
        self.scrollframe = CTkScrollableFrame(self.main_frame, fg_color="transparent", corner_radius=0, width=500)
        self.sectionview = CTkSectionView(self.scrollframe,
                                          max_open=2,
                                          border_spacing=10,
                                          symbol={"font": {"size": 16},
                                                  "anchor": "center",
                                                  "corner_radius": 6,
                                                  "box_width": 20,
                                                  "box_height": 20})

        self.scrollframe.pack(side="top", fill="both", expand=True, pady=(5, 0))
        self.sectionview.pack(side="top", fill="both", expand=True)

        # setup common info that the frames can use
        try:
            lib_directory = os.path.dirname(os.path.abspath(__file__))
            ThemeManager.add_key("logo",
                                 light_image=os.path.join(lib_directory, "assets", "icons", "CustomTkinter_icon_Windows.ico"),
                                 height=20)
            ThemeManager.add_key("vars",
                                 bar=DoubleVar(value=0.5),
                                 checkswitch=BooleanVar(value=True))
        except KeyError:
            pass

        # categories
        self.categories: dict[str, ColorType] = {
            "Buttons"      : "#1F77B4",
            "Choices"      : "#FF7F0E",
            "Text"         : "#2CA02C",
            "Boolean"      : "#D62728",
            "Bars"         : "#9467BD",
            "Frames"       : "#8C564B",
            "Windows"      : "#E377C2",
            "Miscellaneous": "#BCBD22",
            ""             : "#17BECF"
        }

        self.tt_categories = CTkToolTip(self.toggle_order, delay=0, border_width=2)
        for n, (name, color) in enumerate(self.categories.items()):
            if name:
                widget = CTkSymbolBox(self.tt_categories,
                                      text=name,
                                      values=["rect"],
                                      fg_color=color,
                                      symbol_color=color)
                widget.grid(row=n, sticky="w", padx=5, pady=(5 if n == 0 else 0, 5))

        # widgets
        self.widgets: list[tuple[str, type[CTkFrame], str]] = [
            ("Button"         , _CTkButtonsFrame         , "Buttons"      ),
            ("ToggleButton"   , _CTkToggleButtonsFrame   , "Buttons"      ),
            ("ComboBox"       , _CTkComboBoxesFrame      , "Choices"      ),
            ("OptionMenu"     , _CTkOptionMenusFrame     , "Choices"      ),
            ("SpinBox"        , _CTkSpinBoxesFrame       , "Choices"      ),
            ("SymbolBox"      , _CTkSymbolBoxesFrame     , "Choices"      ),
            ("SegmentedButton", _CTkSegmentedButtonsFrame, "Choices"      ),
            ("ListBox"        , _CTkListBoxesFrame       , "Choices"      ),
            ("Label"          , _CTkLabelsFrame          , "Text"         ),
            ("Entry"          , _CTkEntriesFrame         , "Text"         ),
            ("Textbox"        , _CTkTextboxesFrame       , "Text"         ),
            ("RadioButton"    , _CTkRadioButtonsFrame    , "Boolean"      ),
            ("CheckBox"       , _CTkCheckBoxesFrame      , "Boolean"      ),
            ("Switch"         , _CTkSwitchesFrame        , "Boolean"      ),
            ("ProgressBar"    , _CTkProgressBarsFrame    , "Bars"         ),
            ("Slider"         , _CTkSlidersFrame         , "Bars"         ),
            ("Scrollbar"      , _CTkScrollbarsFrame      , "Bars"         ),
            ("Frame"          , _CTkFramesFrame          , "Frames"       ),
            ("ScrollableFrame", _CTkScrollableFramesFrame, "Frames"       ),
            ("Tabview"        , _CTkTabviewsFrame        , "Frames"       ),
            ("GridView"       , _CTkGridViewsFrame       , "Frames"       ),
            ("SectionView"    , _CTkSectionViewsFrame    , "Frames"       ),
            ("FloatingFrame"  , _CTkFloatingFramesFrame  , "Frames"       ),
            ("Toplevel"       , _CTkToplevelsFrame       , "Windows"      ),
            ("InputDialog"    , _CTkInputDialogsFrame    , "Windows"      ),
            ("ToolTip"        , _CTkToolTipsFrame        , "Miscellaneous"),
        ]

        for name, frame_class, category in self.widgets:
            frame = frame_class(self.sectionview.add(name),
                                fg_color="transparent",
                                corner_radius=0)
            frame.pack(side="top", fill="both", expand=True, padx=5)
            self.sectionview.symbol(name).configure(fg_color=self.categories[category])

    def _change_theme(self, new_theme: str) -> None:
        set_default_color_theme(new_theme)
        self.new_instance_requested = True
        self.destroy()

    def _change_drawing(self, new_drawing_method: str) -> None:
        BaseShape.preferred_drawing_method = new_drawing_method
        self.new_instance_requested = True
        self.destroy()

    def _update_sections(self, *_: Any) -> None:
        name_filter = self.entry_filter.get().lower()
        visible_sections = [widget[0] for widget in self.widgets if name_filter in widget[0].lower()]
        if self.toggle_order.get():
            visible_sections.sort()
        self.sectionview.set(visible_sections, [])



class _CTkButtonsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        def fx() -> None:
            #so that the cursor is set properly
            pass

        self.button_1 = CTkButton(self, command=fx)
        self.button_2 = CTkButton(self, text="No Hover", hover=False, command=fx)
        self.button_3 = CTkButton(self, text="disabled", state="disabled", command=fx)
        self.button_4 = CTkButton(self, text="Max radius", corner_radius=1000, command=fx)
        self.button_5 = CTkButton(self, text="With image", image="logo", command=fx)
        self.button_6 = CTkButton(self, text="", image="logo", fg_color="transparent", width=0, height=0, command=fx)

        self.button_1.pack(pady=5)
        self.button_2.pack(pady=5)
        self.button_3.pack(pady=5)
        self.button_4.pack(pady=5)
        self.button_5.pack(pady=5)
        self.button_6.pack(pady=5)


class _CTkToggleButtonsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.togglebutton_1 = CTkToggleButton(self)
        self.togglebutton_2 = CTkToggleButton(self, text_unchecked="text unchecked", text_checked="text checked")
        self.togglebutton_3 = CTkToggleButton(self, text="With image", image="logo", compound="right")
        self.togglebutton_4 = CTkToggleButton(self, image_unchecked="logo", text_checked="text but no image", height=35)
        self.togglebutton_5 = CTkToggleButton(self, image="logo", text="", fg_color_unchecked="transparent",
                                              corner_radius=1000, border_width=0, width=0, height=0)

        self.togglebutton_2.select()

        self.togglebutton_1.pack(pady=5)
        self.togglebutton_2.pack(pady=5)
        self.togglebutton_3.pack(pady=5)
        self.togglebutton_4.pack(pady=5)
        self.togglebutton_5.pack(pady=5)


class _CTkComboBoxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.combobox_1 = CTkComboBox(self,
                                      placeholder_text="Placeholder text",
                                      values=["CTkComboBox", "Value 2", "Value 3", "User can also", "write any text"])
        self.combobox_2 = CTkComboBox(self,
                                      state="readonly",
                                      values=["readonly", "Value 2", "Value 3", "User can only", "choose a value"])
        self.combobox_3 = CTkComboBox(self,
                                      state="disabled",
                                      values=["disabled"],
                                      corner_radius=1000)
        self.combobox_4 = CTkComboBox(self,
                                      mode="toggle",
                                      separator=", ",
                                      values=["toggle mode", "Values", "are added", "(if missing)", "or removed", "(if present)", "when selected"],
                                      width=200)
        self.combobox_5 = CTkComboBox(self,
                                      mode="type",
                                      values=["type mode", "Values", "are used", "as placeholders", "to indicate", "a different usage"],
                                      width=200)
        self.combobox_6 = CTkComboBox(self,
                                      mode="command",
                                      command=self._combo_command,
                                      values=["command mode", "only 'command' is invoked", "UPPERCASE", "lowercase", "Title Case", "Strip whitespaces"],
                                      width=200)

        self.combobox_1.set("CTkComboBox")
        self.combobox_2.set("readonly")
        self.combobox_3.set("disabled")
        self.combobox_4.set("toggle mode")
        self._combo_command("")

        self.combobox_1.pack(pady=5)
        self.combobox_2.pack(pady=5)
        self.combobox_3.pack(pady=5)
        self.combobox_4.pack(pady=5)
        self.combobox_5.pack(pady=5)
        self.combobox_6.pack(pady=5)

    def _combo_command(self, value: str) -> None:
        if value == "UPPERCASE":
            self.combobox_6.set(self.combobox_6.get().upper())
        elif value == "lowercase":
            self.combobox_6.set(self.combobox_6.get().lower())
        elif value == "Title Case":
            self.combobox_6.set(self.combobox_6.get().title())
        elif value == "Strip whitespaces":
            self.combobox_6.set(self.combobox_6.get().strip())
        else:
            self.combobox_6.set("  command mode  ")


class _CTkOptionMenusFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.optionmenu_1 = CTkOptionMenu(self,
                                          values=["CTkOptionMenu", "Value 2", "Value 3"])
        self.optionmenu_2 = CTkOptionMenu(self,
                                          state="disabled",
                                          corner_radius=1000,
                                          values=["disabled", "Value 2", "Value 3"])
        self.optionmenu_3 = CTkOptionMenu(self,
                                          compound="left",
                                          anchor="e",
                                          values=["compound left", "anchor e", "Value 3"])

        self.optionmenu_1.pack(pady=5)
        self.optionmenu_2.pack(pady=5)
        self.optionmenu_3.pack(pady=5)


class _CTkSpinBoxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.spinbox_1 = CTkSpinBox(self,
                                    values=["CTkSpinBox", "with values", "which are", "shown one", "at a time"],
                                    width=120)
        self.spinbox_2 = CTkSpinBox(self,
                                    from_=1.0,
                                    to=60.0,
                                    buttonincrement=0.2,
                                    scrollincrement=1.0,
                                    format="{:.2f} s",
                                    justify="center",
                                    corner_radius=1000)
        self.spinbox_3 = CTkSpinBox(self,
                                    from_=0x0,
                                    to=0xFFFF,
                                    buttonincrement=0x1,
                                    scrollincrement=0x100,
                                    format="0x{:04X}",
                                    compound="left")

        self.spinbox_1.set("CTkSpinBox")
        self.spinbox_2.set("From-To")
        self.spinbox_3.set(0x0000)

        self.spinbox_1.pack(pady=5)
        self.spinbox_2.pack(pady=5)
        self.spinbox_3.pack(pady=5)


class _CTkSymbolBoxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.symbolbox_1 = CTkSymbolBox(self, values=["", "+", "x", "|", "/", "-", "\\", "^", ">", "v", "<", "check", "circle", "rect", "play", "star"], width=150)
        self.symbolbox_2 = CTkSymbolBox(self, text="Tri-state CheckBox", values=["", "check", "-"], width=150)
        self.symbolbox_3 = CTkSymbolBox(self, text="Test result", values=["", "check", "x"], fg_color=["transparent", "green", "red"], width=150)
        self.symbolbox_4 = CTkSymbolBox(self, text="Direction", values=["^", ">", "v", "<"], width=150)
        self.symbolbox_5 = CTkSymbolBox(self, text="Operation", values=["+", "-", "x", "/"], width=150)
        self.symbolbox_6 = CTkSymbolBox(self, text="Button-like", values=["star"], corner_radius=1000, width=150)
        self.symbolbox_7 = CTkSymbolBox(self, text="Audio trace", values=["circle", "rect", "play", "rect"], fg_color=["red", "red", "green", "green"], width=150)

        self.symbolbox_3.set("check")

        self.symbolbox_1.pack(pady=5)
        self.symbolbox_2.pack(pady=5)
        self.symbolbox_3.pack(pady=5)
        self.symbolbox_4.pack(pady=5)
        self.symbolbox_5.pack(pady=5)
        self.symbolbox_6.pack(pady=5)
        self.symbolbox_7.pack(pady=5)


class _CTkSegmentedButtonsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.seg_button_1 = CTkSegmentedButton(self, values=["CTkSegmentedButton", "Value 2", "Value 3"])
        self.seg_button_2 = CTkSegmentedButton(self, values=["Buttons are", "spread to", "respect the", "provided width"], box_width=100)
        self.seg_button_3 = CTkSegmentedButton(self, values=["vertical", "Max radius", "Value 3", "Value 4"], orientation="vertical", corner_radius=1000, height=35)

        self.seg_button_1.set("CTkSegmentedButton")
        self.seg_button_3.set("vertical")

        self.seg_button_1.pack(pady=5)
        self.seg_button_2.pack(pady=5)
        self.seg_button_3.pack(pady=5)


class _CTkListBoxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        values = [f"Value {x+1}" for x in range(20)]
        self.listbox_1 = CTkListBox(self,
                                    width=150,
                                    values=["CTkListBox", "vertical", "1 column", "1 selection"] + values)
        self.listbox_2 = CTkListBox(self,
                                    width=300,
                                    height=100,
                                    values=["horizontal", "3 rows", "multi selection"] + values,
                                    max_selected=0,
                                    orientation="horizontal",
                                    rows=3)
        self.listbox_3 = CTkListBox(self,
                                    width=300,
                                    height=150,
                                    corner_radius=1000,
                                    values=["both", "min 2 selected", "max 5 selected"] + values,
                                    min_selected=2,
                                    max_selected=5,
                                    orientation="both",
                                    columns=4,
                                    label={"text": "Title that spans the whole width"})

        self.listbox_1.pack(pady=5)
        self.listbox_2.pack(pady=5)
        self.listbox_3.pack(pady=5)


class _CTkLabelsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.label_1 = CTkLabel(self, text="CTkLabel", height=1)
        self.label_2 = CTkLabel(self, text="with border", border_width=2, corner_radius=6)
        self.label_3 = CTkLabel(self, text="with image", image="logo", compound="right")
        self.label_4 = CTkLabel(self, text="Text\nover\nmultiple lines", justify="right")

        self.label_1.pack(pady=5)
        self.label_2.pack(pady=5)
        self.label_3.pack(pady=5)
        self.label_4.pack(pady=5)


class _CTkEntriesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.entry_1 = CTkEntry(self)
        self.entry_2 = CTkEntry(self, placeholder_text="Placeholder text", width=200)
        self.entry_3 = CTkEntry(self, placeholder_text="Password", show="*", justify="center", corner_radius=1000)

        self.entry_1.set("CTkEntry")

        self.entry_1.pack(pady=5)
        self.entry_2.pack(pady=5)
        self.entry_3.pack(pady=5)


class _CTkTextboxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.textbox_1 = CTkTextbox(self, width=300)
        self.textbox_2 = CTkTextbox(self, corner_radius=1000, border_width=3, wrap="none")

        long_text = "Lorem ipsum dolor sit amet, consetetur sadipscing elitr, sed diam nonumy eirmod tempor invidunt ut labore et dolore magna aliquyam erat, sed diam voluptua.\n\n" * 20
        self.textbox_1.insert("0.0", "CTkTextbox\n\n" + long_text)
        self.textbox_2.insert("0.0", "Max radius - with border - no wrap\n\n" + long_text)

        self.textbox_1.pack(pady=5)
        self.textbox_2.pack(pady=5)


class _CTkRadioButtonsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.radio_var = IntVar(value=0)
        self.radio_button_1 = CTkRadioButton(self, variable=self.radio_var, value=0, width=130)
        self.radio_button_2 = CTkRadioButton(self, variable=self.radio_var, value=1, text="Fixed settings", hover=False, border_width_checked=8, border_width_unchecked=6, width=130)
        self.radio_button_3 = CTkRadioButton(self, variable=self.radio_var, value=2, text="disabled", state="disabled", width=130)
        self.radio_button_4 = CTkRadioButton(self, variable=self.radio_var, value=3, text="compound top", compound="top", internal_spacing=0, width=130)

        self.radio_button_1.pack(pady=5)
        self.radio_button_2.pack(pady=5)
        self.radio_button_3.pack(pady=5)
        self.radio_button_4.pack(pady=5)


class _CTkCheckBoxesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.var = ThemeManager.get_info("vars").get("checkswitch", None)

        self.checkbox_1 = CTkCheckBox(self, variable=self.var, width=130)
        self.checkbox_2 = CTkCheckBox(self, text="disabled ON", state="disabled", width=130)
        self.checkbox_3 = CTkCheckBox(self, text="disabled OFF", state="disabled", width=130)
        self.checkbox_4 = CTkCheckBox(self, text="compound right", compound="right", width=130)

        self.checkbox_2.select()

        self.checkbox_1.pack(pady=5)
        self.checkbox_2.pack(pady=5)
        self.checkbox_3.pack(pady=5)
        self.checkbox_4.pack(pady=5)


class _CTkSwitchesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.var = ThemeManager.get_info("vars").get("checkswitch", None)

        self.switch_1 = CTkSwitch(self, variable=self.var, width=130)
        self.switch_2 = CTkSwitch(self, text="negative border", border_width=-3, width=130)
        self.switch_3 = CTkSwitch(self, text="vertical", orientation="vertical", corner_radius=5, button_length=2, border_width=0)
        self.switch_4 = CTkSwitch(self, text="Fixed settings", hover=False, compound="bottom", corner_radius=0, button_length=5, border_width=5, thickness=30, internal_spacing=0, width=130)
        self.frame = CTkFrame(self, fg_color="transparent", width=0, height=0)
        self.switch_5_1 = CTkSwitch(self.frame, text="Circuit breaker-like", hover=False, compound="right", orientation="vertical", corner_radius=0, button_length=6, border_width=6, thickness=20)
        self.switch_5_2 = CTkSwitch(self.frame, text="", hover=False, compound="left", orientation="vertical", corner_radius=0, button_length=6, border_width=6, thickness=20, width=0)

        self.switch_5_1.configure(command=self.switch_5_2.set)
        self.switch_5_2.configure(command=self.switch_5_1.set)

        self.switch_1.pack(pady=5)
        self.switch_2.pack(pady=5)
        self.switch_3.pack(pady=5)
        self.switch_4.pack(pady=5)
        self.frame.pack(pady=5)
        self.switch_5_1.pack(side="left")
        self.switch_5_2.pack(side="left")


class _CTkProgressBarsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.outer_frame = CTkFrame(self, fg_color="transparent")
        self.left_frame = CTkFrame(self.outer_frame, fg_color="transparent")

        self.var = ThemeManager.get_info("vars").get("bar", None)

        self.label_1 = CTkLabel(self.left_frame, text="determinate mode", height=1)
        self.progressbar_1 = CTkProgressBar(self.left_frame, mode="determinate")
        self.label_2 = CTkLabel(self.left_frame, text="indeterminate mode", height=1)
        self.progressbar_2 = CTkProgressBar(self.left_frame, mode="indeterminate", progress_speed=0.25)
        self.label_3 = CTkLabel(self.left_frame, text="single_run mode", height=1)
        self.progressbar_3 = CTkProgressBar(self.left_frame, mode="single_run", show_value=True, thickness=20)
        self.progressbar_4 = CTkProgressBar(self.outer_frame, orientation="vertical", variable=self.var, corner_radius=3, border_width=3, thickness=45, show_value=True)

        self.progressbar_1.start()
        self.progressbar_2.start()
        self.progressbar_3.bind("<Button-1>", self._start_single_run)
        self.progressbar_3.set(text="Click me")

        self.outer_frame.pack()
        self.left_frame.pack(side="left")
        self.label_1.pack(pady=5)
        self.progressbar_1.pack(pady=5)
        self.label_2.pack(pady=5)
        self.progressbar_2.pack(pady=5)
        self.label_3.pack(pady=5)
        self.progressbar_3.pack(pady=5)
        self.progressbar_4.pack(side="left", padx=(20, 0), pady=5)

    def _start_single_run(self, _: Event) -> None:
        self.progressbar_3.set(0.0)
        self.progressbar_3.start()


class _CTkSlidersFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.outer_frame = CTkFrame(self, fg_color="transparent")
        self.left_frame = CTkFrame(self.outer_frame, fg_color="transparent")

        self.var = ThemeManager.get_info("vars").get("bar", None)

        self.label_1 = CTkLabel(self.left_frame, text="with steps", height=1)
        self.slider_1 = CTkSlider(self.left_frame, number_of_steps=4)
        self.slider_2 = CTkSlider(self.left_frame, mode="in_range", number_of_steps=9, from_=1, to=10, format="{:.0f} seconds")
        self.label_2 = CTkLabel(self.left_frame, text="continuous", height=1)
        self.slider_3 = CTkSlider(self.left_frame, from_=10, to=100)
        self.slider_4 = CTkSlider(self.left_frame, mode="out_range", from_=100, to=-100, corner_radius=0, button_length=4, border_width=4)
        self.slider_5 = CTkSlider(self.outer_frame, orientation="vertical", variable1=self.var, corner_radius=2, button_length=4, show_value=False)
        self.slider_6 = CTkSlider(self.outer_frame, orientation="vertical", mode="any_range", format="{:.2%}", tooltip={"delay": 0})

        self.slider_1.set(0.5)
        self.slider_2.set(2, 9)
        self.slider_3.set(55)
        self.slider_4.set(50, -50)
        self.slider_6.set(0.3, 0.7)

        self.outer_frame.pack()
        self.left_frame.pack(side="left")
        self.label_1.pack(pady=5)
        self.slider_1.pack(pady=5)
        self.slider_2.pack(pady=5)
        self.label_2.pack(pady=5)
        self.slider_3.pack(pady=5)
        self.slider_4.pack(pady=5)
        self.slider_5.pack(side="left", padx=(20, 0), pady=5)
        self.slider_6.pack(side="left", padx=(20, 0), pady=5)


class _CTkScrollbarsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.scrollbar_1 = CTkScrollbar(self, orientation="horizontal")
        self.scrollbar_2 = CTkScrollbar(self, orientation="vertical", corner_radius=2, border_width=0, thickness=10, length=100, scrollincrement=2)

        self.scrollbar_1.set(0, 0.3)
        self.scrollbar_2.set(0, 0.5)

        self.scrollbar_1.pack(side="bottom", fill="x", expand=True)
        self.scrollbar_2.pack(side="right", pady=(5, 0))


class _CTkFramesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.frame_1 = CTkFrame(self)
        self.frame_2 = CTkFrame(self, width=400, height=50, border_width=1, corner_radius=0)
        self.frame_3 = CTkFrame(self, width=100, height=100, border_width=10, corner_radius=1000)

        frame = self.frame_1
        for n in range(4):
            CTkLabel(frame, text="Inner-" * n + "CTkFrame").pack(padx=5, pady=10)
            if n < 3:
                frame = CTkFrame(frame)
                frame.pack(padx=10, pady=(0, 10))

        self.frame_1.pack(pady=5)
        self.frame_2.pack(pady=5)
        self.frame_3.pack(pady=5)


class _CTkScrollableFramesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.scrollable_frame_1 = CTkScrollableFrame(self, label={"text": "CTkScrollableFrame"})
        self.scrollable_frame_2 = CTkScrollableFrame(self, orientation="both", corner_radius=1000)

        for i in range(100):
            switch = CTkSwitch(self.scrollable_frame_1, text=f"CTkSwitch {i+1}")
            switch.pack(padx=20, pady=5)

        for r in range(10):
            frame = CTkFrame(self.scrollable_frame_2, width=0, height=0, corner_radius=0, fg_color="transparent")
            frame.pack(side="top")
            for c in range(10):
                checkbox = CTkCheckBox(frame, text="", width=0, corner_radius=0, border_width=1)
                checkbox.pack(side="left")
                if (r + c) % 2 == 0:
                    checkbox.select()

        self.scrollable_frame_1.pack(pady=5)
        self.scrollable_frame_2.pack(pady=5)


class _CTkTabviewsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.tabview_1 = CTkTabview(self)
        tab1 = self.tabview_1.add("CTkTabview")
        tab2 = self.tabview_1.add("Tab 2")
        tab3 = self.tabview_1.add("Tab 3")
        CTkButton(tab1, text="Widget on 1st Tab").pack(pady=5)
        CTkCheckBox(tab2, text="Widget on 2nd Tab").pack(pady=5)
        CTkSwitch(tab3, text="Widget on 3rd Tab").pack(pady=5)

        self.tabview_2 = CTkTabview(self, anchor="sw", corner_radius=30, border_width=3, width=400, height=100, state="disabled")
        tab1 = self.tabview_2.add("anchor sw")
        tab2 = self.tabview_2.add("disabled")
        tab3 = self.tabview_2.add("with border")
        CTkButton(tab1, text="Widget on 1st Tab").pack(pady=5)

        self.tabview_1.pack(pady=5)
        self.tabview_2.pack(pady=5)


class _CTkGridViewsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.gridview = CTkGridView(self, width=400, height=400)

        self.positions = [(0, 0, 2, 2),
                          (0, 2, 1, 2),
                          (1, 2, 1, 2),
                          (2, 0, 1, 1),
                          (2, 1, 1, 2),
                          (2, 3, 1, 1),
                          (3, 0, 1, 4)]
        for n, positions in enumerate(self.positions):
            frame = self.gridview.insert(f"Frame {n}", *positions)
            next_n = (n + 1) % len(self.positions)
            CTkLabel(frame, text=f"Frame {n + 1}", height=0).pack(pady=(5, 0))
            CTkButton(frame, text="Hide next", command=partial(self._hide_frame, next_n)).pack(padx=5, pady=2)
            CTkButton(frame, text="Show next", command=partial(self._show_frame, next_n)).pack(padx=5, pady=(0, 5))

        self.gridview.pack(pady=5)

    def _hide_frame(self, n: int) -> None:
        self.gridview.hide(f"Frame {n}")

    def _show_frame(self, n: int) -> None:
        self.gridview.show(f"Frame {n}", *self.positions[n])


class _CTkSectionViewsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.sectionview_1 = CTkSectionView(self)
        sec1 = self.sectionview_1.add("CTkSectionView")
        sec2 = self.sectionview_1.add("Section 2")
        sec3 = self.sectionview_1.add("Section 3")
        CTkButton(sec1, text="Widget in 1st Section").pack(padx=5, pady=5)
        CTkCheckBox(sec2, text="Widget in 2nd Section").pack(padx=5, pady=5)
        CTkSwitch(sec3, text="Widget in 3rd Section").pack(padx=5, pady=5)

        self.sectionview_2 = CTkSectionView(self,
                                            open_symbol=">",
                                            close_symbol="v",
                                            border_spacing=5,
                                            internal_spacing=0,
                                            symbol={"compound": "left"},
                                            max_open=0)
        sec1 = self.sectionview_2.add("Different style")
        sec2 = self.sectionview_2.add("No limit to open sections")
        sec3 = self.sectionview_2.add("Section 3")
        CTkButton(sec1, text="Widget in 1st Section").pack(padx=5, pady=5)
        CTkCheckBox(sec2, text="Widget in 2nd Section").pack(padx=5, pady=5)
        CTkSwitch(sec3, text="Widget in 3rd Section").pack(padx=5, pady=5)

        self.sectionview_1.pack(pady=5)
        self.sectionview_2.pack(pady=5)


class _CTkFloatingFramesFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.floating_frame = CTkFloatingFrame(self, corner_radius=20, border_width=5)
        label = CTkLabel(self.floating_frame, text="A frame detached from any window,\nalways on top of everything,\nthat can contain anything.", width=200, height=200)
        label.pack(fill="both", expand=True, padx=10, pady=10)
        self.open_floating_frame = CTkButton(self, text="Open CTkFloatingFrame", command=lambda: self.floating_frame.open(1000, 500))
        self.close_floating_frame = CTkButton(self, text="Close", command=self.floating_frame.close)

        self.open_floating_frame.pack(pady=5)
        self.close_floating_frame.pack(pady=5)


class _CTkToplevelsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.open_toplevel = CTkButton(self, text="Open CTkToplevel", command=self._open_ctktoplevel)

        self.open_toplevel.pack(pady=5)

    def _open_ctktoplevel(self) -> None:
        toplevel = CTkToplevel(self, title="CTkToplevel")
        toplevel.geometry("500x250")
        toplevel.resizable(True, True)
        label = CTkLabel(toplevel, text="A new window that can contains anything")
        label.pack(padx=5, pady=5)
        self.after(50, toplevel.lift)


class _CTkInputDialogsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.open_dialog_1 = CTkButton(self, text="Open CTkInputDialog", command=self._open_input_dialog_1)
        self.open_dialog_2 = CTkButton(self, text="with values", command=self._open_input_dialog_2)

        self.open_dialog_1.pack(pady=5)
        self.open_dialog_2.pack(pady=5)

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


class _CTkToolTipsFrame(CTkFrame):
    def __init__(self, master, **kwargs: Any) -> None:
        super().__init__(master, **kwargs)

        self.button_withtt_1 = CTkButton(self, text="CTkToolTip")
        self.tooltip_1 = CTkToolTip(self.button_withtt_1,
                                    label={"wraplength": 200},
                                    title="CTkToolTip",
                                    text="Little window that opens when the user hovers over the linked widget, which usually contains an explanation of the object.")
        self.button_withtt_2 = CTkButton(self, text="with any widgets")
        self.tooltip_2 = CTkToolTip(self.button_withtt_2,
                                    mode="live_mouse",
                                    anchor="s",
                                    fg_color="transparent",
                                    close_on_interaction=False,
                                    pre_command=self._update_progressbar_ontt)
        self.progressbar_ontt = CTkProgressBar(self.tooltip_2, orientation="horizontal", thickness=30, show_value=True)
        self.progressbar_ontt.pack()

        self.button_withtt_1.pack(pady=5)
        self.button_withtt_2.pack(pady=5)

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
