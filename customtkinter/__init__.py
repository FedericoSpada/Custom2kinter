__version__ = "5.3.0"

from tkinter import Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, TclError
from tkinter.constants import *
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
from .windows.widgets.core_rendering import Star
from .windows.widgets.core_rendering import Triangle

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
from .windows.widgets import CTkGridView
from .windows.widgets import CTkLabel
from .windows.widgets import CTkListBox
from .windows.widgets import CTkOptionMenu
from .windows.widgets import CTkProgressBar
from .windows.widgets import CTkRadioButton
from .windows.widgets import CTkScrollbar
from .windows.widgets import CTkSectionView
from .windows.widgets import CTkSegmentedButton
from .windows.widgets import CTkSlider
from .windows.widgets import CTkSpinBox
from .windows.widgets import CTkSwitch
from .windows.widgets import CTkSymbolBox
from .windows.widgets import CTkTabview
from .windows.widgets import CTkTextbox
from .windows.widgets import CTkToggleButton
from .windows.widgets import CTkToast
from .windows.widgets import CTkToolTip
from .windows.widgets import CTkScrollableFrame

# import windows
from .windows import CTk
from .windows import CTkToplevel
from .windows import CTkInputDialog
from .windows import CTkMessageDialog
from .windows import CTkFontDialog
from .windows import showinfo
from .windows import showwarning
from .windows import showerror
from .windows import askquestion
from .windows import askokcancel
from .windows import askyesno
from .windows import askyesnocancel
from .windows import askretrycancel
from .windows import askabortretryignore
from .windows import askdirectory
from .windows import askopenfilename
from .windows import askopenfilenames
from .windows import asksaveasfilename
from .windows import askcolor
from .windows import askrgbcolor
from .windows import askfont

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
from .windows.ctk_dialogs import IconType
from .windows.ctk_dialogs import AnswersType
from .windows.ctk_dialogs import ReplyType

_ = Variable, StringVar, IntVar, DoubleVar, BooleanVar, Event, TclError, CENTER  # prevent IDE from removing unused imports


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


def get_widget_scaling() -> float:
    """ get scaling for the widget dimensions """
    return ScalingTracker.get_widget_scaling()


def set_window_scaling(scaling_value: float) -> None:
    """ set scaling for window dimensions """
    ScalingTracker.set_window_scaling(scaling_value)


def get_window_scaling() -> float:
    """ get scaling for window dimensions """
    return ScalingTracker.get_window_scaling()


def deactivate_automatic_dpi_awareness() -> None:
    """ deactivate DPI awareness of current process (windll.shcore.SetProcessDpiAwareness(0)) """
    ScalingTracker.deactivate_automatic_dpi_awareness = True
