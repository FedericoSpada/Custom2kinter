from __future__ import annotations

import sys
import os
import pathlib
import json
from typing import Any, Union
from typing_extensions import Literal, TypeAlias, TypedDict, Unpack

from ..utility import deep_update


#old syntax for retrocompatibility reasons
ColorType: TypeAlias = Union[Literal["transparent"], str, tuple[str, str], list[str]]
TransparentColorType: TypeAlias = Union[Literal["transparent"], ColorType]
AnchorType : TypeAlias = Literal["center", "n", "ne", "e", "se", "s", "sw", "w", "nw"]


class ThemeInfo(TypedDict, total=False, extra_items=Any):
    orientation: Literal["horizontal", "vertical", "both"]
    thickness: int
    length: int
    width: int
    height: int
    box_width: int
    box_height: int
    corner_radius: int
    button_length: int
    border_width: int
    border_width_checked: int
    border_width_unchecked: int
    border_spacing: int
    internal_spacing: int
    bg_color: TransparentColorType
    fg_color: TransparentColorType
    fg_color_header: TransparentColorType
    fg_color_checked: ColorType
    fg_color_unchecked: ColorType
    top_fg_color: ColorType
    border_color: TransparentColorType
    symbol_color: ColorType
    button_color: ColorType
    button_hover_color: ColorType
    progress_color: TransparentColorType
    selected_color: ColorType
    unselected_color: ColorType
    selected_hover_color: ColorType
    unselected_hover_color: ColorType
    hover_color: ColorType
    hover_color_checked: TransparentColorType
    hover_color_unchecked: TransparentColorType
    text_color: ColorType
    text_color_disabled: ColorType
    placeholder_text_color: ColorType
    transparency: float
    hover: bool
    show_value: bool
    activate_scrollbars: bool
    placeholder_text: str
    title: str
    text: str
    text_checked: str
    text_unchecked: str
    font: Any
    family: str
    size: int
    weight: Literal["normal", "bold"]
    slant: Literal["italic", "roman"]
    underline: bool
    overstrike: bool
    image: Any
    image_checked: Any
    image_unchecked: Any
    light_image: Any
    dark_image: Any
    open_symbol: str
    close_symbol: str
    anchor: AnchorType
    justify: Literal["left", "center", "right"]
    compound: Literal["center", "left", "right", "top", "bottom", "none"]
    wraplength: int
    delay: int
    minimum_pixel_length: int
    min_character_width: int
    columns: int
    rows: int
    x_offset: int
    y_offset: int
    button: dict
    combobox: dict
    dropdown: dict
    entry: dict
    label: dict
    scrollbar: dict
    segmented_button: dict
    symbol: dict
    togglebutton: dict
    tooltip: dict


class ThemeManager:

    _theme: dict[str, ThemeInfo] = {}  # contains all the theme data
    _built_in_themes: list[str] = ["blue", "gold", "green", "lavender", "metal", "orange", "pink",
                                   "red", "dark-blue", "dark-orange", "autumn", "breeze", "carrot",
                                   "cherry", "coffee", "earth", "marsh", "midnight", "patina",
                                   "rime", "rose", "violet"]
    _last_loaded_theme: str | None = None

    @classmethod
    def load_theme(cls, theme_name_or_path: str, add: bool = False) -> None:
        script_directory = os.path.dirname(os.path.abspath(__file__))

        theme: dict[str, Any]
        if theme_name_or_path in cls._built_in_themes:
            customtkinter_path = pathlib.Path(script_directory).parent.parent.parent
            with open(os.path.join(customtkinter_path, "assets", "themes", f"{theme_name_or_path}.json"), "r") as f:
                theme = json.load(f)
        else:
            with open(theme_name_or_path, "r") as f:
                theme = json.load(f)

        if "Colors" in theme:
            with open(os.path.join(customtkinter_path, "assets", "themes", "_common.json"), "r") as f:
                theme.update(json.load(f))

        cls._replace_platform(theme)
        if add:
            deep_update(cls._theme, theme)
        else:
            cls._theme = theme
        cls._replace_references(cls._theme)

        # store theme path for saving
        cls._last_loaded_theme = theme_name_or_path

    @classmethod
    def add_key(cls, custom_key: str, **kwargs: Unpack[ThemeInfo]) -> None:
        if custom_key in cls._theme:
            raise KeyError(f"Custom Key '{custom_key}' already defined: use 'update_key' method instead.")
        cls._replace_platform(kwargs)
        cls._replace_references(kwargs)
        cls._theme[custom_key] = kwargs

    @classmethod
    def update_key(cls, custom_key: str, **kwargs: Unpack[ThemeInfo]) -> None:
        if custom_key not in cls._theme:
            raise KeyError(f"Custom Key '{custom_key}' not found in the loaded theme: use 'add_key' method instead.")
        cls._replace_platform(kwargs)
        cls._replace_references(kwargs)
        deep_update(cls._theme[custom_key], kwargs)

    @classmethod
    def get_info(cls, default_key: str, custom_key: str | None = None, **kwargs: Unpack[ThemeInfo]) -> ThemeInfo:
        theme_info: ThemeInfo = {}
        deep_update(theme_info, cls._theme[default_key])
        if custom_key is not None:
            if custom_key in cls._theme:
                deep_update(theme_info, cls._theme[custom_key])
            else:
                raise KeyError(f"Custom Key '{custom_key}' not found in the loaded theme.")
        cls._replace_references(kwargs)
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

    @classmethod
    def _replace_platform(cls, dictionary: dict) -> None:
        for key, value in dictionary.items():
            if isinstance(value, dict):
                if "macOS" in value:
                    if sys.platform == "darwin":
                        dictionary[key] = value["macOS"]
                    elif sys.platform.startswith("win"):
                        dictionary[key] = value["Windows"]
                    else:
                        dictionary[key] = value["Linux"]
                else:
                    cls._replace_platform(value)

    @classmethod
    def _replace_references(cls, dictionary: dict) -> None:
        for key, value in dictionary.items():
            if isinstance(value, dict):
                cls._replace_references(value)

            elif isinstance(value, str) and value.startswith("@"):
                #if the value actually starts with "@", it can be escaped using "@@"
                if value.startswith("@@"):
                    new_value = value.removeprefix("@")
                else:
                    try:
                        new_value = cls._theme
                        for name in value.removeprefix("@").split("."):
                            new_value = new_value[name]
                    except (KeyError, TypeError) as exc:
                        raise ValueError(f"Theme reference '{value}' could not be resolved.") from exc
                dictionary[key] = new_value
