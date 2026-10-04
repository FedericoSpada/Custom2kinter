Appearance Mode
===============

The library supports Appearance Mode: you can switch at any time between a
Light and a Dark version of the App.
All visible colors reflect the current active mode, which can be changed with:

.. code:: python

   ctk.set_appearance_mode("light")

or

.. code:: python

   ctk.set_appearance_mode("dark")

You can also configure the Library to retrieve the mode from the operating system:

.. code:: python

   ctk.set_appearance_mode("system")

In this case, the mode is checked continuously, and if the user changes the mode
on their system, the App will automatically change the Appearance Mode.


How to specify a Color
----------------------

All colors of the widgets can be customized, but if you plan to allow the user to
change the Appearance Mode, it is important that you provide the colors properly.

Each ``_color`` argument can be either a single color name (``"red"``),
a single hex color string (``"#FF0000"``) or a tuple containing 2 of such strings
(``("red", "#0000FF")``).
In this last case, the displayed color will be selected by the widget according to
the current Appearance Mode (first element is for Light and the second is for Dark).
If you use a single color, then it will be used for both Light and Dark appearance modes.

.. code:: python

   button = ctk.CTkButton(app, fg_color="red")                # single color name
   button = ctk.CTkButton(app, fg_color="#FF0000")            # single hex string
   button = ctk.CTkButton(app, fg_color=("red", "#821D1A"))   # tuple color

Some arguments can also accept the special string ``"transparent"``;
the widget will use its parent's foreground color.

.. code:: python

   button = ctk.CTkButton(app, fg_color="transparent")  # special color

.. warning::
   This creates the effect of transparency by blending with the surrounding color,
   but pay attention that it won't actually be transparent; if the widget spans different
   backgrounds, the illusion of transparency will break.

.. note::
   ``bg_color`` is only the color of the widget's corners if it has rounded corners.
   The main color of a widget is called ``fg_color``.

   .. image:: images/bg_color.png
      :alt: CTkButton color attributes explained
