.. py:method:: configure([require_redraw], **kwargs) -> None:

   Allows changing the value of 1 or more arguments after the widget has been created.

   :param bool require_redraw:
      If set to ``True``, force the redraw of the widget.

      Some of the arguments change it to ``True`` automatically.

   :param any kwargs:
      Name-Value pairs where the name is a |valid argument| and the value is an acceptable value for that argument.

   :raises ValueError:
      If an unsupported argument has been provided.

      If an invalid color has been provided as a value for any of the arguments.



.. py:method:: cget(attribute_name) -> Any:

   Allows retrieving the current value of a widget's argument by specifying its name as a string.

   | If the widget has a nested widget, you can retrieve its values by prefixing the desired argument with this widget's argument name that is used to configure the nested widget.
   | For example, ``cget("dropdown_fg_color")`` will return the ``fg_color`` of the ``dropdown``.

   :param str attribute_name:
      The name of a |valid argument|.

   :returns:
      The value of the requested argument.

   :raises ValueError:
      If an unknown argument name has been provided.



.. py:method:: destroy() -> None:

   Hides the widget if displayed and destroys it, so that it can never be shown again.



.. py:method:: bind(sequence, func) -> str | tuple[str, ...]:

   Setup a function to be invoked when specific events take place, like the user hovers
   the widget with the mouse, right-clicks it or the widget is shown or hidden.

   :param str sequence:
      String that describes the event that will trigger the provided function.

      For a complete explanation of the semantics, check out the |semantics documentation|.

   :type func: (tkinter.Event) -> None
   :param func:
      Callable object that will be invoked when the event takes place.

      The function will be invoked by passing to it a :tkdoc:`tkinter.Event <event-handlers>`
      object containing additional information.

   :returns:
      An ID that can be passed to :py:meth:`unbind()` to remove the association event-function.



.. py:method:: unbind(sequence[, funcid]) -> None:

   Deletes the bindings created via :py:meth:`bind()` for the event described by ``sequence``.

   If the second argument is provided, just that callback is removed; otherwise, all callbacks
   associated to that event are deleted.

   :param str sequence:
      String that describes the event that will trigger the provided function.

      For a complete explanation of the semantics, check out the |semantics documentation|.

   :type funcid: str | tuple[str, ...] | None
   :param funcid:
      Value returned by :py:meth:`bind()` to remove just a specific callback.
      If omitted, all bindings will be deleted.



.. |valid argument| replace:: `valid argument <Arguments_>`__
.. |semantics documentation| replace:: :tkdoc:`Tkinter documentation <event-sequences>`
