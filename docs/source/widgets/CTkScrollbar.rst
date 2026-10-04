CTkScrollbar
============

.. image:: images/CTkScrollbar.png
   :alt: CTkScrollbar examples
   :align: center
   :height: 80px

The ``CTkScrollbar`` widget is used to control the visible portion
of another scrollable widget.

Other widgets already include this one, but you can always
instantiate your own widget and link it to them.


Example Code
------------

Create a :doc:`/widgets/CTkTextbox` with external scrollbar:

.. code:: python

   app = ctk.CTk()
   app.grid_rowconfigure(0, weight=1)
   app.grid_columnconfigure(0, weight=1)

   # create scrollable textbox
   textbox = ctk.CTkTextbox(app, show_scrollbars=False)
   textbox.grid(row=0, column=0, sticky="nsew")

   # create scrollbar
   scrollbar = ctk.CTkScrollbar(app, command=textbox.yview)
   scrollbar.grid(row=0, column=1, sticky="ns")

   # connect textbox scroll event to the scrollbar
   textbox.configure(yscrollcommand=scrollbar.set)

   app.mainloop()


.. py:class:: CTkScrollbar
   :hidden:

   .. _scrollbar_arguments:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/master.rst
   .. include:: /arguments/theme_key.rst

   Functionality
   ~~~~~~~~~~~~~

   .. py:attribute:: scrollincrement
      :type: int | float
      :value: 1.0

      Multiplier factor used to scale the amount by which values should change when scrolling the widget.

      The unit of measurement depends on the linked widget.

   .. py:attribute:: command
      :type: ((str, int | float, str) -> None) | None
      :value: None

      | Function that is invoked when the user manipulates the widget.
      | It is usually assigned with the ``xview()`` or ``yview()`` method of the widget you want to control with the scrollbar.

      For a detailed explanation of the arguments the function receives,
      check out the :tkdoc:`Tkinter documentation <scrollbar-callback>`.

   Themed
   ~~~~~~

   .. include:: /arguments/thicknesslength.rst

   .. py:attribute:: minimum_pixel_length
      :type: int

      Minimum Slider Button length in |unscaled pixels|.

      If the values to be displayed require a Slider Button length smaller than this value,
      the button is stretched to have at least this length.

   .. include:: /arguments/corner_radius.rst
   .. include:: /arguments/border_width.rst
   .. include:: /arguments/bg_color.rst
   .. include:: /arguments/fg_color.rst
   .. include:: /arguments/button_color.rst
   .. include:: /arguments/button_hover_color.rst
   .. include:: /arguments/border_color.rst
   .. include:: /arguments/hover.rst


   Methods
   -------

   .. py:method:: get() -> tuple[float, float]:

      Returns the current displayed values as percentages of the available space.

      :returns:
         A tuple containing starting and ending values as percentages.



   .. py:method:: set(start_value, end_value) -> None:

      Allows changing the displayed values.

      This method is usually assigned to the ``xscrollcommand`` or ``yscrollcommand`` attribute
      of the widget you want to control with the scrollbar.

      :param float start_value:
         Starting position at which the Slider Button will be drawn, as a percentage of the available space.

      :param float end_value:
         Ending position at which the Slider Button will be drawn, as a percentage of the available space.



   .. _view_methods:

   .. py:method:: view() -> tuple[float, float]:
   .. py:method:: view("moveto", fraction) -> None:
      :no-index:
   .. py:method:: view("scroll", number, what) -> None:
      :no-index:

      Allows managing the scrollbar by performing different actions based on the value and number of provided parameters:

      - No parameters:
         Returns the current displayed values as percentages of the available space, just like :py:meth:`get()`.
      - ``"moveto"`` as first parameter and 1 additional argument:
         Moves the starting value to the provided ``fraction`` parameter and updates the ending
         value so as to preserve the original difference between the two values.
      - ``"scroll"`` as first parameter and 2 additional arguments:
         Changes both starting and ending values by the same quantity, which depends on ``number`` and ``what``.

      It is suggested to use this method instead of the linked widget's method so that
      :py:attr:`scrollincrement` is actually applied.

      :param float fraction:
         New value to be used as the starting value.

      :param int number:
         Number used to calculate the amount by which the values will be updated.

      :type what: 'units' | 'pages'
      :param what:
         Used to interpret the value provided with the ``number`` parameter.

      :returns:
         A tuple containing starting and ending values as percentages (if invoked without parameters).



   .. py:method:: view_moveto(fraction) -> None:

      Syntactic sugar for :py:meth:`view()` invoked with ``"moveto"`` as first parameter.



   .. py:method:: view_scroll(number, what) -> None:

      Syntactic sugar for :py:meth:`view()` invoked with ``"scroll"`` as first parameter.

   Inherited
   ~~~~~~~~~

   .. include:: /methods/widget.rst
   .. include:: /methods/geometry_manager.rst
