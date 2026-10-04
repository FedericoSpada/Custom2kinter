.. py:attribute:: top_fg_color
   :type: str | tuple[str, str]

   | Replaces :py:attr:`fg_color` if this widget is placed on a :doc:`Container </containers/index>` with the exact same main color.
   | This keeps the widget boundaries clear.

   If only :py:attr:`fg_color` is explicitly provided during the widget declaration
   or ``fg_color=="transparent"``, this argument is ignored.
