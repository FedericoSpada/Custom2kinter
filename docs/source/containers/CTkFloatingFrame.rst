CTkFloatingFrame
================

The ``CTkFloatingFrame`` widget is a frame-like container that
you can open, close, and position independently on the screen.

This is the parent class that is used by other widgets,
like :doc:`/widgets/CTkToast` and :doc:`/widgets/CTkToolTip`,
and it can be inherited to create custom widgets that need to
always stay on top of every window.

If you want to create a normal window with a title bar and minimize
and close buttons, use :doc:`/containers/CTkToplevel` instead.


Example Code
------------

.. tab-set::

   .. tab-item:: Functional approach

      .. code:: python

         frame = ctk.CTkFloatingFrame()

         def button_callback() -> None:
             print("button click")

         # add widgets to frame
         button = ctk.CTkButton(frame, command=button_callback)
         button.pack()

         #show the frame
         frame.open(x, y, anchor)


   .. tab-item:: OOP approach

      .. code:: python

         class CustomFrame(ctk.CTkFloatingFrame):
             def __init__(self, **kwargs) -> None:
                 super().__init__(**kwargs)

                 # add widgets to frame
                 self.button = ctk.CTkButton(self, command=self.button_callback)
                 self.button.pack()

             def button_callback(self) -> None:
                 print("button click")

         # show the frame
         frame = CustomFrame()
         frame.open(x, y, anchor)


.. py:class:: CTkFloatingFrame
   :hidden:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/master_window.rst
   .. include:: /arguments/theme_key.rst

   Themed
   ~~~~~~

   .. include:: /arguments/widtheight_container.rst
   .. include:: /arguments/corner_radius.rst
   .. include:: /arguments/border_width.rst
   .. include:: /arguments/fg_color.rst
   .. include:: /arguments/border_color.rst
   .. include:: /arguments/transparency.rst

   Class attributes
   ~~~~~~~~~~~~~~~~

   |class_attributes_description|

   .. py:attribute:: transparent_color
      :type: str | tuple[str, str]

      The widget is configured to make every child part that has this
      exact color fully transparent.

      This allows having rounded corners by using this color as ``bg_color``.
      You can also reuse this color for other children to create a passthrough effect.

      .. hint::
         If you need to use exactly the default colors used for this
         attribute inside any ``CTkFloatingFrame``, change this attribute
         to a color that you never use.


   Methods
   -------

   .. include:: /methods/floatingframe.rst

   .. py:method:: close() -> None:

      Hides the widget.

      It can be shown again using :py:meth:`open()`.

   Inherited
   ~~~~~~~~~

   .. include:: /methods/widget.rst
