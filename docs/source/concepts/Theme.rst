Theme
=====

All widgets have default values for all their arguments.
Most of them (the ones related to graphical rendering) are stored in a JSON file
that is loaded before instantiating any App.

.. code:: python

   ctk.set_default_color_theme("blue")

The library is provided with a set of themes with various colors that you can explore
thanks to the :ref:`Showroom app <showroom_app>`.

All provided themes use tuple colors for a Light and Dark :doc:`/concepts/AppearanceMode`.


Key references
--------------

It's possible to specify a value as a reference to another key value using the syntax::

   "@<key>.<subkey>.<subsubkey>.<...>"

As soon as a JSON file is loaded, the Library converts all strings that start with
``@`` to the current value that the referenced key has.
This allows you to create single keys that dictate the value for many widgets:

.. code:: json

   {
     "CommonValues": {
       "height": 30,
       "corner_radius": 10
     },

     "CTkButton": {
       "width": 140,
       "height": "@CommonValues.height",
       "corner_radius": "@CommonValues.corner_radius"
     },
     "CTkEntry": {
       "width": 200,
       "height": "@CommonValues.height",
       "corner_radius": "@CommonValues.corner_radius"
     }
   }

``CTkButton`` and ``CTkEntry`` will have ``height=30`` and ``corner_radius=10``;
so, if you update the values contained in ``CommonValues``, the same change will
be applied to both widgets.

.. hint::
   This key reference mechanism also works when you provide an argument directly:

   .. code:: python

      button = ctk.CTkButton(app, corner_radius="@CTkEntry.corner_radius")

   This is a classic example of a side effect (a.k.a. bug) that turned out to be useful,
   so it became a feature.

.. warning::
   Any reference will be replaced immediately with the value the referenced object
   has at the time of key/widget creation (subsequent changes to the referenced value
   won't affect this one).


Custom Themes
-------------

Full
~~~~

A theme is described by a JSON file like this: `common.json`_.

Built-in themes extensively use the `Key references`_ feature, so the above file is
full of ``"@Colors"`` references.
Each theme implements only the ``Colors`` key. Here is an example: `blue.json`_.

You can also create your own theme: if you just want to change the overall color scheme,
copy `blue.json`_ and change the values.
If instead you want to change the sizes or the colors for specific widgets, you have to
start from `common.json`_.

Then, you can load the new theme by passing its path to the
:py:func:`set_default_color_theme()` function:

.. code:: python

   ctk.set_default_color_theme("path/to/your/custom_theme.json")


Partial
~~~~~~~

You don't actually need to create a *complete* JSON file with the settings for ALL widgets.
You can limit yourself to providing the values you actually want to change:

.. code:: json

   {
     "CTkButton": {
       "border_width": 5
     },
     "CTkLabel": {
       "fg_color": ["#FEDE81", "#C057AD"]
     },
     "CTkEntry": {
       "justify": "center"
     }
   }

Then, after selecting a starting default theme, you can update its values using the
:py:func:`add_color_theme()` function:

.. code:: python

   ctk.set_default_color_theme("blue")
   ctk.add_color_theme("path/to/your/partial_theme.json")

You can even invoke it multiple times if you prefer/need to store the data in separate JSON files:
the most recent invocation will replace the values if their keys are contained in multiple files.

.. hint::
   Any change to an existing key can be done also programmatically using
   :py:func:`ThemeManager.update_key()`:

   .. code:: python

      ctk.ThemeManager.update_key("CTkButton",
                                  fg_color="red",
                                  compound="right",
                                  border_width=3)


.. _custom_keys:

Custom Keys
~~~~~~~~~~~

In a JSON file, you can also include any key that is not already defined in `common.json`_.
All widgets have a positional argument called ``theme_key`` that can accept the name of a
defined key, which will be used to retrieve the values to be used for the arguments.
In this case as well, you don't need to specify all arguments: you can just provide the ones
you want to change:

.. code:: json

   {
     "MyButton": {
       "corner_radius": 1000,
       "border_width": 7,
       "border_color": "white"
     }
   }

.. code:: python

   button = ctk.CTkButton(app, theme_key="MyButton")

Even if you provide a ``theme_key``, you can always override the settings by providing the values
to be used as parameters, and the same key can be used multiple times, even for any widget type:

.. code:: python

   button1 = ctk.CTkButton(app, theme_key="MyButton", border_color="black", anchor="w")
   button2 = ctk.CTkButton(app, theme_key="MyButton", border_color="red", anchor="e")
   label = ctk.CTkLabel(app, theme_key="MyButton")


.. tip::
   If you create custom keys with the idea of using them just once for a specific widget,
   you can move all graphical settings to a JSON file, leaving the implementation quite clean,
   with just the functional part of the App.

   .. code:: json

      {
        "PasswordEntry": {
          "placeholder_text": "Password",
          "show": "*",
          "justify": "center",
          "compound": "none",
          "corner_radius": 1000
        },
        "LoginButton": {
          "text": "Login",
          "corner_radius": 1000,
          "width": 300,
          "height": 30
        }
      }

   .. code:: python

         password_entry = ctk.CTkEntry(app, theme_key="PasswordEntry")
         login_button = ctk.CTkButton(app, theme_key="LoginButton", command=ask_login)


You can also add a custom key containing miscellaneous values that you can then retrieve
directly using :py:func:`ThemeManager.get_info()` and use as you prefer:

.. code:: json

   {
     "VariousData": {
       "highlight_color": "yellow",
       "number_of_buttons": 3,
       "prefix": "0x"
     }
   }

.. code:: python

   values = ctk.ThemeManager.get_info("VariousData")

   print(f"{values['highlight_color']=}")
   print(f"{values['number_of_buttons']=}")
   print(f"{values['prefix']=}")


.. hint::
   The creation of a new custom key can be done also programmatically using :py:func:`ThemeManager.add_key()`:

   .. code:: python

      ctk.ThemeManager.add_key("MyButton",
                               corner_radius=1000,
                               border_width=7,
                               border_color="white")


OS dependency
-------------

To have different settings based on the operating system, you can define a key as follows:

.. code:: json

   "Key": {
     "macOS": {

     },
     "Windows": {

     },
     "Linux": {

     }
   }



.. _common.json: https://github.com/FedericoSpada/Custom2kinter/blob/master/customtkinter/assets/themes/_common.json
.. _blue.json: https://github.com/FedericoSpada/Custom2kinter/blob/master/customtkinter/assets/themes/blue.json
