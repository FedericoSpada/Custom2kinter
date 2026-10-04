.. py:attribute:: width
   :type: int

   Width of the widget in |unscaled pixels|.

   If the geometry manager used to display the widget has been configured to stretch it, this value is ignored.

   Moreover, when a widget is placed inside this widget using ``pack()`` or ``grid()``,
   by default, the container collapses to fit the space occupied by its children, so this argument has no effect.
   To force the provided dimensions, you have to invoke ``.pack_propagate(False)`` or ``.grid_propagate(False)``.


.. py:attribute:: height
   :type: int

   Height of the widget in |unscaled pixels|.

   If the geometry manager used to display the widget has been configured to stretch it, this value is ignored.

   Moreover, when a widget is placed inside this widget using ``pack()`` or ``grid()``,
   by default, the container collapses to fit the space occupied by its children, so this argument has no effect.
   To force the provided dimensions, you have to invoke ``.pack_propagate(False)`` or ``.grid_propagate(False)``.
