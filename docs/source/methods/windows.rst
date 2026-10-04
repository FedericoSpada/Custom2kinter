.. py:method:: geometry([geometry_string][, apply_scaling]) -> str | None:

   Sets or gets the window geometry (sizes and position).

   If ``apply_scaling`` is ``True`` (the default), the values are considered in |unscaled pixels|;
   otherwise, no scaling factor is applied and the values are applied or returned as they are.

   :type geometry_string: str | None
   :param geometry_string:
      | Window geometry to be applied.
      | Check out the :tkdoc:`Tkinter documentation <geometry>` for the syntax.

      Do not provide this parameter or set it to ``None`` if you want to retrieve the current geometry values.

   :param bool apply_scaling:
      If set to ``False``, the geometry strings will be considered already scaled,
      so they will be used/returned as they are, without applying any
      :doc:`Scaling Factor </concepts/Scaling>`.

   :returns:
      The current window geometry if ``geometry_string`` is not provided.



.. py:method:: wm_iconphoto(default, *images) -> None:

   Sets the window icon to the provided image.

   If ``default`` is ``True``, the change will affect ALL past and future windows for which ``wm_iconphoto()``
   wasn't called or was called with ``default=True``.

   If ``default`` is ``False``, the change will affect only this window, and the icon won't change unless
   you call this method again.

   You can provide many pre-scaled images, but usually 1 is just fine.

   :param bool default:
      Allows applying the change to all windows, even those that will be created later.

   :param CTkImage images:
      Image to be used as icon.

      If the provided :doc:`/utilities/CTkImage` object has 2 images,
      one is applied in Light mode and the other for Dark mode.



.. py:method:: destroy() -> None:

   Hides the window if displayed and destroys it, so that it can never be shown again.

   .. note::
      The system automatically destroys contained widgets recursively.



.. py:method:: configure(**kwargs) -> None:

   Allows changing the value of 1 or more arguments after the widget has been created.

   :param any kwargs:
      Name-Value pairs where the name is a |valid argument| and the value is an acceptable value for that argument.

   :raises ValueError:
      If an unsupported argument has been provided.

      If an invalid color has been provided as a value for any of the arguments.



.. py:method:: cget(attribute_name) -> Any:

   Allows retrieving the current value of a widget's argument by specifying its name as a string.

   :param str attribute_name:
      The name of a |valid argument|.

   :returns:
      The value of the requested argument.

   :raises ValueError:
      If an unknown argument name has been provided.



.. py:method:: withdraw() -> None:
.. py:method:: iconify() -> None:
.. py:method:: deiconify() -> None:
.. py:method:: lift([aboveThis]) -> None:
.. py:method:: lower([belowThis]) -> None:
.. py:method:: minsize([width][, height]) -> None:
.. py:method:: maxsize([width][, height]) -> None:
.. py:method:: resizable([width][, height]) ->  tuple[bool, bool] | None:

   Inherited methods from ``tkinter.Toplevel`` widget.

   Check out the :tkdoc:`Tkinter documentation <toplevel>` for their explanation.



.. |valid argument| replace:: `valid argument <Arguments_>`__
