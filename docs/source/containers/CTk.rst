CTk
===

The ``CTk`` class forms the basis of any CustomTkinter program; it creates the main app window.
During the runtime of a program, there must only be one instance of this class with a
single call of the :py:meth:`mainloop()` method, which starts the app.

Additional windows can be created using :doc:`/containers/CTkToplevel`.


Example Code
------------

.. tab-set::

   .. tab-item:: Functional approach

      .. code:: python

         app = ctk.CTk(title="CTk")
         app.geometry("600x500")

         def button_callback() -> None:
             print("button click")

         # add widgets to app
         button = ctk.CTkButton(app, command=button_callback)
         button.pack()

         # run the app
         app.mainloop()


   .. tab-item:: OOP approach

      .. code:: python

         class App(ctk.CTk):
             def __init__(self) -> None:
                 super().__init__(title="CTk")
                 self.geometry("600x500")

                 # add widgets to app
                 self.button = ctk.CTkButton(self, command=self.button_callback)
                 self.button.pack()

             def button_callback(self) -> None:
                 print("button click")

         # run the app
         app = App()
         app.mainloop()


.. py:class:: CTk
   :hidden:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/theme_key.rst

   Themed
   ~~~~~~

   .. include:: /arguments/fg_color.rst

   .. py:attribute:: title
      :type: str

      Text to be displayed in the window title bar, near the icon.

   Inherited
   ~~~~~~~~~

   .. py:attribute:: use
      :type: int | str | None
   .. py:attribute:: baseName
      :type: str | None
   .. py:attribute:: className
      :type: str
   .. py:attribute:: screenName
      :type: str | None
   .. py:attribute:: useTk
      :type: bool
   .. py:attribute:: sync
      :type: bool
   .. py:attribute:: bd
      :type: float | str
   .. py:attribute:: border
      :type: float | str
   .. py:attribute:: borderwidth
      :type: float | str
   .. py:attribute:: class_
      :type: str
   .. py:attribute:: cursor
      :type: str
   .. py:attribute:: height
      :type: float | str
   .. py:attribute:: width
      :type: float | str
   .. py:attribute:: padx
      :type: float | int | str
   .. py:attribute:: pady
      :type: float | int | str
   .. py:attribute:: highlightthickness
      :type: float | str
   .. py:attribute:: highlightbackground
      :type: str
   .. py:attribute:: highlightcolor
      :type: str
   .. py:attribute:: menu
      :type: tkinter.Menu
   .. py:attribute:: relief
      :type: 'raised' | 'sunken' | 'flat' | 'ridge' | 'solid' | 'groove'
   .. py:attribute:: takefocus
      :type: bool
   .. py:attribute:: container
      :type: bool
   .. py:attribute:: screen
      :type: str
   .. py:attribute:: visual
      :type: str | tuple[str, int]

      Inherited attributes from ``tkinter.Tk`` widget.

      Good luck finding a source that explains them all.
      Some explanations can be found `here <https://docs.python.org/3/library/tkinter.html#tkinter.Tk>`__,
      while others are common with :tkdoc:`Toplevel <toplevel>`.

      .. warning::
         Some can be provided just during the creation of a new instance;
         some can be modified only afterward with :py:meth:`configure()`.

   Class attributes
   ~~~~~~~~~~~~~~~~

   |class_attributes_description|

   .. include:: /arguments/deactivate_header_manipulation.rst


   Methods
   -------

   .. py:method:: mainloop() -> None:

      This method must be called, generally after all the static widgets are created,
      to start processing events and make the app work as intended.

   .. include:: /methods/windows.rst
