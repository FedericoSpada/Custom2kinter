.. py:method:: delete(first_index[, last_index]) -> None:

   Deletes the widget's content between 2 specified character indexes.

   :type first_index: str | int
   :param first_index:
      First character index that will be deleted.

      Check out the |character index doc| for admissible values.

   :type last_index: str | int | None
   :param last_index:
      First character index that will NOT be deleted.

      Check out the |character index doc| for admissible values.



.. py:method:: insert(index, string) -> None:

   Insert the ``string`` value at the provided character index.

   :type index: str | int
   :param index:
      Character index at which the string will be inserted.

      Check out the |character index doc| for admissible values.

   :param str string:
      Text to be placed at the provided index.



.. py:method:: cursor_index(index) -> int:
.. py:method:: icursor(index) -> None:
.. py:method:: selection_adjust(index) -> None:
.. py:method:: selection_clear() -> None:
.. py:method:: selection_from(index) -> None:
.. py:method:: selection_present() -> bool:
.. py:method:: selection_range(start, end) -> None:
.. py:method:: selection_to(index) -> None:
.. py:method:: xview(...) -> None:
.. py:method:: xview_moveto(fraction) -> None:
.. py:method:: xview_scroll(number, what) -> None:

   Inherited methods from ``tkinter.Entry`` widget.

   Check out the :tkdoc:`Tkinter documentation <entry>` for their explanation.



.. |character index doc| replace:: `Tkinter documentation <https://tkdocs.com/shipman/entry.html#entry-index>`__
