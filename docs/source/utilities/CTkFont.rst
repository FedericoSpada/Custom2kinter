CTkFont
=======

``CTkFont`` is a reusable font object for controlling the typography of CustomTkinter widgets.

Use it when several widgets should share the same family, size, or style,
or when the font must be updated after the widgets have been created.

For a font that never needs later configuration,
a regular Tkinter font tuple may be sufficient.


Example Code
------------

There are 4 ways in CustomTkinter to set a font:

.. tab-set::

   .. tab-item:: CTkFont instance

      .. code:: python

         myfont = ctk.CTkFont(family="family name", size=size_in_px)

         label1 = ctk.CTkLabel(app, font=myfont)
         label2 = ctk.CTkLabel(app, font=myfont)


   .. tab-item:: Dict of arguments

      .. code:: python

         label = ctk.CTkLabel(app, font={"family": "family name", "size": size_in_px})


   .. tab-item:: Tuple Tkinter-style

      .. code:: python

         label = ctk.CTkLabel(app, font=("family name", size_in_px, "bold italic underline overstrike"))


   .. tab-item:: Custom Key

      .. code:: python

         ctk.ThemeManager.add_key("TitleFont", size=25, weight="bold", underline=True)
         ctk.ThemeManager.add_key("Deleted", overstrike=True)
         ...
         label1 = ctk.CTkLabel(app, font="TitleFont", text="My Title")
         label2 = ctk.CTkLabel(app, font="Deleted", text="Overstruck text")
         label3 = ctk.CTkLabel(app, font="TitleFont", text="My second Title")
         label4 = ctk.CTkLabel(app, font=ctk.CTkFont("Deleted", size=50), text="Big Overstruck text")


In all cases, they will be converted to a ``CTkFont`` object that you can retrieve, reuse and update:

.. code:: python

   myfont = label.cget("font")

   newlabel = ctk.CTkLabel(app, font=myfont)

   myfont.configure(...)


If you don't provide a font, the widget will create a ``CTkFont`` with
the theme's default arguments.
If you want to update the font settings for ALL **future** widgets,
you can manipulate the ``"CTkFont"`` key in the theme:

.. code:: python

   ctk.ThemeManager.update_key("CTkFont", family="Comic Sans", size=17)
   ...
   label = ctk.CTkLabel(app)  # will use Comic Sans


.. py:class:: CTkFont
   :hidden:

   .. _font_arguments:

   Arguments
   ---------

   Positional
   ~~~~~~~~~~

   .. include:: /arguments/theme_key.rst

   Themed
   ~~~~~~

   .. py:attribute:: family
      :type: str

      Name of the Font.


   .. py:attribute:: size
      :type: int

      Height of the text in |unscaled pixels|.


   .. py:attribute:: weight
      :type: 'normal' | 'bold'

      Allows making the text **bold**.


   .. py:attribute:: slant
      :type: 'italic' | 'roman'

      Allows making the text *italic*.


   .. py:attribute:: underline
      :type: bool

      If set to ``True``, the text will be |underlined|.


   .. py:attribute:: overstrike
      :type: bool

      If set to ``True``, the text will be |overstruck|.


   Methods
   -------

   .. py:method:: configure(**kwargs) -> None:

      Allows changing the value of 1 or more arguments.

      All widgets that use the same ``CTkFont`` object will update their text automatically.

      :param any kwargs:
         Name-Value pairs where the name is a |valid argument| and the value is an acceptable value for that argument.

      :raises ValueError:
         If an unsupported argument has been provided.



   .. py:method:: cget(attribute_name) -> Any:

      Allows retrieving the current value of a font's argument by specifying its name as a string.

      :param str attribute_name:
         The name of a |valid argument|.

      :returns:
         The value of the requested argument.

      :raises ValueError:
         If an unknown argument name has been provided.



   .. py:method:: add_configure_callback(callback) -> None:

      Registers the provided function to be invoked
      when the :py:meth:`configure()` method is used.

      Widgets that receive this object as Font already use
      this method to register a callback that updates their
      text when the font is updated.

      :type callback: () -> None
      :param callback:
         Function to be added to the list of callbacks.



   .. py:method:: remove_configure_callback(callback) -> None:

      Unregisters the provided function so it will no longer be invoked
      when the :py:meth:`configure()` method is used.

      If ``callback`` was never registered using :py:meth:`add_configure_callback()`,
      nothing happens.

      :type callback: () -> None
      :param callback:
         Function to be removed from the list of callbacks.



   .. py:method:: create_scaled_tuple(font_scaling) -> tuple[str, int, str]:

      Returns the tuple representation of Font in the form ``(family, size, style)``,
      the format that Tkinter expects to receive as the ``font`` attribute.

      :param float font_scaling:
         Scaling factor to be applied to the size.

      :returns:
         The tuple representation of the Font, Tkinter-style.



   .. py:method:: copy() -> CTkFont:

      Returns a new instance of ``CTkFont`` with all arguments set to the same values as the object on which this method is invoked.

      :returns:
         A deep copy of the object.

   Inherited
   ~~~~~~~~~

   .. py:method:: actual([option]) -> str:
   .. py:method:: measure(text) -> int:
   .. py:method:: metrics([option]) -> Any:

      Inherited methods from ``tkinter.Font`` class.

      Check out the :tkdoc:`Tkinter documentation <fonts>` for their explanation.



.. |underlined| raw:: html

   <u>underlined</u>

.. |overstruck| raw:: html

   <del>overstruck</del>



.. |valid argument| replace:: `valid argument <Arguments_>`__
