from __future__ import annotations

import sys
import os
import pathlib
import json
from typing import Any
from typing_extensions import Literal, TypedDict, Unpack

from ..utility import deep_update


class ThemeInfo(TypedDict, total=False):
    orientation: Literal["horizontal", "vertical"]
    thickness: int
    lenght: int
    width: int
    height: int
    checkbox_width: int
    checkbox_height: int
    switch_width: int
    switch_height: int
    radiobutton_width: int
    radiobutton_height: int
    corner_radius: int
    button_corner_radius: int
    button_length: int
    border_width: int
    border_width_checked: int
    border_width_unchecked: int
    border_spacing: int
    bg_color: str | tuple[str, str]
    fg_color: str | tuple[str, str]
    top_fg_color: str | tuple[str, str]
    border_color: str | tuple[str, str]
    checkmark_color: str | tuple[str, str]
    button_color: str | tuple[str, str]
    button_hover_color: str | tuple[str, str]
    placeholder_text_color: str | tuple[str, str]
    progress_color: str | tuple[str, str]
    selected_color: str | tuple[str, str]
    unselected_color: str | tuple[str, str]
    selected_hover_color: str | tuple[str, str]
    unselected_hover_color: str | tuple[str, str]
    text_color: str | tuple[str, str]
    text_color_disabled: str | tuple[str, str]
    hover_color: str | tuple[str, str]
    hover: bool
    dynamic_resizing: bool
    activate_scrollbars: bool
    round_width_to_even_numbers: bool
    round_height_to_even_numbers: bool
    placeholder_text: str
    title: str
    text: str
    font: Any
    family: str
    size: int
    weight: Literal["normal", "bold"]
    slant: Literal["italic", "roman"]
    underline: bool
    overstrike: bool
    anchor: str  #center or combination of n, e, s, w
    justify: Literal["left", "center", "right"]
    compound: Literal["center", "left", "right", "top", "bottom", "none"]
    wraplength: int
    minimum_pixel_length: int
    min_character_width: int
    overwrite_preferred_drawing_method: Literal["polygon_shapes", "font_shapes", "circle_shapes"] | None
    button: dict
    dropdown: dict
    entry: dict
    frame: dict
    label: dict
    scrollbar: dict
    segmented_button: dict


class ThemeManager:

    _theme: dict[str, ThemeInfo] = {}  # contains all the theme data
    _built_in_themes: list[str] = ["blue", "green", "gold", "dark-blue"]
    _last_loaded_theme: str | None = None

    @classmethod
    def load_theme(cls, theme_name_or_path: str, add: bool = False) -> None:
        script_directory = os.path.dirname(os.path.abspath(__file__))

        if theme_name_or_path in cls._built_in_themes:
            customtkinter_path = pathlib.Path(script_directory).parent.parent.parent
            with open(os.path.join(customtkinter_path, "assets", "themes", f"{theme_name_or_path}.json"), "r") as f:
                theme = json.load(f)
        else:
            with open(theme_name_or_path, "r") as f:
                theme = json.load(f)

        # store theme path for saving
        cls._last_loaded_theme = theme_name_or_path

        # filter theme values for platform
        for key, info in theme.items():
            # check if values for key differ on platforms
            if "macOS" in info:
                if sys.platform == "darwin":
                    theme[key] = info["macOS"]
                elif sys.platform.startswith("win"):
                    theme[key] = info["Windows"]
                else:
                    theme[key] = info["Linux"]

        if add:
            deep_update(cls._theme, theme)
        else:
            cls._theme = theme

    @classmethod
    def add_key(cls, custom_key: str, **kwargs: Unpack[ThemeInfo]) -> None:
        if custom_key in cls._theme:
            raise KeyError(f"Custom Key '{custom_key}' already defined: use 'update_key' method instead.")
        cls._theme[custom_key] = kwargs

    @classmethod
    def update_key(cls, custom_key: str, **kwargs: Unpack[ThemeInfo]) -> None:
        if custom_key not in cls._theme:
            raise KeyError(f"Custom Key '{custom_key}' not found in the loaded theme: use 'add_key' method instead.")
        deep_update(cls._theme[custom_key], kwargs)

    @classmethod
    def get_info(cls, default_key: str, custom_key: str | None, **kwargs: Unpack[ThemeInfo]) -> ThemeInfo:
        theme_info: ThemeInfo = {}
        deep_update(theme_info, cls._theme[default_key])
        if custom_key is not None:
            if custom_key in cls._theme:
                deep_update(theme_info, cls._theme[custom_key])
            else:
                raise KeyError(f"Custom Key '{custom_key}' not found in the loaded theme.")
        deep_update(theme_info, kwargs)
        return theme_info

    @classmethod
    def save_theme(cls, path: str | None = None) -> None:
        if cls._theme:
            if cls._last_loaded_theme in cls._built_in_themes and path is None:
                raise ValueError(f"Cannot modify builtin theme '{cls._last_loaded_theme}': provide an output path.")
            if path is None:
                path = cls._last_loaded_theme
            with open(path, "w") as f:
                json.dump(cls._theme, f, indent=2)
        else:
            raise ValueError("Nothing to save.")
