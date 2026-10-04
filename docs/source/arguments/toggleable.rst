.. py:attribute:: onvalue
   :type: int | float | str | bool
   :value: True

   Value returned by :py:meth:`get()` or assigned to :py:attr:`variable` when
   the widget is in the "on" internal state.


.. py:attribute:: offvalue
   :type: int | float | str | bool
   :value: False

   Value returned by :py:meth:`get()` or assigned to :py:attr:`variable` when
   the widget is in the "off" internal state.


.. py:attribute:: variable
   :type: IntVar | DoubleVar | StringVar | BooleanVar | None
   :value: None

   Allows linking this widget to an ``IntVar``, ``DoubleVar``, ``StringVar`` or ``BooleanVar`` object
   that can be shared among many widgets.

   |variable_description|


.. py:attribute:: pre_command
   :type: ((int | float | str | bool) -> ('break' | None)) | None
   :value: None

   Function that is invoked when the user clicks on the widget,
   but **before** the widget changes the "on"/"off" internal state.
   It receives the new potential value as its only parameter.

   If the function returns exactly ``"break"``, the state change is not performed
   and :py:attr:`command` is not invoked at all.


.. py:attribute:: command
   :type: ((int | float | str | bool) -> None) | None
   :value: None

   Function that is invoked when the user clicks on the widget,
   but **after** the widget changed the "on"/"off" internal state.
   It receives the new value as its only parameter.

   If the function specified by :py:attr:`pre_command` returned ``"break"``,
   this function is not invoked.
