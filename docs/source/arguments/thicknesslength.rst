.. py:attribute:: orientation
   :type: 'horizontal' | 'vertical'

   Specifies how to convert :py:attr:`thickness` and :py:attr:`length` in ``width`` and ``height``.


.. py:attribute:: thickness
   :type: int

   | Thickness of the widget in |unscaled pixels|.
   | It is used as the ``width`` or ``height`` of the widget based on :py:attr:`orientation`.

   If the geometry manager used to display the widget has been configured to stretch it, this value is ignored.


.. py:attribute:: length
   :type: int

   | Length of the widget in |unscaled pixels|.
   | It is used as the ``width`` or ``height`` of the widget based on :py:attr:`orientation`.

   If the geometry manager used to display the widget has been configured to stretch it, this value is ignored.
