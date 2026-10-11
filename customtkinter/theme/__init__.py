from .theme_manager import ThemeManager
from .theme_manager import AnchorType
from .theme_manager import ColorType
from .theme_manager import TransparentColorType

# load default blue theme
try:
    ThemeManager.load_theme("blue")
except FileNotFoundError as err:
    raise FileNotFoundError(f"{err}\nThe .json theme file for CustomTkinter could not be found.") from err
