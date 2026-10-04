CTkImage
========

CTkImage is a container for an image resource used by CustomTkinter widgets to display
light-mode and dark-mode variants with the provided dimensions.

It is not a widget and can't be displayed by itself;
pass it to a widget such as :doc:`/widgets/CTkLabel` or :doc:`/widgets/CTkButton`.

By default, the image will be displayed with its original dimensions.
If you provide just :py:attr:`width` or :py:attr:`height`,
the other dimension will be calculated to preserve the aspect ratio.
If you specify both, the image is resized to those exact dimensions and may be stretched.

If you provide just one of :py:attr:`light_image` and :py:attr:`dark_image`,
it will be used for both :doc:`Appearance Modes </concepts/AppearanceMode>`.


Example Code
------------

There are 4 ways in CustomTkinter to set an image:

.. tab-set::

   .. tab-item:: CTkImage instance

      .. code:: python

         myimage = ctk.CTkImage(light_image="path_to_image",
                                dark_image="path_to_image",
                                width=width_in_px)

         label1 = ctk.CTkLabel(app, image=myimage)
         label2 = ctk.CTkLabel(app, image=myimage)


   .. tab-item:: Dict of arguments

      .. code:: python

         label = ctk.CTkLabel(app, image={"light_image": "path_to_image", "height": height_in_px})


   .. tab-item:: Tuple

      .. code:: python

         label1 = ctk.CTkLabel(app, image=("path_to_image", width_in_px, height_in_px))
         label2 = ctk.CTkLabel(app, image=("path_to_light_image", "path_to_dark_image", width_in_px, height_in_px))


   .. tab-item:: Custom Key

      .. code:: python

         ctk.ThemeManager.add_key("MyImage", light_image="path_to_image",
                                             dark_image="path_to_image",
                                             width=width_in_px)
         ...
         label1 = ctk.CTkLabel(app, image="MyImage")
         label2 = ctk.CTkLabel(app, image="MyImage")
         label3 = ctk.CTkLabel(app, image=ctk.CTkImage("MyImage", width=different_width))


In all cases, they will be converted to a ``CTkImage`` object that you can retrieve, reuse and update:

.. code:: python

   myimage = label.cget("image")

   newlabel = ctk.CTkLabel(app, image=myimage)

   myimage.configure(...)


.. tip::

   If you need to manage many images, for example, to add an icon to all buttons,
   you can store all paths in a JSON file:

   .. code:: json

      {
        "Image1": {
          "light_image": "path_to_light_image",
          "dark_image": "path_to_dark_image",
          "width": 20
        },
        "Image2": {
          "light_image": "path_to_image",
          "height": 30
        },
        "Image3": {

        }
      }

   Then, at the start of your program, you can import it:

   .. code:: python

      import customtkinter as ctk

      ctk.set_appearance_mode("light")
      ctk.set_default_color_theme("blue")
      ctk.add_color_theme("path_to_json")

   Finally, when you need to add an image, you can just reference it with its custom key name:

   .. code:: python

      label1 = ctk.CTkLabel(app, image="Image1")
      label2 = ctk.CTkLabel(app, image="Image2")


.. py:class:: CTkImage
   :hidden:

   .. _image_arguments:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/theme_key.rst

   Themed
   ~~~~~~

   .. py:attribute:: width
      :type: int
      :value: 0

      Width of the image in |unscaled pixels|.

      .. hint::
         Set it to ``0`` to use the image's original width,
         or use the proper value to preserve the aspect ratio.


   .. py:attribute:: height
      :type: int
      :value: 0

      Height of the image in |unscaled pixels|.

      .. hint::
         Set it to ``0`` to use the image's original height,
         or use the proper value to preserve the aspect ratio.


   .. py:attribute:: light_image
      :type: Image.Image | Path | str | None

      Image to be used when :doc:`/concepts/AppearanceMode` is Light.

      | It can be an instance of ``Image.Image``, a ``Path``, or a string representing a file path.
      | If a file path is provided, it is immediately opened using ``Image.open()``.

      .. note::
         If set to ``None`` or ``""``, :py:attr:`dark_image` is used instead.


   .. py:attribute:: dark_image
      :type: Image.Image | Path | str | None

      Image to be used when :doc:`/concepts/AppearanceMode` is Dark.

      | It can be an instance of ``Image.Image``, a ``Path``, or a string representing a file path.
      | If a file path is provided, it is immediately opened using ``Image.open()``.

      .. note::
         If set to ``None`` or ``""``, :py:attr:`light_image` is used instead.


   Methods
   -------

   .. py:method:: configure(**kwargs) -> None:

      Allows changing the value of 1 or more arguments.

      All widgets that use the same ``CTkImage`` object will update their image automatically.

      :param any kwargs:
         Name-Value pairs where the name is a |valid argument| and the value is an acceptable value for that argument.

      :raises ValueError:
         If an unsupported argument has been provided.

         If an unsupported type has been provided as a value for any of the "image" arguments.



   .. py:method:: cget(attribute_name) -> Any:

      Allows retrieving the current value of an image's argument by specifying its name as a string.

      :param str attribute_name:
         The name of a |valid argument|.

      :returns:
         The value of the requested argument.

      :raises ValueError:
         If an unknown argument name has been provided.



   .. py:method:: add_configure_callback(callback) -> None:

      Registers the provided function to be invoked
      when the :py:meth:`configure()` method is used.

      Widgets that receive this object as Image already use
      this method to register a callback that updates their
      content when the image is updated.

      :type callback: () -> None
      :param callback:
         Function to be added to the list of callbacks.



   .. py:method:: remove_configure_callback(callback) -> None:

      Unregisters the provided function so it will no longer be invoked
      when the :py:meth:`configure()` method is used.

      If ``callback`` was never registered using :py:meth:`add_configure_callback()`,
      nothing happens.

      :type callback: () -> None
      :param callback:
         Function to be removed from the list of callbacks.



.. |valid argument| replace:: `valid argument <Arguments_>`__
