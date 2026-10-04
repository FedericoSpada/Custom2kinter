.. py:method:: see(widget) -> None:

   Scrolls the frame so that the provided ``widget`` is visible.

   .. warning::
      The widget must be a child or grandchild of the frame, otherwise ``ValueError`` is raised.

   :param CTkWidget widget:
      Widget you want to be sure is currently visible.

   :raises ValueError:
      If the widget is not a child or grandchild of the frame.



.. py:method:: is_visible(widget) -> bool:

   | Returns whether the provided ``widget`` is **fully** visible.
   | If the widget size is bigger than the frame itself, this method will always return ``False``.

   .. warning::
      The widget must be a child or grandchild of the frame, otherwise ``ValueError`` is raised.

   :param CTkWidget widget:
      Widget whose visibility status you want to know.

   :returns:
      ``True`` if ``widget`` is entirely visible at the moment.

   :raises ValueError:
      If the widget is not a child or grandchild of the frame.



.. py:method:: xview(...) -> None:
.. py:method:: xview_moveto(fraction) -> None:
.. py:method:: xview_scroll(number, what) -> None:
.. py:method:: yview(...) -> None:
.. py:method:: yview_moveto(fraction) -> None:
.. py:method:: yview_scroll(number, what) -> None:

   Allows managing the visible part of the canvas.

   They remap the ``CTkScrollbar`` :ref:`methods <view_methods>` in ``x`` and ``y`` directions.

   .. hint::
      You can assign them to the ``command`` attribute of an external Scrollbar.
