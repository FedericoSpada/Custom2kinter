import sys

from .ctk_font import CTkFont
from .ctk_font import FontType
from .font_manager import FontManager

# to change preferred_drawing_method if loading shapes font fails
from ..core_rendering import BaseShape
from ..utility import get_asset_path

FontManager.init_font_manager()

# load Roboto fonts (used on Windows/Linux)
FontManager.load_font(get_asset_path("fonts", "Roboto", "Roboto-Regular.ttf"))
FontManager.load_font(get_asset_path("fonts", "Roboto", "Roboto-Medium.ttf"))

# load font necessary for rendering the widgets (used on Windows/Linux)
if not FontManager.load_font(get_asset_path("fonts", "CustomTkinter_shapes_font.otf")):
    # change draw method if font loading failed
    if BaseShape.preferred_drawing_method == "font":
        sys.stderr.write("customtkinter.font warning: " +
                         "Preferred drawing method 'font' can not be used because the font file could not be loaded.\n" +
                         "Using 'circles' instead. The rendering quality will be bad!\n")
        BaseShape.preferred_drawing_method = "circles"
