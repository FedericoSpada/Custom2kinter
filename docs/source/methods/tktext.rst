.. py:method:: get(index1[, index2]) -> str:

   Returns the widget's content between 2 specified character indexes.

   :type index1: str | float
   :param index1:
      First character index that will be present in the returned value.

      Check out the |character index doc| for admissible values.

   :type index2: str | float | None
   :param index2:
      First character index that will NOT be present in the returned value.

      Check out the |character index doc| for admissible values.

   :returns:
      Text in the widget present between the specified indexes.


.. py:method:: delete(index1[, index2]) -> None:

   Deletes the widget's content between 2 specified character indexes.

   :type index1: str | float
   :param index1:
      First character index that will be deleted.

      Check out the |character index doc| for admissible values.

   :type index2: str | float | None
   :param index2:
      First character index that will NOT be deleted.

      Check out the |character index doc| for admissible values.



.. py:method:: insert(index, chars, ...) -> None:

   Insert the ``chars`` value at the provided character index.

   :type index: str | float
   :param index:
      Character index at which the string will be inserted.

      Check out the |character index doc| for admissible values.

   :param str chars:
      Text to be placed at the provided index.



.. py:method:: bbox(index) -> tuple[int, int, int, int] | None:
.. py:method:: compare(index1, op, index2) -> bool:
.. py:method:: dlineinfo(index) -> tuple[int, int, int, int, int] | None:
.. py:method:: edit_modified(arg) -> bool:
.. py:method:: edit_redo() -> None:
.. py:method:: edit_reset() -> None:
.. py:method:: edit_separator() -> None:
.. py:method:: edit_undo() -> None:
.. py:method:: index(index) -> str:
.. py:method:: mark_gravity(mark, gravity) -> Literal["left", "right"] | None:
.. py:method:: mark_names() -> tuple[str, ...]:
.. py:method:: mark_next(index) -> str | None:
.. py:method:: mark_previous(index) -> str | None:
.. py:method:: mark_set(mark, index) -> None:
.. py:method:: mark_unset(*marks) -> None:
.. py:method:: scan_dragto(x, y) -> None:
.. py:method:: scan_mark(x, y) -> None:
.. py:method:: search(pattern, index, ...) -> str:
.. py:method:: see(index) -> None:
.. py:method:: tag_add(tagName, index1, index2) -> None:
.. py:method:: tag_bind(tagName, sequence, func, add) -> str:
.. py:method:: tag_unbind(tagName, sequence, funcid) -> None:
.. py:method:: tag_cget(tagName, option) -> Any:
.. py:method:: tag_configure(tagName, **kwargs) -> Any:
.. py:method:: tag_delete(*tagNames) -> None:
.. py:method:: tag_lower(tagName, belowThis) -> None:
.. py:method:: tag_raise(tagName, aboveThis) -> None:
.. py:method:: tag_names(index) -> tuple[str, ...]:
.. py:method:: tag_nextrange(tagName, index1, index2) -> tuple[str, str]:
.. py:method:: tag_prevrange(tagName, index1, index2) -> tuple[str, str]:
.. py:method:: tag_ranges(tagName) -> tuple[str, ...]:
.. py:method:: tag_remove(tagName, index1, index2) -> None:
.. py:method:: xview(...) -> None:
.. py:method:: xview_moveto(fraction) -> None:
.. py:method:: xview_scroll(number, what) -> None:
.. py:method:: yview(...) -> None:
.. py:method:: yview_moveto(fraction) -> None:
.. py:method:: yview_scroll(number, what) -> None:

   Inherited methods from ``tkinter.Text`` widget.

   Check out the :tkdoc:`Tkinter documentation <text-methods>` for their explanation.



.. |character index doc| replace:: :tkdoc:`Tkinter documentation <text-index>`
