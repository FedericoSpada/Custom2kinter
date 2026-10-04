Configuration
=============

The following functions can be invoked on the Library itself
to configure its general appearance or retrieve basic info.

Here is a set of instructions that should always be present at the start of the program
(of course, you can customize them):

.. code:: python

   import customtkinter as ctk

   ctk.set_appearance_mode("system")
   ctk.set_default_color_theme("blue")


Appearance Mode
---------------

.. py:function:: set_appearance_mode(mode) -> None:

   Changes the :doc:`/concepts/AppearanceMode` for all windows and widgets.

   :type mode: 'light' | 'dark' | 'system'
   :param mode:
      If ``"light"`` or ``"dark"`` is used, the mode will be forced to the provided value.

      If ``"system"`` is used, the actual mode depends on the mode of the computer,
      and it will also change automatically if the computer's mode changes.



.. py:function:: get_appearance_mode() -> 'light' | 'dark':

   Returns the actual :doc:`/concepts/AppearanceMode` currently active,
   even if ``"system"`` has been used.

   :returns:
      The current mode between ``"light"`` and ``"dark"``.


Scaling
-------

.. py:function:: set_widget_scaling(scaling_value) -> None:

   Adds an additional scaling factor for all widgets
   on top of the one described in :doc:`/concepts/Scaling`.

   It can be used to zoom in or out of all widgets at once.

   :param float scaling_value:
      Scaling factor to be applied (min ``0.4``).



.. py:function:: get_widget_scaling() -> float:

   Returns the value previously provided with :py:func:`set_widget_scaling()`.

   :returns:
      The current additional scaling factor for the widgets.



.. py:function:: set_window_scaling(scaling_value) -> None:

   Adds an additional scaling factor for all windows
   on top of the one described in :doc:`/concepts/Scaling`.

   It can be used to zoom in or out of all windows at once.

   :param float scaling_value:
      Scaling factor to be applied (min ``0.4``).



.. py:function:: get_window_scaling() -> float:

   Returns the value previously provided with :py:func:`set_window_scaling()`.

   :returns:
      The current additional scaling factor for the windows.



.. py:function:: deactivate_automatic_dpi_awareness() -> None:

   Deactivates DPI awareness of current process,
   forcing the :doc:`Scaling Factor </concepts/Scaling>` to be ``1.0``.


Theme
-----

.. py:function:: set_default_color_theme(theme_name_or_path) -> None:

   Opens a JSON file to be used to retrieve the settings for **all** widgets.

   It replaces any previously open file.
   To extend the theme with new custom keys, use :py:func:`add_color_theme()`.

   :param str theme_name_or_path:
      It can be a built-in theme name, or it must be a path to a **complete** JSON file.

   :raises FileNotFoundError:
      If the file doesn't exist.

      If the built-in themes are not in the expected folder.

   :raises ValueError:
      If a key reference could not be resolved.



.. py:function:: add_color_theme(theme_path) -> None:

   Opens a JSON file to extend or modify the existing keys,
   which are used to retrieve the settings for the widgets.

   :param str theme_path:
      Path to the JSON file.

   :raises FileNotFoundError:
      If the file doesn't exist.

   :raises ValueError:
      If a key reference could not be resolved.



.. py:function:: ThemeManager.add_key(custom_key, **kwargs) -> None:

   Adds a **new** key to the theme, with the settings provided as name-value pairs.

   :param str custom_key:
      Name of the key to be used later to reference the provided settings.

   :param Any kwargs:
      Name-Value pairs that will be associated to the custom key name.

   :raises KeyError:
      If ``custom_key`` is already used.



.. py:function:: ThemeManager.update_key(key, **kwargs) -> None:

   Updates an **existing** theme key, with the settings provided as name-value pairs.

   :param str key:
      Name of the key to be updated.

   :param Any kwargs:
      Name-Value pairs that will used.

   :raises KeyError:
      If ``key`` doesn't exist.



.. py:function:: ThemeManager.get_info(default_key[, custom_key][, **kwargs]) -> dict[str, Any]:

   Returns a dict of Name-Value pairs with the settings associated with the provided keys.

   The output dict is initialized with the settings associated with ``default_key``.
   Then, it is deeply updated with the values of the ``custom_key`` (if not ``None``).
   This last one doesn't need to contain all possible Names: it updates just the one it contains.
   Finally, if Name-Value pairs have been provided as additional arguments,
   they are used to update the returned dict.

   This function is used by all widgets to retrieve the value for their arguments.
   They use the name of their class as ``default_key``.
   ``custom_key`` is instead a positional argument,
   and ``kwargs`` are the arguments you provide to the constructor.

   It can be used directly to retrieve other data you wanted to store in a JSON file
   or to create custom widgets.

   :param str default_key:
      Key that should contain all possible Name-Value pairs.

   :type custom_key: str | None
   :param custom_key:
      If not ``None``, Key that can contain a subset of all possible Name-Value pairs.

   :param Any kwargs:
      Additional Name-Value pairs used to update the returned dict.

   :returns:
      A dict of Name-Value pairs.

   :raises KeyError:
      If ``default_key`` or ``custom_key`` are not found.



.. py:function:: ThemeManager.save_theme([path]) -> None:

   Saves the current theme settings in a JSON file.

   The file can be later restored using :py:func:`set_default_color_theme()` or :py:func:`add_color_theme()`.

   :type path: str | None
   :param path:
      Path of the JSON file to be overwritten.

      It can be omitted if you have previously loaded a custom JSON file.

   :raises ValueError:
      If there are no theme settings.

      If ``path`` is not provided and a custom JSON file was never loaded.
