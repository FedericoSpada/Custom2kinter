.. py:method:: open(x_root, y_root[, anchor]) -> None:

   Shows the widget in the position where the corner provided with ``anchor``
   is exactly at ``(x_root, y_root)`` coordinates with respect to the screen.

   If the widget is already visible, its position is updated.

   :param int x_root:
      Horizontal coordinate where to place the widget.

      In a single-screen setup, ``0`` is the **left** border,
      and the maximum value depends on the screen resolution.

   :param int y_root:
      Vertical coordinate where to place the widget.

      In a single-screen setup, ``0`` is the **top** border,
      and the maximum value depends on the screen resolution.

   :type anchor: 'center' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w' | 'nw'
   :param anchor:
      It controls the point of the widget that will be placed at the provided coordinates.

      ``"center"`` refers to the middle of the widget, ``"n"`` is the middle of the top border,
      and ``"sw"`` is the bottom-left corner.



.. py:method:: is_open() -> bool:

   Returns whether the widget is currently displayed.

   :returns:
      ``True`` if the widget is visible, ``False`` otherwise.



.. py:method:: update_dimensions() -> None:

   If new widgets are added at a later moment, after the widget has already been opened at least once,
   it's better to call this method to force an update of the dimensions.
