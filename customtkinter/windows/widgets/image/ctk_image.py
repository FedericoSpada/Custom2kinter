from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Tuple, Union
from typing_extensions import Literal, TypeAlias, TypedDict, Unpack
from PIL import Image, ImageTk

from ..theme import ThemeManager
from ..utility import check_kwargs_empty


class CTkImageArgs(TypedDict, total=False):
    width: int
    height: int
    light_image: Image.Image | Path | str | None
    dark_image: Image.Image | Path | str | None


class CTkImage:
    """
    Class to store one or two PIl.Image.Image objects and display size independent of scaling:

    light_image: PIL.Image.Image for light mode
    dark_image: PIL.Image.Image for dark mode
    size: tuple (<width>, <height>) with display size for both images

    One of the two images can be None and will be replaced by the other image.
    """

    #used to avoid opening the same file multiple times
    _images: dict[str, Image.Image] = {}

    def __init__(self,
                 theme_key: str | None = None,
                 **kwargs: Unpack[CTkImageArgs]) -> None:

        self._theme_info: CTkImageArgs = ThemeManager.get_info("CTkImage", theme_key, **kwargs)

        #convert images to usable type
        self._theme_info["light_image"] = self._convert_image(self._theme_info["light_image"])
        self._theme_info["dark_image"] = self._convert_image(self._theme_info["dark_image"])

        #functionality
        self._configure_callback_list: list[Callable[[], None]] = []
        self._scaled_photo_images: dict[tuple[int, int, int], ImageTk.PhotoImage] = {}

    @classmethod
    def from_parameter(cls, parameter: ImageType) -> CTkImage:
        if parameter is None or parameter == "":
            return CTkImage()

        elif isinstance(parameter, CTkImage):
            return parameter

        elif isinstance(parameter, dict):
            return CTkImage(**parameter)

        elif isinstance(parameter, tuple) and 3 <= len(parameter) <= 4:
            if isinstance(parameter[1], float | int):
                parameter = (None,) + parameter
            return CTkImage(light_image=parameter[0],
                            dark_image=parameter[1],
                            width=parameter[2],
                            height=parameter[3])

        elif isinstance(parameter, str):
            return CTkImage(theme_key=parameter)

        else:
            raise ValueError(f"Wrong image type {type(parameter)}.\n" +
                             "Image argument must be 'None', a tuple of len 3 to 4, " +
                             "an instance of CTkImage, an instance of CTkImageArgs or a str representing a custom theme key.\n" +
                             "\nUsage example:\n" +
                             "image=customtkinter.CTkImage(light_image='<path>', dark_image='<path>', width=<width>, height=<height>)\n" +
                             "image=('<path>', <width>, <height>)\n" +
                             "image=('<light_path>', '<dark_path>', <width>, <height>)\n" +
                             "image={'light_image': '<path>', 'dark_image': '<path>', 'width': <width>, 'height': <height>}\n" +
                             "image='<theme_key>'\n" +
                             "image=None")

    def add_configure_callback(self, callback: Callable[[], None]) -> None:
        """ Adds function that gets called when image gets configured """
        self._configure_callback_list.append(callback)

    def remove_configure_callback(self, callback: Callable[[], None]) -> None:
        """ Removes function that gets called when image gets configured """
        try:
            self._configure_callback_list.remove(callback)
        except ValueError:
            pass

    def configure(self, **kwargs: Unpack[CTkImageArgs]) -> None:
        if "width" in kwargs:
            self._theme_info["width"] = kwargs.pop("width")

        if "height" in kwargs:
            self._theme_info["height"] = kwargs.pop("height")

        if "light_image" in kwargs:
            self._theme_info["light_image"] = self._convert_image(kwargs.pop("light_image"))
            self._scaled_photo_images.clear()

        if "dark_image" in kwargs:
            self._theme_info["dark_image"] = self._convert_image(kwargs.pop("dark_image"))
            self._scaled_photo_images.clear()

        # call all functions registered with add_configure_callback()
        for callback in self._configure_callback_list:
            callback()

        check_kwargs_empty(kwargs, True)

    def cget(self, attribute_name: str) -> Any:
        if attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            raise ValueError(f"'{attribute_name}' is not a supported argument. Look at the documentation for supported arguments.")

    def get(self, scaling_factor: float, appearance_mode: Literal["light", "dark"]) -> ImageTk.PhotoImage | Literal[""]:
        if appearance_mode == "light":
            light_image = self._theme_info["light_image"]
            image = light_image if light_image is not None else self._theme_info["dark_image"]
        else:
            dark_image = self._theme_info["dark_image"]
            image = dark_image if dark_image is not None else self._theme_info["light_image"]

        if image is None:
            image = ""
        else:
            size = (round(self._theme_info["width"] * scaling_factor),
                    round(self._theme_info["height"] * scaling_factor))
            key = (*size, id(image))
            if key in self._scaled_photo_images:
                image = self._scaled_photo_images[key]
            else:
                image = ImageTk.PhotoImage(image.resize(size))
                self._scaled_photo_images[key] = image
        return image

    def _convert_image(self, image: Image.Image | Path | str | None) -> Image.Image | None:
        if image is None or image == "":
            return None

        elif isinstance(image, Image.Image):
            return image

        elif isinstance(image, (Path, str)):
            if isinstance(image, Path):
                image = str(image.resolve())
            if image not in self._images:
                self._images[image] = Image.open(image)
            return self._images[image]

        else:
            raise ValueError(f"Can't convert type {type(image)} to Image.Image.\n" +
                             "Please provide a str representing a path o directly an Image.Image object.")


#old syntax for retrocompatibility reasons
ImageType: TypeAlias = Union[CTkImageArgs, CTkImage, Tuple, str, None]
