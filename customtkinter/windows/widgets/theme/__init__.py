from .theme_manager import ThemeManager

# load default blue theme
try:
    ThemeManager.load_theme("blue")
except FileNotFoundError as err:
    raise FileNotFoundError(f"{err}\nThe .json theme file for CustomTkinter could not be found.\n" +
                            "If packaging with pyinstaller was used, have a look at the wiki:\n" +
                            "https://github.com/TomSchimansky/CustomTkinter/wiki/Packaging#windows-pyinstaller-auto-py-to-exe") from err
