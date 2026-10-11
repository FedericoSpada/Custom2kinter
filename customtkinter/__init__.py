__version__ = "5.3.0"

from tkinter import Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, TclError
from tkinter.constants import *
from typing_extensions import Literal

# import manager classes
from .appearance_mode import AppearanceModeTracker
from .font import FontManager
from .scaling import ScalingTracker
from .theme import ThemeManager
from .core_rendering import DRAWING_METHODS
from .core_rendering import Arrow
from .core_rendering import Bar
from .core_rendering import BaseShape
from .core_rendering import BorderedRoundedRect
from .core_rendering import Checkmark
from .core_rendering import RoundedRect
from .core_rendering import Star
from .core_rendering import Triangle

# import base widgets
from .core_rendering import CTkCanvas
from .core_widget_classes import CTkContainer
from .core_widget_classes import CTkScrollable
from .core_widget_classes import CTkWidget

# import widgets
from .ctk_tk import CTk
from .ctk_button import CTkButton
from .ctk_checkbox import CTkCheckBox
from .ctk_combobox import CTkComboBox
from .ctk_entry import CTkEntry
from .ctk_floating_frame import CTkFloatingFrame
from .ctk_frame import CTkFrame
from .ctk_gridview import CTkGridView
from .ctk_label import CTkLabel
from .ctk_listbox import CTkListBox
from .ctk_optionmenu import CTkOptionMenu
from .ctk_progressbar import CTkProgressBar
from .ctk_radiobutton import CTkRadioButton
from .ctk_scrollbar import CTkScrollbar
from .ctk_sectionview import CTkSectionView
from .ctk_segmented_button import CTkSegmentedButton
from .ctk_slider import CTkSlider
from .ctk_spinbox import CTkSpinBox
from .ctk_switch import CTkSwitch
from .ctk_symbolbox import CTkSymbolBox
from .ctk_tabview import CTkTabview
from .ctk_textbox import CTkTextbox
from .ctk_togglebutton import CTkToggleButton
from .ctk_toast import CTkToast
from .ctk_tooltip import CTkToolTip
from .ctk_scrollable_frame import CTkScrollableFrame
from .ctk_toplevel import CTkToplevel
from .ctk_input_dialog import CTkInputDialog
from .ctk_dialogs import CTkMessageDialog
from .ctk_dialogs import CTkFontDialog
from .ctk_dialogs import showinfo
from .ctk_dialogs import showwarning
from .ctk_dialogs import showerror
from .ctk_dialogs import askquestion
from .ctk_dialogs import askokcancel
from .ctk_dialogs import askyesno
from .ctk_dialogs import askyesnocancel
from .ctk_dialogs import askretrycancel
from .ctk_dialogs import askabortretryignore
from .ctk_dialogs import askdirectory
from .ctk_dialogs import askopenfilename
from .ctk_dialogs import askopenfilenames
from .ctk_dialogs import asksaveasfilename
from .ctk_dialogs import askcolor
from .ctk_dialogs import askrgbcolor
from .ctk_dialogs import askfont

# import auxiliary classes
from .font import CTkFont
from .image import CTkImage

# import type aliases
from .theme import AnchorType
from .theme import ColorType
from .theme import TransparentColorType
from .core_rendering import DrawingMethodType
from .core_rendering import SectionType
from .font import FontType
from .image import ImageType
from .ctk_dialogs import IconType
from .ctk_dialogs import AnswersType
from .ctk_dialogs import ReplyType

_ = Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, TclError, CENTER  # prevent IDE from removing unused imports


def set_appearance_mode(mode: Literal["light", "dark", "system"]) -> None:
    """
    Changes the appearance mode of all windows and widgets: "light" and "dark" force it,
    while "system" follows the mode of the computer (also when it changes).
    """
    AppearanceModeTracker.set_appearance_mode(mode)


def get_appearance_mode() -> Literal["light", "dark"]:
    """Returns the actual appearance mode currently active: "light" or "dark"."""
    if AppearanceModeTracker.get_mode() == 0:
        return "light"
    elif AppearanceModeTracker.get_mode() == 1:
        return "dark"
    raise RuntimeError("Something went very wrong")


def set_default_color_theme(theme_name_or_path: str) -> None:
    """Loads a theme from a built-in theme name or from the path of a JSON file."""
    ThemeManager.load_theme(theme_name_or_path, add=False)


def add_color_theme(theme_path: str) -> None:
    """Extends a previously loaded theme by appending the keys contained in the provided JSON file."""
    ThemeManager.load_theme(theme_path, add=True)


def set_widget_scaling(scaling_value: float) -> None:
    """Sets the additional scaling factor for all widgets (min 0.4) and updates them."""
    ScalingTracker.set_widget_scaling(scaling_value)


def get_widget_scaling() -> float:
    """Returns the additional scaling factor for all widgets previosly set with set_widget_scaling()."""
    return ScalingTracker.get_widget_scaling()


def set_window_scaling(scaling_value: float) -> None:
    """Sets the additional scaling factor for all windows (min 0.4) and updates them."""
    ScalingTracker.set_window_scaling(scaling_value)


def get_window_scaling() -> float:
    """Returns the additional scaling factor for all windows previosly set with set_window_scaling()."""
    return ScalingTracker.get_window_scaling()


def deactivate_automatic_dpi_awareness() -> None:
    """Deactivates DPI awareness of current process (windll.shcore.SetProcessDpiAwareness(0))."""
    ScalingTracker.deactivate_automatic_dpi_awareness = True
