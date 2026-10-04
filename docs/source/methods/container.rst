.. py:method:: winfo_children() -> list[tkinter.Widget]:

   Returns a list of all Widgets which are children of this widget.

   :returns:
      A list of ``tkinter.Widget``.



.. py:method:: get_fg_color() -> str | tuple[str, str]:

   | Returns the actual main color of the widget.
   | If the requested color is ``"transparent"``, it returns the "actual main color" of its parent.

   It is mainly used by children widgets to transform their ``"transparent"`` color into true colors.

   :returns:
      The displayed main color of the widget.
