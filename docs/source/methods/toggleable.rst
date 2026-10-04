.. py:method:: get() -> int | float | str | bool:

   Returns the current value of the widget.

   :returns:
      :py:attr:`onvalue` or :py:attr:`offvalue` based on the internal state.



.. py:method:: set(value | state) -> None:

   Allows changing the internal state programmatically by providing
   either one of :py:attr:`onvalue` or :py:attr:`offvalue`,
   or a boolean state where ``True`` is "on" and ``False`` is "off".

   The change is performed regardless of the widget's :py:attr:`state`.

   |no_callbacks|

   :type value: int | float | str | bool | None
   :param value:
      The new internal state will be "on" if this parameter is equal to :py:attr:`onvalue`, "off" otherwise.

      Do not provide this parameter or set it to ``None`` if you want to use the ``state`` parameter.

   :type state: bool | None
   :param state:
      The new internal state will be "on" if this parameter is ``True``, "off" otherwise.



.. py:method:: select() -> None:

   Syntactic sugar for :py:meth:`set()` invoked with ``state=True``.



.. py:method:: deselect() -> None:

   Syntactic sugar for :py:meth:`set()` invoked with ``state=False``.



.. py:method:: invoke() -> None:

   Toggles the internal status between "on" and "off"
   if the widget's :py:attr:`state` is not ``"disabled"``
   and the :py:attr:`pre_command` doesn't return ``"break"``.

   It can be called to simulate the user who clicks on the widget.
