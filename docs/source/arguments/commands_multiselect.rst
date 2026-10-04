.. py:attribute:: pre_command
   :type: ((str) -> ('break' | None)) | None
   :value: None

   Function that is invoked when the user selects a new value,
   but **before** the widget content is actually changed.
   It receives the selected value as its only parameter.

   If the function returns exactly ``"break"``, the content is not changed
   and :py:attr:`command` is not invoked at all.


.. py:attribute:: command
   :type: ((str) -> None) | None
   :value: None

   Function that is invoked when the user selects a new value,
   but **after** the widget content has been changed.
   It receives the selected value as its only parameter.

   If the function specified by :py:attr:`pre_command` returned ``"break"``,
   this function is not invoked.
