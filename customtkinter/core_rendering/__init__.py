import sys

from .ctk_canvas import CTkCanvas
from .draw_engine import DRAWING_METHODS
from .draw_engine import Arrow
from .draw_engine import Bar
from .draw_engine import BaseShape
from .draw_engine import BorderedRoundedRect
from .draw_engine import Checkmark
from .draw_engine import RoundedRect
from .draw_engine import Star
from .draw_engine import Triangle

from .draw_engine import DrawingMethodType
from .draw_engine import SectionType

CTkCanvas.init_font_character_mapping()

# determine draw method based on current platform
if sys.platform == "darwin":
    BaseShape.preferred_drawing_method = "polygons"
else:
    BaseShape.preferred_drawing_method = "font"
