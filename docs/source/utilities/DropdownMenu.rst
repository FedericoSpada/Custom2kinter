DropdownMenu
============

``DropdownMenu`` is a popup menu that displays a list of selectable string values
and invokes a callback with the selected value.

It is a lower-level utility, not a stand-alone widget, so it can be used inside other widgets
to spawn a menu, like :doc:`/widgets/CTkOptionMenu` and :doc:`/widgets/CTkComboBox`.


.. py:class:: DropdownMenu
   :hidden:

   .. _dropdownmenu_arguments:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/master_window.rst

   Functionality
   ~~~~~~~~~~~~~

   .. py:attribute:: values
      :type: list[str]
      :value: []

      List of strings to be displayed.


   .. py:attribute:: command
      :type: ((str) -> None) | None
      :value: None

      Function that is invoked when the user clicks on a value.
      It receives the selected value as its only parameter.

   Themed
   ~~~~~~

   .. include:: /arguments/fg_color.rst
   .. include:: /arguments/hover_color.rst
   .. include:: /arguments/text_color.rst

   .. py:attribute:: min_character_width
      :type: int

      Minimum number of characters shown.

      This determines the width of the Menu.

   .. include:: /arguments/font.rst

   Inherited
   ~~~~~~~~~

   .. py:attribute:: postcommand
      :type: str | (() -> None)
   .. py:attribute:: selectcolor
      :type: str
   .. py:attribute:: takefocus
      :type: bool

      Inherited attributes from ``tkinter.Menu`` widget.

      Check out the :tkdoc:`Tkinter documentation <menu>` for their explanation.


   Methods
   -------

   .. py:method:: open(x, y) -> None:

      Shows the Menu in the position where the top-left corner is exactly
      at ``(x, y)`` coordinates with respect to the screen.

      If the Menu is already visible, its position is updated.

      :param int x:
         Horizontal coordinate where to place the Menu.

         In a single-screen setup, ``0`` is the **left** border,
         and the maximum value depends on the screen resolution.

      :param int y:
         Vertical coordinate where to place the widget.

         In a single-screen setup, ``0`` is the **top** border,
         and the maximum value depends on the screen resolution.



   .. py:method:: close() -> None:

      Hides the Menu.

      It can be shown again using :py:meth:`open()`.



   .. py:method:: is_open() -> bool:

      Returns whether the Menu is currently displayed.

      :returns:
         ``True`` if the Menu is visible, ``False`` otherwise.



   .. py:method:: destroy() -> None:

      Hides the Menu if displayed and destroys it, so that it can never be shown again.



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



.. |valid argument| replace:: `valid argument <Arguments_>`__
