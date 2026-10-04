.. py:attribute:: title
   :type: str | Iterable[str] | (() -> (str | Iterable[str])) | None
   :value: None
.. py:attribute:: text
   :type: str | Iterable[str] | (() -> (str | Iterable[str])) | None
   :value: None

   Strings to be displayed in the :doc:`/widgets/CTkLabel` nested widgets
   (the title one is **bold**).

   Each one can be:

   - ``str``: value used as is;
   - iterable of ``str``: they are combined by separating them with ``\n``;
   - function returning the above: it is invoked every time the widget is about to be shown;
   - ``None``: the label is not mapped.

   .. note::
      If the widget content is entirely determined by callbacks, and they return ``""``,
      the widget is not shown (like if :py:attr:`pre_command` returned ``"break"``)
