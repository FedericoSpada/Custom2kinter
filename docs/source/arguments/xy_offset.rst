.. py:attribute:: x_offset
   :type: int
.. py:attribute:: y_offset
   :type: int

   Allows slightly changing the position of the widget with respect to the one imposed by :py:attr:`anchor`.

   ``x_offset`` will distance the widget horizontally, while ``y_offset`` will distance it vertically.

   .. note::
      The actual direction depends on :py:attr:`anchor` itself,
      so a **positive** value always moves the widget away from the anchor point.
