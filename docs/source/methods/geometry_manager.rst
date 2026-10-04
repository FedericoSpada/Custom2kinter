.. py:method:: pack([apply_scaling][, ...]) -> None:

   Displays the widget within its parent, attached to the previous widget that was displayed using the same method.

   .. tip::
      This is the best geometry manager when no special disposition is required,
      but you just want to show multiple widgets side by side, both vertically and horizontally.

   :param bool apply_scaling:
      |apply_scaling_description|

   :param ...:
      A complete description of all parameters can be found in the :tcldoc:`Tkinter documentation <pack>`.



.. py:method:: grid([apply_scaling][, ...]) -> None:

   Displays the widget within its parent using a grid layout.

   .. tip::
      It allows you to display widgets perfectly aligned in multiple rows and columns.

   :param bool apply_scaling:
      |apply_scaling_description|

   :param ...:
      A complete description of all parameters can be found in the :tcldoc:`Tkinter documentation <grid>`.



.. py:method:: place([apply_scaling][, ...]) -> None:

   Displays the widget within its parent at a specific position, either absolutely or relative to the available space.

   .. tip::
      This geometry manager allows you to position a widget exactly where you want.

   :param bool apply_scaling:
      |apply_scaling_description|

   :param ...:
      A complete description of all parameters can be found in the :tcldoc:`Tkinter documentation <place>`.



.. |apply_scaling_description| replace::
   If set to ``False``, all other parameters will be considered already scaled, so they will be used as they are,
   without applying any :doc:`Scaling Factor </concepts/Scaling>`.
