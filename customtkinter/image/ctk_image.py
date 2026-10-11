from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Tuple, Union
from typing_extensions import Literal, TypeAlias, TypedDict, Unpack
from PIL import Image, ImageTk

from ..theme import ThemeManager
from ..utility import check_kwargs_empty


class CTkImageArgs(TypedDict, total=False, closed=True):
    width: int   #'0' means original dimension or proper value to preserve aspect ratio
    height: int  #'0' means original dimension or proper value to preserve aspect ratio
    light_image: Image.Image | Path | str | None
    dark_image: Image.Image | Path | str | None


class CTkImage:
    """
    Container for an image resource, with light and dark variants and a display size independent of scaling.

    It is not a widget: pass it to the 'image' argument of widgets such as CTkLabel or CTkButton.
    A widget also accepts a dict of arguments, a tuple or a custom theme key,
    and converts them to a CTkImage that can be retrieved with cget("image").

    For more details, check out the documentation:
    https://custom2kinter.readthedocs.io/stable/utilities/CTkImage.html
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
        """
        Converts any accepted image representation to a CTkImage (a CTkImage is returned as it is).

        Args:
            parameter: a CTkImage, a dict of arguments, a tuple (path, width, height) or
                       (light_path, dark_path, width, height), a custom theme key, or None/"" for no image.

        Raises:
            ValueError: if the parameter has an unsupported type.
        """
        if parameter is None or parameter == "":
            return CTkImage()

        elif isinstance(parameter, CTkImage):
            return parameter

        elif isinstance(parameter, dict):
            return CTkImage(**parameter)

        elif isinstance(parameter, tuple) and 3 <= len(parameter) <= 4:
            if isinstance(parameter[1], (float, int)):
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
                             "image=customtkinter.CTkImage(light_image=<light_path>, dark_image=<dark_path>, width=<width>, height=<height>)\n" +
                             "image=(<path>, <width>, <height>)\n" +
                             "image=(<light_path>, <dark_path>, <width>, <height>)\n" +
                             "image={'light_image': <path>, 'dark_image': <path>, 'width': <width>, 'height': <height>}\n" +
                             "image=<theme_key>\n" +
                             "image=None")

    def add_configure_callback(self, callback: Callable[[], None]) -> None:
        """Registers a function that is invoked every time the image is configured."""
        self._configure_callback_list.append(callback)

    def remove_configure_callback(self, callback: Callable[[], None]) -> None:
        """Unregisters a function previously added with add_configure_callback()."""
        try:
            self._configure_callback_list.remove(callback)
        except ValueError:
            pass

    def configure(self, **kwargs: Unpack[CTkImageArgs]) -> None:
        """
        Changes the value of one or more arguments after the object has been created.
        All the widgets using this image are updated.

        Args:
            **kwargs: name-value pairs of valid arguments.

        Raises:
            ValueError: if an unsupported argument is provided.
        """
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

        check_kwargs_empty(kwargs, raise_error=True)

    def cget(self, attribute_name: str) -> Any:
        """
        Returns the current value of the argument named 'attribute_name'.

        Raises:
            ValueError: if the argument name is unknown.
        """
        if attribute_name in self._theme_info:
            return self._theme_info[attribute_name]
        else:
            raise ValueError(f"'{attribute_name}' is not a supported argument. Look at the documentation for supported arguments.")

    def get(self, scaling_factor: float, appearance_mode: Literal["light", "dark"]) -> ImageTk.PhotoImage | Literal[""]:
        """
        Returns the image to be displayed, resized to the display size multiplied by 'scaling_factor'
        (an empty string if there is no image).

        Args:
            scaling_factor: scaling to be applied to the display size.
            appearance_mode: selects the light or dark image (the other is used if one is missing).
        """
        if appearance_mode == "light":
            light_image = self._theme_info["light_image"]
            image = light_image if light_image is not None else self._theme_info["dark_image"]
        else:
            dark_image = self._theme_info["dark_image"]
            image = dark_image if dark_image is not None else self._theme_info["light_image"]

        if image is None:
            image = ""
        else:
            width = self._theme_info["width"]
            height = self._theme_info["height"]

            #change 0s to proper values
            if width == 0 and height == 0:
                width = image.width
                height = image.height
            elif width == 0:
                width = round(image.width * height / image.height)
            elif height == 0:
                height = round(image.height * width / image.width)

            size = (round(width * scaling_factor), round(height * scaling_factor))
            key = (*size, id(image))
            if key in self._scaled_photo_images:
                image = self._scaled_photo_images[key]
            else:
                image = ImageTk.PhotoImage(image.resize(size))
                self._scaled_photo_images[key] = image
        return image

    def __bool__(self) -> bool:
        return self._theme_info["light_image"] is not None or self._theme_info["dark_image"] is not None

    def _convert_image(self, image: Image.Image | Path | str | None) -> Image.Image | None:
        if image is None or image == "":
            return None

        elif isinstance(image, Image.Image):
            return image

        elif isinstance(image, (Path, str)):
            if isinstance(image, Path):
                image = str(image.resolve())
            if image not in self._images:
                #since Image.open is lazy, we access the file immediately by creating a copy
                # so that the file can be freed
                self._images[image] = Image.open(image).copy()
            return self._images[image]

        else:
            raise ValueError(f"Can't convert type {type(image)} to Image.Image.\n" +
                             "Please provide a str representing a path or an Image.Image object directly.")


#old syntax for retrocompatibility reasons
ImageType: TypeAlias = Union[CTkImageArgs, CTkImage, Tuple, str, None]
